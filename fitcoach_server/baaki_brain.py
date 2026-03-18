"""
╔══════════════════════════════════════════════════════════════╗
║              BAAKI AI — عقل باكي الرياضي                    ║
║         نموذج NLP مبني من الصفر بدون أي API خارجي          ║
║                                                              ║
║  المكونات:                                                   ║
║  1. Intent Classifier  — يفهم نية المستخدم                  ║
║  2. Entity Extractor   — يستخرج الأرقام والكلمات المهمة     ║
║  3. Context Manager    — يتذكر المحادثة                     ║
║  4. Response Engine    — يولّد الرد المناسب                  ║
║  5. Personalization    — يخصّص الرد حسب بيانات المستخدم     ║
╚══════════════════════════════════════════════════════════════╝
"""

import re
import math
import random
import unicodedata
from typing import Optional


# ══════════════════════════════════════════════════════════════
# 1. NORMALIZER — تنظيف النص العربي
# ══════════════════════════════════════════════════════════════
class ArabicNormalizer:
    """يوحّد الكتابة العربية: يزيل التشكيل ويوحّد الأحرف"""

    REPLACEMENTS = {
        "أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي",
        "ة": "ه", "ؤ": "و", "ئ": "ي",
    }

    @classmethod
    def normalize(cls, text: str) -> str:
        # إزالة التشكيل
        text = "".join(
            c for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )
        # توحيد الأحرف
        for src, dst in cls.REPLACEMENTS.items():
            text = text.replace(src, dst)
        # أحرف صغيرة (للإنجليزية)
        text = text.lower().strip()
        return text


# ══════════════════════════════════════════════════════════════
# 2. INTENT CLASSIFIER — تصنيف نية المستخدم
# ══════════════════════════════════════════════════════════════
class IntentClassifier:
    """
    يصنّف نية المستخدم إلى فئات:
    كل فئة لها قائمة كلمات مفتاحية وأوزان
    """

    INTENTS = {
        # ── تمارين ──────────────────────────────────────────
        "exercise_chest": {
            "keywords": ["صدر", "بنش", "ضغط الصدر", "chest", "بوش اب", "ضغط", "بنش برس"],
            "weight": 1.0
        },
        "exercise_back": {
            "keywords": ["ظهر", "ديدليفت", "عقله", "سحب", "تجديف", "back", "لات", "رو"],
            "weight": 1.0
        },
        "exercise_legs": {
            "keywords": ["رجل", "ارجل", "سكوات", "قرفصاء", "فخذ", "ركبه", "leg", "squat", "لانج"],
            "weight": 1.0
        },
        "exercise_shoulders": {
            "keywords": ["كتف", "دلتا", "رفع جانبي", "ضغط كتف", "shoulder", "اكتاف"],
            "weight": 1.0
        },
        "exercise_arms": {
            "keywords": ["عضله", "بايسبس", "تراي", "كيرل", "ذراع", "arm", "bicep", "tricep"],
            "weight": 1.0
        },
        "exercise_core": {
            "keywords": ["بطن", "كور", "بلانك", "كرنش", "core", "abs", "plank"],
            "weight": 1.0
        },
        "exercise_cardio": {
            "keywords": ["كارديو", "جري", "مشي", "دراجه", "قلب", "تحمل", "cardio", "run", "حرق"],
            "weight": 1.0
        },
        "exercise_general": {
            "keywords": ["تمرين", "تدريب", "برنامج", "روتين", "جدول تمارين", "انواع التمارين"],
            "weight": 0.8
        },

        # ── تغذية ────────────────────────────────────────────
        "nutrition_protein": {
            "keywords": ["بروتين", "protein", "دجاج", "بيض", "لحم", "تونه", "مكمل", "واي"],
            "weight": 1.0
        },
        "nutrition_calories": {
            "keywords": ["سعره", "سعرات", "كالوري", "calories", "اكل", "وجبه", "طعام", "حصه"],
            "weight": 1.0
        },
        "nutrition_carbs": {
            "keywords": ["كارب", "كربوهيدرات", "رز", "خبز", "معكرونه", "نشا", "carb"],
            "weight": 1.0
        },
        "nutrition_fats": {
            "keywords": ["دهون", "زيت", "اوميغا", "fat", "افوكادو", "مكسرات"],
            "weight": 1.0
        },
        "nutrition_water": {
            "keywords": ["ماي", "ماء", "مياه", "water", "شرب", "ترطيب", "كوب"],
            "weight": 1.0
        },
        "nutrition_meal_plan": {
            "keywords": ["وجبات", "خطه غذائيه", "نظام غذائي", "اكل صحي", "دايت", "diet"],
            "weight": 1.0
        },
        "nutrition_supplements": {
            "keywords": ["مكملات", "كرياتين", "creatine", "واي بروتين", "whey", "بي سي اي"],
            "weight": 1.0
        },
        "nutrition_ramadan": {
            "keywords": ["رمضان", "صيام", "سحور", "افطار", "صايم", "فطور رمضان"],
            "weight": 1.2
        },

        # ── خسارة وزن / بناء عضلات ──────────────────────────
        "goal_lose_weight": {
            "keywords": ["خسارة وزن", "تنزيل وزن", "نحافه", "تخسيس", "احرق دهون", "دهون"],
            "weight": 1.0
        },
        "goal_gain_muscle": {
            "keywords": ["بناء عضلات", "ضخامه", "زياده وزن", "كتله", "كبر عضلات"],
            "weight": 1.0
        },

        # ── الجسم والصحة ──────────────────────────────────────
        "bmi_calculator": {
            "keywords": ["bmi", "مؤشر كتله", "وزن مثالي", "وزني كويس", "هل وزني"],
            "weight": 1.0
        },
        "body_pain": {
            "keywords": ["الم", "وجع", "ايذاء", "اصابه", "مفصل", "ظهر يوجع", "ركبه تعبت"],
            "weight": 1.1
        },
        "sleep_recovery": {
            "keywords": ["نوم", "راحه", "تعافي", "نعسان", "تعبان", "ارهاق", "sleep"],
            "weight": 1.0
        },

        # ── تحفيز ────────────────────────────────────────────
        "motivation": {
            "keywords": ["محفزني", "تعبت", "ما قادر", "كسلان", "مو مستوي", "ساعدني"],
            "weight": 1.0
        },

        # ── تحيات / عام ──────────────────────────────────────
        "greeting": {
            "keywords": ["مرحبا", "هلا", "السلام", "اهلا", "كيفك", "صباح", "مساء", "يا باكي"],
            "weight": 0.9
        },
        "thanks": {
            "keywords": ["شكرا", "مشكور", "برافو", "ممتاز", "حلو", "thanks"],
            "weight": 0.7
        },
        "off_topic": {
            "keywords": ["سياسه", "دين", "اخبار", "فلوس", "حب", "علاقه"],
            "weight": 0.5
        },
    }

    @classmethod
    def classify(cls, text: str) -> tuple[str, float]:
        """يُرجع (اسم_النية, درجة_الثقة)"""
        norm = ArabicNormalizer.normalize(text)
        scores: dict[str, float] = {}

        for intent, data in cls.INTENTS.items():
            score = 0.0
            for kw in data["keywords"]:
                kw_norm = ArabicNormalizer.normalize(kw)
                if kw_norm in norm:
                    # كلمة أطول = وزن أكبر
                    score += len(kw_norm.split()) * data["weight"]
            if score > 0:
                scores[intent] = score

        if not scores:
            return "unknown", 0.0

        best = max(scores, key=scores.get)
        # تطبيع الدرجة بين 0 و 1
        max_possible = max(len(kw.split()) for kw in cls.INTENTS[best]["keywords"]) * 3
        confidence = min(scores[best] / max_possible, 1.0)
        return best, confidence


# ══════════════════════════════════════════════════════════════
# 3. ENTITY EXTRACTOR — استخراج الكيانات
# ══════════════════════════════════════════════════════════════
class EntityExtractor:
    """يستخرج الأرقام والوحدات والمعلومات المهمة من النص"""

    @staticmethod
    def extract_numbers(text: str) -> list[float]:
        """يستخرج كل الأرقام من النص"""
        pattern = r"\d+(?:\.\d+)?"
        return [float(n) for n in re.findall(pattern, text)]

    @staticmethod
    def extract_weight(text: str) -> Optional[float]:
        patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:كغ|كيلو|kg|كيلوغرام)",
            r"وزني\s+(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*كيلو",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return float(m.group(1))
        return None

    @staticmethod
    def extract_height(text: str) -> Optional[float]:
        patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:سم|cm|متر|m)",
            r"طولي\s+(\d+(?:\.\d+)?)",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                val = float(m.group(1))
                # إذا كان أقل من 3 فهو بالمتر
                return val * 100 if val < 3 else val
        return None

    @staticmethod
    def extract_age(text: str) -> Optional[int]:
        patterns = [
            r"(\d+)\s*(?:سنه|سنة|عام|year)",
            r"عمري\s+(\d+)",
            r"عندي\s+(\d+)\s*سن",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                age = int(m.group(1))
                if 10 <= age <= 90:
                    return age
        return None


# ══════════════════════════════════════════════════════════════
# 4. FITNESS CALCULATOR — الحسابات العلمية
# ══════════════════════════════════════════════════════════════
class FitnessCalculator:

    @staticmethod
    def calculate_bmi(weight_kg: float, height_cm: float) -> dict:
        height_m = height_cm / 100
        bmi = weight_kg / (height_m ** 2)
        bmi = round(bmi, 1)

        if bmi < 18.5:
            category, advice = "نقص وزن", "تحتاج زيادة وزن صحية بالبروتين والكارب"
        elif bmi < 25:
            category, advice = "وزن مثالي ✅", "ممتاز! حافظ على هذا الوزن"
        elif bmi < 30:
            category, advice = "زيادة وزن", "تحتاج كارديو + تقليل السعرات"
        else:
            category, advice = "سمنة", "ابدأ ببرنامج شامل للتخسيس مع متابعة طبية"

        return {"bmi": bmi, "category": category, "advice": advice}

    @staticmethod
    def calculate_calories(
        weight: float, height: float, age: int,
        gender: str, activity: str, goal: str
    ) -> dict:
        # معادلة Mifflin-St Jeor
        if gender == "male":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        activity_map = {
            "sedentary": 1.2,
            "light":     1.375,
            "moderate":  1.55,
            "active":    1.725,
            "athlete":   1.9,
        }
        tdee = bmr * activity_map.get(activity, 1.375)

        goal_map = {
            "lose":     (tdee - 500, "عجز 500 سعرة"),
            "gain":     (tdee + 300, "فائض 300 سعرة"),
            "maintain": (tdee,       "نفس الإنفاق"),
        }
        target, note = goal_map.get(goal, (tdee, ""))
        target = round(target)

        return {
            "bmr":      round(bmr),
            "tdee":     round(tdee),
            "target":   target,
            "protein":  round(weight * 2.0),
            "carbs":    round(target * 0.45 / 4),
            "fats":     round(target * 0.25 / 9),
            "note":     note,
        }

    @staticmethod
    def calculate_water(weight_kg: float) -> float:
        """0.035 لتر لكل كيلو"""
        return round(weight_kg * 0.035, 1)

    @staticmethod
    def ideal_weight(height_cm: float, gender: str) -> tuple[float, float]:
        """نطاق الوزن المثالي حسب BMI 18.5-24.9"""
        h = height_cm / 100
        low  = round(18.5 * h * h, 1)
        high = round(24.9 * h * h, 1)
        return low, high


# ══════════════════════════════════════════════════════════════
# 5. KNOWLEDGE BASE — قاعدة المعرفة الرياضية
# ══════════════════════════════════════════════════════════════
class FitnessKnowledge:
    """
    قاعدة بيانات ضخمة من المعلومات الرياضية والتغذوية
    كل إجابة مبنية على معلومات علمية حقيقية
    """

    EXERCISES = {
        "chest": {
            "title": "💪 تمارين الصدر",
            "beginner": [
                "بوش أب (الضغط) — 3×15",
                "بوش أب متسع — 3×12",
                "بوش أب على الركبتين (للمبتدئين) — 3×15",
            ],
            "intermediate": [
                "بنش برس بالبار — 4×10",
                "ضغط مائل بالدامبل — 3×12",
                "فلايز بالدامبل — 3×15",
            ],
            "advanced": [
                "بنش برس ثقيل — 5×5",
                "كيبل كروس أوفر — 4×12",
                "ديبس بالوزن — 4×10",
            ],
            "posture_tips": [
                "أبقِ قدميك على الأرض دائماً",
                "أنزل البار للصدر ببطء (2 ثانية)",
                "لا تقوّس ظهرك بشكل مبالغ",
                "تنفس للأسفل عند النزول، وازفر عند الدفع",
            ],
            "muscles": "الصدر الكبير، الأمامي من الكتف، المثلثة",
        },
        "back": {
            "title": "🏋️ تمارين الظهر",
            "beginner": [
                "سحب عمودي بالكيبل (لات بول داون) — 3×12",
                "تجديف بالدامبل — 3×12",
                "بوش أب على شكل T — 3×10",
            ],
            "intermediate": [
                "تجديف بالبار — 4×10",
                "عقلة — 3×8",
                "ديدليفت رومياني — 3×10",
            ],
            "advanced": [
                "ديدليفت — 4×6",
                "عقلة بوزن — 4×8",
                "سحب تي-بار — 4×10",
            ],
            "posture_tips": [
                "ظهرك مستقيم دائماً — هذا الأهم!",
                "لا تتقوس عند رفع الأثقال",
                "شد لوحي كتفيك عند السحب",
                "ابدأ الحركة من الكوعين لا اليدين",
            ],
            "muscles": "العريض الأكبر، المعيني، الشبه منحرف",
        },
        "legs": {
            "title": "🦵 تمارين الأرجل",
            "beginner": [
                "سكوات بوزن الجسم — 3×15",
                "لانج أمامي — 3×12",
                "رفع الكعب (ساق) — 3×20",
            ],
            "intermediate": [
                "سكوات بالبار — 4×10",
                "ضغط أرجل (ليج برس) — 4×12",
                "امتداد أرجل — 3×15",
            ],
            "advanced": [
                "سكوات ثقيل — 5×5",
                "هاك سكوات — 4×10",
                "ديدليفت رومياني — 4×8",
            ],
            "posture_tips": [
                "الركبتان فوق أصابع القدم دائماً",
                "ظهرك مستقيم عند النزول",
                "انزل حتى 90 درجة على الأقل",
                "ادفع من الكعب عند الصعود",
            ],
            "muscles": "الفخذ الأمامي، الخلفي، الأرداف، الساق",
        },
        "shoulders": {
            "title": "🔝 تمارين الكتف",
            "beginner": [
                "رفع جانبي بدامبل خفيف — 3×15",
                "رفع أمامي — 3×12",
                "ضغط كتف بدامبل — 3×12",
            ],
            "intermediate": [
                "ضغط عسكري بالبار — 4×10",
                "رفع جانبي بالكيبل — 3×15",
                "فايس بول — 3×12",
            ],
            "advanced": [
                "ضغط عسكري ثقيل — 5×5",
                "شراغ بالبار — 4×12",
                "أرنولد برس — 4×10",
            ],
            "posture_tips": [
                "لا ترفع الكتف أكثر من مستوى الأذن",
                "ظهرك مستقيم عند الضغط",
                "تحكم في الحركة ببطء",
            ],
            "muscles": "الدلتا الأمامي، الجانبي، الخلفي",
        },
        "arms": {
            "title": "💪 تمارين الذراعين",
            "beginner": [
                "كيرل بالدامبل — 3×12",
                "ديبس على الكرسي — 3×12",
                "كيرل هامر — 3×12",
            ],
            "intermediate": [
                "كيرل بالبار EZ — 4×10",
                "بوش داون — 4×12",
                "كيرل تركيز — 3×12",
            ],
            "advanced": [
                "كيرل بتشر — 4×10",
                "فرنش برس — 4×10",
                "كيرل 21s — 3 sets",
            ],
            "posture_tips": [
                "لا تحرّك الكوع أثناء الكيرل",
                "تحكم في مرحلة النزول",
                "لا تستخدم الزخم",
            ],
            "muscles": "البايسبس، التراي سبس، العضلة العضدية",
        },
        "core": {
            "title": "🎯 تمارين البطن والكور",
            "beginner": [
                "بلانك — 3×30 ثانية",
                "كرنش — 3×20",
                "رفع الأرجل — 3×15",
            ],
            "intermediate": [
                "بلانك جانبي — 3×30 ثانية",
                "ماونتن كلايمر — 3×30 ثانية",
                "دراجة — 3×20",
            ],
            "advanced": [
                "دراغون فلاغ — 3×8",
                "L-Sit — 3×15 ثانية",
                "بلانك بالحركة — 3×45 ثانية",
            ],
            "posture_tips": [
                "شد البطن دائماً",
                "لا تحبس النفس",
                "الظهر مستوٍ في البلانك",
            ],
            "muscles": "المستقيم البطني، المائل، العمق البطني",
        },
        "cardio": {
            "title": "🏃 تمارين الكارديو",
            "types": {
                "HIIT": "تمرين متقطع عالي الكثافة — 20 دقيقة يساوي 45 دقيقة جري عادي",
                "LISS": "كارديو هادئ مستمر — مشي سريع 45 دقيقة، ممتاز لحرق الدهون",
                "Circuit": "دوائر تمرينية — تجمع القوة والكارديو معاً",
            },
            "fat_burn_zone": "60-70% من أقصى معدل قلب",
            "max_heart_rate": "220 - عمرك",
        },
    }

    NUTRITION = {
        "protein_sources": {
            "animal": [
                ("صدر دجاج 100g", 31, 165),
                ("بيض كامل (واحدة)", 6, 70),
                ("تونة 100g", 30, 130),
                ("لحم بقر خالي الدهن 100g", 26, 180),
                ("سمك سلمون 100g", 25, 208),
                ("جبن قريش 100g", 11, 72),
            ],
            "plant": [
                ("عدس مطبوخ كوب", 18, 230),
                ("حمص مطبوخ كوب", 15, 270),
                ("توفو 100g", 8, 76),
                ("مكسرات مشكلة 30g", 6, 170),
            ],
        },
        "pre_workout": [
            "موزة + قهوة سوداء (قبل 30 دقيقة)",
            "أرز أبيض + دجاج (قبل ساعة)",
            "شوفان + عسل (قبل 45 دقيقة)",
            "تمر 3-4 حبات (قبل 20 دقيقة)",
        ],
        "post_workout": [
            "واي بروتين + موز",
            "صدر دجاج + أرز بني",
            "بيض مسلوق + خبز أسمر",
            "تونة + بطاطا حلوة",
        ],
        "ramadan_guide": {
            "suhoor": [
                "شوفان بالحليب والموز",
                "بيضتان مسلوقتان",
                "خبز أسمر + جبنة",
                "تمر 3 حبات",
                "ماء 2 كوب على الأقل",
            ],
            "iftar": [
                "تمر 3 حبات + ماء (أول شيء)",
                "شوربة عدس أو خضار",
                "سلطة خضراء",
                "وجبة رئيسية متوازنة",
            ],
            "timing": "التمرين بعد الإفطار بساعتين أو قبل الإفطار بـ 30 دقيقة",
            "water": "اشرب 8-10 أكواب بين الإفطار والسحور",
        },
    }

    PAIN_GUIDE = {
        "lower_back": {
            "causes": ["ضعف عضلات الكور", "الجلوس الطويل", "رفع أثقال بوضعية خاطئة"],
            "exercises": ["القطة والبقرة (Cat-Cow)", "الطائر والكلب (Bird-Dog)", "بلانك"],
            "avoid": ["ديدليفت", "سكوات بأوزان ثقيلة", "تجديف بالبار"],
            "tips": ["نم على جانبك مع وسادة بين الركبتين", "مطط كل ساعة"],
        },
        "knee": {
            "causes": ["ضعف عضلة الفخذ الأمامي", "وزن زائد", "خطأ في الوضعية"],
            "exercises": ["تمديد الأرجل على الكرسي", "سكوات نصفي", "سباحة"],
            "avoid": ["ركض على الإسفلت", "سكوات عميق", "أي ألم = توقف فوراً"],
            "tips": ["استخدم رباط الركبة", "تجنب الأسطح الصلبة"],
        },
        "shoulder": {
            "causes": ["تمزق بالكفة المدورة", "التهاب الوتر", "ضعف العضلة المثبتة"],
            "exercises": ["دوائر الكتف البطيئة", "رفع جانبي خفيف جداً", "تقوية العضلة المثبتة"],
            "avoid": ["بنش برس", "عقلة", "أي تمرين فوق الرأس حتى يتحسن"],
            "tips": ["ثلج 15 دقيقة بعد التمرين", "زُر طبيب عظام"],
        },
        "neck": {
            "causes": ["النوم بوضعية خاطئة", "النظر للهاتف طويلاً", "توتر العضلات"],
            "exercises": ["تمديد جانبي للرقبة", "تمديد أمامي وخلفي", "دوران بطيء"],
            "avoid": ["أي ضغط مباشر على الرقبة", "نزول الرأس بقوة"],
            "tips": ["ارفع الشاشة لمستوى العينين", "وسادة داعمة"],
        },
    }

    MOTIVATION_QUOTES = [
        "كل تمرين صعب الآن سيصبح سهلاً بعد شهر. استمر يا بطل! 🔥",
        "الفرق بين من ينجح ومن لا ينجح هو من يكمل حين يتعب. يلا! 💪",
        "جسمك يستطيع أكثر مما تظن — عقلك هو من يستسلم أولاً. لا تدعه! ⚡",
        "كل شخص تحسده على جسمه مرّ بنفس اللحظة التي تمر بها الآن. استمر!",
        "النتيجة لا تأتي في يوم — لكنها تأتي. ثق بالعملية يا أسد! 🦁",
        "60 دقيقة تمرين = 4% من يومك. لا عذر! 💥",
        "الكسل مؤقت، النتيجة دائمة. قم وتحرك! 🚀",
    ]

    SLEEP_GUIDE = {
        "importance": [
            "70% من بناء العضلات يحدث أثناء النوم",
            "قلة النوم ترفع هرمون الكورتيزول ويهدم العضلات",
            "النوم الجيد يرفع هرمون التستوستيرون بشكل طبيعي",
        ],
        "tips": [
            "نم 7-9 ساعات يومياً",
            "أغلق الشاشات قبل النوم بساعة",
            "درجة حرارة الغرفة 18-20 مئوية",
            "لا كافيين بعد الساعة 4 مساءً",
            "تمرين قوي لا يكون آخر ساعتين قبل النوم",
        ],
        "stages": {
            "خفيف": "أول 90 دقيقة — الجسم يبدأ بالاسترخاء",
            "عميق": "الأهم — إفراز هرمون النمو وبناء العضلات",
            "REM":  "تقوية الذاكرة وتعلم الحركات الجديدة",
        },
    }


# ══════════════════════════════════════════════════════════════
# 6. CONTEXT MANAGER — إدارة سياق المحادثة
# ══════════════════════════════════════════════════════════════
class ConversationContext:
    """يتذكر المحادثة ويتعلم من الأسئلة السابقة"""

    def __init__(self):
        self.history: list[dict]  = []
        self.last_intent: str     = ""
        self.last_topic: str      = ""
        self.asked_about: set     = set()
        self.turn_count: int      = 0

    def add(self, role: str, text: str, intent: str = ""):
        self.history.append({
            "role":   role,
            "text":   text,
            "intent": intent,
        })
        if role == "user":
            self.turn_count += 1
            if intent:
                self.last_intent = intent
                self.asked_about.add(intent)
        # احتفظ بآخر 10 رسائل فقط
        if len(self.history) > 10:
            self.history = self.history[-10:]

    def is_followup(self) -> bool:
        """هل هذا سؤال متابعة للموضوع السابق؟"""
        if len(self.history) < 2:
            return False
        last_user = [m for m in self.history if m["role"] == "user"]
        if len(last_user) >= 2:
            prev_intent = last_user[-2].get("intent", "")
            curr_intent = last_user[-1].get("intent", "")
            return prev_intent == curr_intent
        return False

    def get_topic_group(self, intent: str) -> str:
        """يحول intent مفصّل لموضوع عام"""
        if intent.startswith("exercise_"): return "exercise"
        if intent.startswith("nutrition_"): return "nutrition"
        if intent.startswith("goal_"): return "goal"
        return intent


# ══════════════════════════════════════════════════════════════
# 7. RESPONSE ENGINE — محرك توليد الردود
# ══════════════════════════════════════════════════════════════
class ResponseEngine:
    """
    يولّد ردوداً طبيعية ومخصصة بناءً على:
    - نية المستخدم
    - بياناته الشخصية
    - سياق المحادثة
    - التنويع (لا يعطي نفس الرد مرتين)
    """

    def __init__(self):
        self.normalizer  = ArabicNormalizer()
        self.classifier  = IntentClassifier()
        self.extractor   = EntityExtractor()
        self.calculator  = FitnessCalculator()
        self.knowledge   = FitnessKnowledge()
        self.used_quotes: set = set()

    def _get_level(self, user_data: dict) -> str:
        return user_data.get("lvl", "beginner")

    def _get_name(self, user_data: dict) -> str:
        return user_data.get("name") or "يا بطل"

    def _exercises_for_level(self, muscle: str, level: str) -> list[str]:
        ex = self.knowledge.EXERCISES.get(muscle, {})
        if level in ("beast", "strong", "active"):
            return ex.get("advanced", []) or ex.get("intermediate", [])
        elif level in ("medium", "moderate"):
            return ex.get("intermediate", [])
        else:
            return ex.get("beginner", [])

    def _random_opener(self, name: str) -> str:
        openers = [
            f"يلا يا {name}! ",
            f"برافو على السؤال {name}! ",
            f"سؤال ممتاز {name}! ",
            f"هيا نجاوبك {name}! ",
            f"",  # بدون opener أحياناً
        ]
        return random.choice(openers)

    def _random_closer(self) -> str:
        closers = [
            "\n\nاسألني أي شيء ثاني! 💪",
            "\n\nيلا قوي! 🔥",
            "\n\nهل تحب أعطيك المزيد؟",
            "",
        ]
        return random.choice(closers)

    def generate(self, user_msg: str, user_data: dict, ctx: ConversationContext) -> str:
        """الدالة الرئيسية — تولّد الرد الكامل"""

        intent, confidence = self.classifier.classify(user_msg)
        ctx.add("user", user_msg, intent)

        name  = self._get_name(user_data)
        level = self._get_level(user_data)
        goal  = user_data.get("goal", "")
        pain  = user_data.get("pain", [])
        is_ram = user_data.get("ram", False)

        # ── تجربة استخراج بيانات من الرسالة نفسها ──
        extracted_weight = self.extractor.extract_weight(user_msg)
        extracted_height = self.extractor.extract_height(user_msg)
        extracted_age    = self.extractor.extract_age(user_msg)

        # إذا ذكر وزناً وطولاً في نفس الرسالة → احسب BMI تلقائياً
        if extracted_weight and extracted_height and "bmi" not in intent:
            bmi_data = self.calculator.calculate_bmi(extracted_weight, extracted_height)
            response = (
                f"حسبت لك يا {name}! 📊\n\n"
                f"**مؤشر كتلة الجسم (BMI):**\n"
                f"• وزنك: {extracted_weight}كغ | طولك: {extracted_height}سم\n"
                f"• BMI = {bmi_data['bmi']}\n"
                f"• التصنيف: {bmi_data['category']}\n"
                f"• نصيحة: {bmi_data['advice']}"
            )
            ctx.add("bot", response, "bmi_calculator")
            return response

        # ── router حسب الnية ──
        handler_map = {
            "greeting":            self._handle_greeting,
            "thanks":              self._handle_thanks,
            "off_topic":           self._handle_off_topic,
            "bmi_calculator":      self._handle_bmi,
            "motivation":          self._handle_motivation,
            "body_pain":           self._handle_pain,
            "sleep_recovery":      self._handle_sleep,
            "nutrition_water":     self._handle_water,
            "nutrition_protein":   self._handle_protein,
            "nutrition_calories":  self._handle_calories,
            "nutrition_carbs":     self._handle_carbs,
            "nutrition_fats":      self._handle_fats,
            "nutrition_meal_plan": self._handle_meal_plan,
            "nutrition_supplements": self._handle_supplements,
            "nutrition_ramadan":   self._handle_ramadan,
            "goal_lose_weight":    self._handle_lose_weight,
            "goal_gain_muscle":    self._handle_gain_muscle,
            "exercise_chest":      lambda u, d, c: self._handle_exercise(u, d, c, "chest"),
            "exercise_back":       lambda u, d, c: self._handle_exercise(u, d, c, "back"),
            "exercise_legs":       lambda u, d, c: self._handle_exercise(u, d, c, "legs"),
            "exercise_shoulders":  lambda u, d, c: self._handle_exercise(u, d, c, "shoulders"),
            "exercise_arms":       lambda u, d, c: self._handle_exercise(u, d, c, "arms"),
            "exercise_core":       lambda u, d, c: self._handle_exercise(u, d, c, "core"),
            "exercise_cardio":     self._handle_cardio,
            "exercise_general":    self._handle_general_exercise,
            "unknown":             self._handle_unknown,
        }

        handler = handler_map.get(intent, self._handle_unknown)
        response = handler(user_msg, user_data, ctx)

        # إضافة تحذيرات الألم إذا كانت مرتبطة بالتمرين
        if intent.startswith("exercise_") and pain:
            pain_warning = self._get_pain_warning(intent, pain)
            if pain_warning:
                response += f"\n\n⚠️ **تنبيه لوضعك:** {pain_warning}"

        # إضافة نصيحة رمضان إذا كان الوقت مناسباً
        if is_ram and intent.startswith("exercise_") and random.random() > 0.6:
            response += f"\n\n🌙 **رمضان:** تمرن بعد الإفطار بساعتين للحصول على أفضل أداء."

        ctx.add("bot", response, intent)
        return response

    # ── Handlers ──────────────────────────────────────────────

    def _handle_greeting(self, msg, user_data, ctx):
        name = self._get_name(user_data)
        lvl  = self._get_level(user_data)
        lvl_map = {
            "beast": "وحش الصالة 🔥",
            "strong": "مستوى قوي 💪",
            "medium": "متوسط ⚡",
            "light": "خفيف ونشط 🌟",
            "beginner": "مبتدئ 🌱",
        }
        level_text = lvl_map.get(lvl, "")
        greetings = [
            f"هلا {name}! 💪 أنا باكي، مدربك الشخصي الذكي.\nمستواك: {level_text}\nاسألني عن التمارين، التغذية، النوم، أو أي شيء رياضي! يلا! 🔥",
            f"أهلاً {name}! يسعدني أساعدك اليوم 🌟\nعندي معلومات عن التمارين، التغذية، الوزن المثالي، وأكثر.\nوش تبي تعرف؟ 💪",
            f"يا هلا {name}! جاهز أكون مدربك الشخصي 🏋️\nاسألني أي سؤال رياضي وأجاوبك بعلم وخبرة. يلا بينا! ⚡",
        ]
        return random.choice(greetings)

    def _handle_thanks(self, msg, user_data, ctx):
        name = self._get_name(user_data)
        responses = [
            f"العفو يا {name}! هذا واجبي. اسألني متى ما تبي! 💪",
            f"يسعدني دائماً يا بطل! أي سؤال ثاني؟ 🔥",
            f"برافو عليك! استمر في التدريب ونتائجك تحكي. يلا! 💪",
        ]
        return random.choice(responses)

    def _handle_off_topic(self, msg, user_data, ctx):
        name = self._get_name(user_data)
        return (
            f"هههه يا {name}، هذا موضوع خارج تخصصي! 😄\n"
            f"أنا متخصص بس في: التمارين، التغذية، الوزن المثالي، والصحة الرياضية.\n"
            f"اسألني عن هذه الأمور وأجاوبك بدقة! 💪"
        )

    def _handle_bmi(self, msg, user_data, ctx):
        name   = self._get_name(user_data)
        weight = user_data.get("wt")
        height = user_data.get("ht")

        if weight and height:
            bmi_data = self.calculator.calculate_bmi(weight, height)
            low, high = self.calculator.ideal_weight(height, user_data.get("gender", "male"))
            return (
                f"📊 **حسابات جسمك يا {name}:**\n\n"
                f"• الوزن: {weight}كغ | الطول: {height}سم\n"
                f"• BMI = **{bmi_data['bmi']}**\n"
                f"• التصنيف: {bmi_data['category']}\n"
                f"• الوزن المثالي لطولك: {low} - {high} كغ\n\n"
                f"💡 {bmi_data['advice']}"
            )
        else:
            return (
                f"يا {name}، أحتاج وزنك وطولك لأحسب BMI.\n"
                f"قول لي مثلاً: **وزني 80 كغ وطولي 175 سم** وأحسب لك فوراً! 📊"
            )

    def _handle_motivation(self, msg, user_data, ctx):
        name = self._get_name(user_data)
        available = [q for q in self.knowledge.MOTIVATION_QUOTES
                     if q not in self.used_quotes]
        if not available:
            self.used_quotes.clear()
            available = self.knowledge.MOTIVATION_QUOTES

        quote = random.choice(available)
        self.used_quotes.add(quote)

        return (
            f"يا {name}، أسمعك! 💙\n\n"
            f"**{quote}**\n\n"
            f"تذكر: كل شخص مر بهذه اللحظة. الفرق هو من قام وكمل.\n"
            f"قم الآن، حتى لو تمرين خفيف 15 دقيقة. يلا! 🔥"
        )

    def _handle_pain(self, msg, user_data, ctx):
        name = self._get_name(user_data)
        pain_zones = user_data.get("pain", [])
        msg_norm = ArabicNormalizer.normalize(msg)

        # اكتشف منطقة الألم
        pain_area = None
        if any(k in msg_norm for k in ["ظهر", "ضهر", "فقرات"]):
            pain_area = "lower_back"
        elif any(k in msg_norm for k in ["ركبه", "مفصل الركبه"]):
            pain_area = "knee"
        elif any(k in msg_norm for k in ["كتف", "اكتاف"]):
            pain_area = "shoulder"
        elif any(k in msg_norm for k in ["رقبه", "عنق"]):
            pain_area = "neck"

        # إذا عنده آلام مسجلة
        if not pain_area and pain_zones:
            zone_map = {
                "back": "lower_back", "lower-back": "lower_back",
                "knee-r": "knee", "knee-l": "knee",
                "shoulder-r": "shoulder", "shoulder-l": "shoulder",
                "neck": "neck",
            }
            for z in pain_zones:
                if z in zone_map:
                    pain_area = zone_map[z]
                    break

        if pain_area:
            guide = self.knowledge.PAIN_GUIDE.get(pain_area, {})
            area_names = {
                "lower_back": "أسفل الظهر",
                "knee": "الركبة",
                "shoulder": "الكتف",
                "neck": "الرقبة",
            }
            return (
                f"🩺 **دليل علاج ألم {area_names.get(pain_area, 'المنطقة')}:**\n\n"
                f"**الأسباب الشائعة:**\n"
                + "".join(f"• {c}\n" for c in guide.get("causes", [])) +
                f"\n**تمارين العلاج:**\n"
                + "".join(f"✅ {e}\n" for e in guide.get("exercises", [])) +
                f"\n**تجنب:**\n"
                + "".join(f"❌ {a}\n" for a in guide.get("avoid", [])) +
                f"\n**نصائح:**\n"
                + "".join(f"💡 {t}\n" for t in guide.get("tips", []))
            )

        return (
            f"يا {name}، أي منطقة تؤلمك بالضبط؟\n\n"
            f"قول لي: **ظهر / ركبة / كتف / رقبة**\n"
            f"وأعطيك برنامج علاجي مخصص! 🩺"
        )

    def _handle_sleep(self, msg, user_data, ctx):
        name = self._get_name(user_data)
        guide = self.knowledge.SLEEP_GUIDE
        return (
            f"😴 **النوم والتعافي يا {name}:**\n\n"
            f"**لماذا النوم مهم للرياضيين؟**\n"
            + "".join(f"• {i}\n" for i in guide["importance"]) +
            f"\n**نصائح النوم الجيد:**\n"
            + "".join(f"💡 {t}\n" for t in guide["tips"]) +
            f"\n**مراحل النوم:**\n"
            + "".join(f"• {s}: {d}\n" for s, d in guide["stages"].items())
        )

    def _handle_water(self, msg, user_data, ctx):
        name   = self._get_name(user_data)
        weight = user_data.get("wt")
        wgoal  = user_data.get("wgoal", 8)

        if weight:
            liters = self.calculator.calculate_water(weight)
            cups   = round(liters * 4)  # 250ml لكل كوب
            return (
                f"💧 **الماء اليومي لك يا {name}:**\n\n"
                f"• حسب وزنك ({weight}كغ): **{liters} لتر يومياً**\n"
                f"• يعني: **{cups} كوب (250ml)**\n\n"
                f"**نصائح:**\n"
                f"• اشرب كوب فور استيقاظك\n"
                f"• كوب قبل كل وجبة\n"
                f"• كوبين على الأقل قبل وبعد التمرين\n"
                f"• البول الأصفر الفاتح = ترطيب جيد ✅"
            )

        return (
            f"💧 **الماء مهم جداً يا {name}!**\n\n"
            f"القاعدة العامة: **35ml × وزنك بالكيلو**\n"
            f"مثال: وزن 70كغ = 2.45 لتر = 10 أكواب يومياً\n\n"
            f"قول لي وزنك وأحسب لك الكمية الدقيقة! 💧"
        )

    def _handle_protein(self, msg, user_data, ctx):
        name   = self._get_name(user_data)
        weight = user_data.get("wt")
        goal   = user_data.get("goal", "maintain")
        prot   = user_data.get("prot")

        protein_need = prot or (weight * 2.0 if weight else None)
        sources = self.knowledge.NUTRITION["protein_sources"]

        response = f"🥩 **البروتين يا {name}:**\n\n"

        if protein_need:
            response += f"• احتياجك اليومي: **{round(protein_need)}g**\n\n"

        response += (
            f"**أفضل مصادر البروتين:**\n"
            f"*حيواني:*\n"
            + "".join(f"• {s[0]}: {s[1]}g بروتين ({s[2]} سعرة)\n"
                      for s in sources["animal"][:4]) +
            f"\n*نباتي:*\n"
            + "".join(f"• {s[0]}: {s[1]}g بروتين\n"
                      for s in sources["plant"][:3]) +
            f"\n💡 **توصيتي:** {2.0 if goal=='gain' else 1.8}g × وزنك يومياً"
        )
        return response

    def _handle_calories(self, msg, user_data, ctx):
        name   = self._get_name(user_data)
        weight = user_data.get("wt")
        height = user_data.get("ht")
        age    = user_data.get("age")
        gender = user_data.get("gender", "male")
        act    = user_data.get("act", "moderate")
        goal   = user_data.get("goal", "maintain")
        cal    = user_data.get("cal")

        if weight and height and age:
            c = self.calculator.calculate_calories(weight, height, age, gender, act, goal)
            goal_text = {"lose": "خسارة وزن", "gain": "بناء عضلات", "maintain": "حفاظ"}.get(goal, goal)
            return (
                f"🔥 **حسابات السعرات يا {name}:**\n\n"
                f"• معدل الأيض الأساسي (BMR): {c['bmr']} سعرة\n"
                f"• إجمالي الإنفاق اليومي (TDEE): {c['tdee']} سعرة\n"
                f"• هدفك ({goal_text}): **{c['target']} سعرة/يوم**\n\n"
                f"**توزيع الماكرو:**\n"
                f"• بروتين: {c['protein']}g\n"
                f"• كارب: {c['carbs']}g\n"
                f"• دهون: {c['fats']}g\n\n"
                f"💡 {c['note']}"
            )

        if cal:
            return (
                f"🔥 **سعراتك اليومية يا {name}: {cal} سعرة**\n\n"
                f"**لتحقيق هدفك:**\n"
                f"• لا تنقص أكثر من 500 سعرة في اليوم\n"
                f"• لا تزيد أكثر من 300-500 سعرة للبناء\n"
                f"• وزّعها على 4-5 وجبات يومياً"
            )

        return (
            f"🔥 حسابات السعرات تحتاج وزنك، طولك، وعمرك يا {name}.\n"
            f"هذه البيانات موجودة في برنامجك! اذهب لـ **حسابي** وتجدها. 📊"
        )

    def _handle_carbs(self, msg, user_data, ctx):
        name = self._get_name(user_data)
        goal = user_data.get("goal", "maintain")

        carb_advice = {
            "lose":     "قلل الكارب لـ 30-40% من السعرات، وركز على الكارب المعقد",
            "gain":     "ارفع الكارب لـ 50-55% من السعرات للطاقة وبناء العضلات",
            "maintain": "45-50% من السعرات مناسبة للحفاظ على الأداء",
        }

        return (
            f"🌾 **الكربوهيدرات يا {name}:**\n\n"
            f"💡 لهدفك: {carb_advice.get(goal, carb_advice['maintain'])}\n\n"
            f"**أفضل مصادر الكارب:**\n"
            f"✅ أرز بني، شوفان، بطاطا حلوة، خبز أسمر\n"
            f"✅ فاكهة طازجة، فاصوليا، عدس\n\n"
            f"**تجنب:**\n"
            f"❌ سكريات مضافة، عصائر معبأة، مقليات\n\n"
            f"⏰ **التوقيت مهم:** الكارب قبل التمرين للطاقة، وبعده للتعافي"
        )

    def _handle_fats(self, msg, user_data, ctx):
        name = self._get_name(user_data)
        return (
            f"🥑 **الدهون الصحية يا {name}:**\n\n"
            f"**ضروري للجسم لأنها:**\n"
            f"• تنظم هرمون التستوستيرون\n"
            f"• تساعد امتصاص الفيتامينات\n"
            f"• تحمي المفاصل\n\n"
            f"**أفضل المصادر:**\n"
            f"✅ أفوكادو، زيت زيتون بكر\n"
            f"✅ مكسرات: لوز، جوز، فستق\n"
            f"✅ سمك سلمون، سردين (أوميغا 3)\n"
            f"✅ بذور الشيا والكتان\n\n"
            f"**الكمية:** 20-30% من مجموع السعرات اليومية\n"
            f"❌ تجنب: مقليات، زيت نباتي مهدرج، وجبات سريعة"
        )

    def _handle_meal_plan(self, msg, user_data, ctx):
        name   = self._get_name(user_data)
        goal   = user_data.get("goal", "maintain")
        is_ram = user_data.get("ram", False)

        if is_ram:
            return self._handle_ramadan(msg, user_data, ctx)

        cal  = user_data.get("cal", 2000)
        prot = user_data.get("prot", 150)

        plans = {
            "lose": [
                ("🌅 الفطور (7 ص)", ["شوفان نصف كوب + حليب قليل الدسم", "بيضتان مسلوقتان", "تفاحة"]),
                ("🍎 وجبة خفيفة (10 ص)", ["زبادي يوناني + مكسرات 20g"]),
                ("☀️ الغداء (1 م)", ["صدر دجاج 150g مشوي", "خضار مشوية", "سلطة كبيرة"]),
                ("🌙 العشاء (7 م)", ["سمكة مشوية أو تونة", "خضار مطبوخة"]),
            ],
            "gain": [
                ("🌅 الفطور (7 ص)", ["شوفان كوب + موز + عسل", "3 بيضات + صفار 2", "حليب كوب"]),
                ("🍎 وجبة خفيفة (10 ص)", ["مكسرات 40g", "تمر 4 حبات", "بروتين شيك"]),
                ("☀️ الغداء (1 م)", ["أرز بني كوبان", "صدر دجاج 200g", "خضار"]),
                ("💪 بعد التمرين", ["بروتين شيك", "موزتان"]),
                ("🌙 العشاء (8 م)", ["لحم خفيف 200g", "بطاطا حلوة كبيرة"]),
            ],
            "maintain": [
                ("🌅 الفطور (7 ص)", ["شوفان + فاكهة", "بيضتان", "قهوة/شاي"]),
                ("🍎 وجبة خفيفة (10 ص)", ["فاكهة + مكسرات"]),
                ("☀️ الغداء (1 م)", ["أرز بني + بروتين اختيارك + خضار"]),
                ("🌙 العشاء (7 م)", ["بروتين خفيف + سلطة"]),
            ],
        }

        plan = plans.get(goal, plans["maintain"])
        goal_text = {"lose": "خسارة وزن", "gain": "بناء عضلات", "maintain": "حفاظ"}.get(goal, goal)

        response = f"🥗 **خطة وجباتك يا {name} ({goal_text}):**\n"
        response += f"هدف يومي: {cal} سعرة | بروتين: {prot}g\n\n"

        for meal_name, items in plan:
            response += f"**{meal_name}:**\n"
            response += "".join(f"• {item}\n" for item in items)
            response += "\n"

        response += "💧 لا تنسَ 8+ أكواب ماء يومياً!"
        return response

    def _handle_supplements(self, msg, user_data, ctx):
        name = self._get_name(user_data)
        goal = user_data.get("goal", "maintain")
        return (
            f"💊 **المكملات الغذائية يا {name}:**\n\n"
            f"**الأساسية (للجميع):**\n"
            f"• بروتين واي: بعد التمرين مباشرة\n"
            f"• كرياتين: 5g يومياً (للقوة والضخامة)\n"
            f"• فيتامين D3: 2000 IU يومياً (مهم جداً)\n\n"
            f"**حسب هدفك:**\n"
            + (f"• حارق دهون طبيعي (L-Carnitine)\n• أوميغا 3\n"
               if goal == "lose" else
               f"• BCAA: أثناء التمرين\n• المولتي فيتامين\n"
               if goal == "gain" else
               f"• أوميغا 3\n• المولتي فيتامين\n") +
            f"\n⚠️ **مهم:** المكملات **إضافة** للغذاء الصحيح، ليست بديلاً عنه.\n"
            f"الغذاء الأساسي = 90% من النتيجة."
        )

    def _handle_ramadan(self, msg, user_data, ctx):
        name  = self._get_name(user_data)
        guide = self.knowledge.NUTRITION["ramadan_guide"]
        level = self._get_level(user_data)

        intensity = "متوسطة الشدة" if level in ("beast", "strong") else "خفيفة"

        return (
            f"🌙 **برنامج رمضان المبارك يا {name}:**\n\n"
            f"**السحور (قبل الفجر):**\n"
            + "".join(f"• {item}\n" for item in guide["suhoor"]) +
            f"\n**الإفطار:**\n"
            + "".join(f"• {item}\n" for item in guide["iftar"]) +
            f"\n⏰ **وقت التمرين:** {guide['timing']}\n"
            f"💧 **الماء:** {guide['water']}\n\n"
            f"💪 **التمرين في رمضان:**\n"
            f"• شدة {intensity}\n"
            f"• مدة 30-45 دقيقة\n"
            f"• ركز على الحفاظ لا البناء\n"
            f"• تمارين القوة أفضل من الكارديو الثقيل"
        )

    def _handle_lose_weight(self, msg, user_data, ctx):
        name   = self._get_name(user_data)
        weight = user_data.get("wt")
        cal    = user_data.get("cal")
        return (
            f"🔥 **خطة خسارة الوزن يا {name}:**\n\n"
            f"**المبدأ الأساسي:**\n"
            f"• عجز 500 سعرة/يوم = 0.5 كغ/أسبوع\n"
            f"• عجز 1000 سعرة = 1 كغ/أسبوع (الحد الأقصى الصحي)\n\n"
            f"**استراتيجيتك:**\n"
            f"• هدفك: {(cal-500) if cal else 'TDEE - 500'} سعرة/يوم\n"
            f"• بروتين عالٍ: {round(weight*2) if weight else '2g'} × وزنك (يحمي العضلات)\n"
            f"• كارديو: 3-4 مرات أسبوعياً\n"
            f"• تمارين قوة: للحفاظ على العضلات\n\n"
            f"**نصائح ذهبية:**\n"
            f"• لا تجوع! وجبات صغيرة متعددة\n"
            f"• النوم الجيد يساعد حرق الدهون\n"
            f"• الصبر! الخسارة الصحية بطيئة لكن ثابتة"
        )

    def _handle_gain_muscle(self, msg, user_data, ctx):
        name   = self._get_name(user_data)
        weight = user_data.get("wt")
        cal    = user_data.get("cal")
        return (
            f"💪 **خطة بناء العضلات يا {name}:**\n\n"
            f"**المبدأ الأساسي:**\n"
            f"• فائض 200-300 سعرة فوق TDEE\n"
            f"• بروتين: {round(weight*2.2) if weight else '2.2g'} × وزنك يومياً\n\n"
            f"**البرنامج الأمثل:**\n"
            f"• تمارين قوة 4-5 أيام/أسبوع\n"
            f"• مبدأ التحميل التدريجي (زد الوزن كل أسبوع)\n"
            f"• 6-12 تكرار لكل مجموعة\n"
            f"• راحة 48-72 ساعة لكل عضلة\n\n"
            f"**الثالوث المقدس:**\n"
            f"1. التمرين الصحيح ✅\n"
            f"2. الغذاء الكافي ✅\n"
            f"3. النوم 7-9 ساعات ✅\n\n"
            f"بدون واحد منها = نتائج نصف! 🔥"
        )

    def _handle_exercise(self, msg, user_data, ctx, muscle: str):
        name  = self._get_name(user_data)
        level = self._get_level(user_data)
        exs   = self.knowledge.EXERCISES.get(muscle, {})

        ex_list  = self._exercises_for_level(muscle, level)
        tips     = exs.get("posture_tips", [])
        muscles  = exs.get("muscles", "")
        title    = exs.get("title", "💪 التمارين")

        level_text = {
            "beast": "متقدم 🔥", "strong": "متقدم 💪",
            "medium": "متوسط ⚡", "light": "مبتدئ+",
            "beginner": "مبتدئ 🌱",
        }.get(level, "")

        response = (
            f"{title} — مستواك: {level_text}\n\n"
            f"**تمارينك اليوم:**\n"
            + "".join(f"• {e}\n" for e in ex_list) +
            f"\n**العضلات المستهدفة:** {muscles}\n\n"
            f"**نصائح الوضعية الصحيحة:**\n"
            + "".join(f"✅ {t}\n" for t in tips[:3])
        )

        # إضافة pre/post workout
        nutrition = self.knowledge.NUTRITION
        response += (
            f"\n**قبل التمرين:**\n"
            f"• {random.choice(nutrition['pre_workout'])}\n"
            f"**بعد التمرين:**\n"
            f"• {random.choice(nutrition['post_workout'])}"
        )
        return response

    def _handle_cardio(self, msg, user_data, ctx):
        name  = self._get_name(user_data)
        goal  = user_data.get("goal", "maintain")
        age   = user_data.get("age", 25)
        cardio = self.knowledge.EXERCISES["cardio"]

        max_hr  = 220 - (age or 25)
        fat_low  = round(max_hr * 0.6)
        fat_high = round(max_hr * 0.7)

        cardio_recs = {
            "lose":      "HIIT 3×/أسبوع + LISS 2×/أسبوع",
            "gain":      "LISS خفيف 2×/أسبوع (للقلب فقط)",
            "maintain":  "LISS 3×/أسبوع أو HIIT 2×/أسبوع",
            "endurance": "LISS طويل 4×/أسبوع + HIIT 1×",
        }

        return (
            f"🏃 **الكارديو يا {name}:**\n\n"
            f"**معدل ضربات قلبك:**\n"
            f"• الأقصى: {max_hr} ضربة/دقيقة\n"
            f"• منطقة حرق الدهون: {fat_low}-{fat_high} ضربة/دقيقة\n\n"
            f"**أنواع الكارديو:**\n"
            + "".join(f"• **{k}**: {v}\n" for k, v in cardio["types"].items()) +
            f"\n**توصيتك ({goal}):**\n"
            f"• {cardio_recs.get(goal, cardio_recs['maintain'])}"
        )

    def _handle_general_exercise(self, msg, user_data, ctx):
        name  = self._get_name(user_data)
        level = self._get_level(user_data)
        goal  = user_data.get("goal", "maintain")

        programs = {
            ("beginner", "lose"):      "3 أيام كامل الجسم + 2 كارديو",
            ("beginner", "gain"):      "3 أيام كامل الجسم + تغذية جيدة",
            ("medium", "lose"):        "4 أيام (صدر/ظهر/أرجل/كتف) + 2 كارديو",
            ("medium", "gain"):        "4 أيام تقسيم عضلي + كارديو خفيف",
            ("strong", "gain"):        "5 أيام Push/Pull/Legs/Shoulders/Arms",
            ("beast", "gain"):         "6 أيام تقسيم متقدم + كارديو صباحي",
        }

        prog = programs.get((level, goal)) or "3-4 أيام أسبوعياً مع تقسيم عضلي مناسب"

        return (
            f"🏋️ **برنامج التمارين يا {name}:**\n\n"
            f"**توصيتك:** {prog}\n\n"
            f"**مبادئ البرنامج الصحيح:**\n"
            f"• تدريج: ابدأ خفيف وزد تدريجياً\n"
            f"• راحة: لكل عضلة 48 ساعة على الأقل\n"
            f"• تنوع: غير التمارين كل 6-8 أسابيع\n"
            f"• ثبات: الانتظام أهم من الشدة\n\n"
            f"أي عضلة تحب نبدأ بها؟ 💪"
        )

    def _handle_unknown(self, msg, user_data, ctx):
        name = self._get_name(user_data)
        suggestions = [
            "تمارين الصدر والظهر",
            "كم بروتين أحتاج يومياً؟",
            "كيف أخسر وزني؟",
            "خطة وجبات أسبوعية",
            "علاج ألم الظهر",
        ]
        return (
            f"ما فهمت سؤالك تماماً يا {name} 😅\n\n"
            f"حاول تسألني بشكل أوضح، مثل:\n"
            + "".join(f"• {s}\n" for s in suggestions[:3]) +
            f"\nأو اختر موضوعاً وأجاوبك! 💪"
        )

    def _get_pain_warning(self, exercise_intent: str, pain_zones: list) -> str:
        """يعطي تحذير مخصص حسب التمرين والألم المسجل"""
        warnings = {
            ("exercise_back",    "lower-back"):  "أسفل ظهرك مؤلم — تجنب الديدليفت وقلل الأوزان!",
            ("exercise_back",    "back"):        "ظهرك مؤلم — ركز على الوضعية وقلل الوزن كثيراً",
            ("exercise_legs",    "knee-r"):      "ركبتك اليمنى مؤلمة — قلل العمق في السكوات",
            ("exercise_legs",    "knee-l"):      "ركبتك اليسرى مؤلمة — قلل العمق في السكوات",
            ("exercise_chest",   "shoulder-r"):  "كتفك الأيمن مؤلم — قلل الوزن وراقب الإحساس",
            ("exercise_chest",   "shoulder-l"):  "كتفك الأيسر مؤلم — استشر طبيباً قبل البنش",
            ("exercise_shoulders","shoulder-r"): "كتفك الأيمن مؤلم — تمارين خفيفة فقط!",
            ("exercise_shoulders","shoulder-l"): "كتفك الأيسر مؤلم — تمارين خفيفة فقط!",
        }
        for zone in pain_zones:
            key = (exercise_intent, zone)
            if key in warnings:
                return warnings[key]
        return ""


# ══════════════════════════════════════════════════════════════
# 8. BAAKI AI — الواجهة الرئيسية
# ══════════════════════════════════════════════════════════════
class BaakiAI:
    """
    الكلاس الرئيسي — يجمع كل المكونات معاً
    كل مستخدم له instance خاص به مع سياق منفصل
    """

    def __init__(self):
        self.engine   = ResponseEngine()
        self.context  = ConversationContext()

    def chat(self, message: str, user_data: dict) -> dict:
        """
        الدالة الرئيسية للمحادثة
        تُرجع: { reply, intent, confidence, turn }
        """
        intent, confidence = IntentClassifier.classify(message)
        reply = self.engine.generate(message, user_data, self.context)

        return {
            "reply":      reply,
            "intent":     intent,
            "confidence": round(confidence, 2),
            "turn":       self.context.turn_count,
        }

    def reset(self):
        """إعادة تشغيل المحادثة"""
        self.context = ConversationContext()


# ══════════════════════════════════════════════════════════════
# اختبار مباشر
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("🧠 اختبار باكي AI\n" + "═" * 40)

    ai = BaakiAI()
    user = {
        "name": "علي", "wt": 80, "ht": 175, "age": 22,
        "gender": "male", "goal": "gain", "lvl": "medium",
        "cal": 2800, "prot": 160, "carb": 315, "fat": 78,
        "wgoal": 10, "pain": [], "ram": False,
    }

    tests = [
        "السلام عليكم",
        "وش تمارين الصدر المناسبة لي؟",
        "كم بروتين أحتاج يومياً؟",
        "وزني 80 وطولي 175 احسب bmi",
        "عندي ألم في ظهري",
        "محفزني أكمل تدريبي",
    ]

    for q in tests:
        result = ai.chat(q, user)
        print(f"\n❓ {q}")
        print(f"🏷  Intent: {result['intent']} ({result['confidence']})")
        print(f"🤖 باكي: {result['reply'][:120]}...")
        print("-" * 40)
