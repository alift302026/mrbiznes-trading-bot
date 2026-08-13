import random


LANGUAGES = {
    "fa",
    "en",
    "ar",
}


BEHAVIOR_BANK = [
    {
        "id": "sleep_good",
        "category": "mental",
        "positive": True,
        "critical": False,

        "fa": "😴 دیشب واقعاً خوب خوابیدی یا با مغز نیمه‌خاموش اومدی سراغ چارت؟",
        "en": "😴 Did you actually sleep well, or are you bringing a half-awake brain to the chart?",
        "ar": "😴 هل نمت جيداً فعلاً أم أتيت إلى الشارت بذهن مرهق؟",
    },

    {
        "id": "focus_good",
        "category": "mental",
        "positive": True,
        "critical": False,

        "fa": "🎯 الان اگر ۲۰ دقیقه فقط روی یک کار تمرکز کنی، حواست جمع می‌مونه؟",
        "en": "🎯 If you focus on one task for 20 minutes right now, can you stay locked in?",
        "ar": "🎯 إذا ركزت على مهمة واحدة لمدة 20 دقيقة الآن، هل تستطيع الحفاظ على تركيزك؟",
    },

    {
        "id": "stress_low",
        "category": "mental",
        "positive": True,
        "critical": False,

        "fa": "😌 الان ذهنت آرومه و فشار شدید بیرونی روی تصمیم‌هات نداری؟",
        "en": "😌 Is your mind relatively calm without heavy outside pressure affecting your decisions?",
        "ar": "😌 هل ذهنك هادئ نسبياً ولا يوجد ضغط شديد يؤثر على قراراتك؟",
    },

    {
        "id": "physical_energy",
        "category": "mental",
        "positive": True,
        "critical": False,

        "fa": "⚡ از نظر انرژی بدنی حس می‌کنی برای تصمیم‌های دقیق آماده‌ای؟",
        "en": "⚡ Do you physically feel alert enough for careful decisions?",
        "ar": "⚡ هل تشعر جسدياً بأنك يقظ بما يكفي لاتخاذ قرارات دقيقة؟",
    },

    {
        "id": "anger_low",
        "category": "emotion",
        "positive": True,
        "critical": False,

        "fa": "🧊 الان می‌تونی بدون عصبانیت و هیجان اضافه بازار رو نگاه کنی؟",
        "en": "🧊 Can you look at the market without excessive anger or excitement right now?",
        "ar": "🧊 هل تستطيع النظر إلى السوق الآن دون غضب أو حماس مفرط؟",
    },

    {
        "id": "fomo_control",
        "category": "emotion",
        "positive": True,
        "critical": False,

        "fa": "🚀 اگر یه کندل بدون تو پرواز کنه، می‌تونی دنبالش نپری؟",
        "en": "🚀 If a candle takes off without you, can you resist chasing it?",
        "ar": "🚀 إذا انطلقت شمعة بدونك، هل تستطيع مقاومة مطاردتها؟",
    },

    {
        "id": "revenge",
        "category": "emotion",
        "positive": False,
        "critical": True,

        "fa": "🔥 ته دلت حس می‌کنی باید ضرر قبلی رو همین امروز از بازار پس بگیری؟",
        "en": "🔥 Deep down, do you feel you must win back a previous loss today?",
        "ar": "🔥 هل تشعر في داخلك أنك يجب أن تستعيد خسارة سابقة اليوم؟",
    },

    {
        "id": "overconfidence",
        "category": "emotion",
        "positive": False,
        "critical": False,

        "fa": "👑 حس می‌کنی امروز بازار رو کامل خوندی و تقریباً امکان اشتباهت کمه؟",
        "en": "👑 Do you feel you've completely figured out the market today and can barely be wrong?",
        "ar": "👑 هل تشعر أنك فهمت السوق بالكامل اليوم وأن احتمال خطئك ضعيف جداً؟",
    },

    {
        "id": "plan_ready",
        "category": "discipline",
        "positive": True,
        "critical": False,

        "fa": "📋 قبل از ورود، Entry و SL و دلیل معامله رو مشخص می‌کنی؟",
        "en": "📋 Before entering, will you define your entry, stop loss, and reason for the trade?",
        "ar": "📋 قبل الدخول، هل تحدد نقطة الدخول ووقف الخسارة وسبب الصفقة؟",
    },

    {
        "id": "accept_stop",
        "category": "discipline",
        "positive": True,
        "critical": True,

        "fa": "🛑 اگر قیمت به حد ضررت برسه، می‌تونی بدون جنگیدن با بازار قبولش کنی؟",
        "en": "🛑 If price reaches your stop, can you accept it without fighting the market?",
        "ar": "🛑 إذا وصل السعر إلى وقف الخسارة، هل تستطيع تقبله دون مقاومة السوق؟",
    },

    {
        "id": "risk_size",
        "category": "discipline",
        "positive": True,
        "critical": True,

        "fa": "⚖️ حجم معامله‌ات از قبل بر اساس ریسک مشخص می‌شه، نه هیجان لحظه؟",
        "en": "⚖️ Is your position size decided by predefined risk rather than emotion?",
        "ar": "⚖️ هل تحدد حجم الصفقة بناءً على مخاطرة مسبقة وليس على العاطفة؟",
    },

    {
        "id": "can_skip",
        "category": "discipline",
        "positive": True,
        "critical": False,

        "fa": "🚪 اگر ستاپ خوب نباشه، واقعاً می‌تونی امروز اصلاً ترید نکنی؟",
        "en": "🚪 If there is no clean setup, can you genuinely skip trading today?",
        "ar": "🚪 إذا لم توجد فرصة واضحة، هل تستطيع فعلاً عدم التداول اليوم؟",
    },

    {
        "id": "financial_pressure",
        "category": "mental",
        "positive": False,
        "critical": True,

        "fa": "💸 آیا برای خرج ضروری یا فشار مالی، به سود امروز بازار احتیاج داری؟",
        "en": "💸 Do you need today's trading profit for an essential expense or financial pressure?",
        "ar": "💸 هل تحتاج إلى ربح تداول اليوم بسبب مصروف ضروري أو ضغط مالي؟",
    },

    {
        "id": "too_many_trades",
        "category": "discipline",
        "positive": False,
        "critical": False,

        "fa": "🔁 امروز از همین الان میل داری پشت‌سرهم چند معامله باز کنی؟",
        "en": "🔁 Do you already feel an urge to open several trades back-to-back today?",
        "ar": "🔁 هل تشعر منذ الآن برغبة في فتح عدة صفقات متتالية اليوم؟",
    },
]


COGNITIVE_TEMPLATES = [
    {
        "type": "math",
        "builder": "addition",
    },
    {
        "type": "math",
        "builder": "subtraction",
    },
    {
        "type": "math",
        "builder": "multiplication",
    },
    {
        "type": "pattern",
        "builder": "double",
    },
    {
        "type": "pattern",
        "builder": "step",
    },
    {
        "type": "logic",
        "builder": "comparison",
    },
]


def get_language(language):
    if language in LANGUAGES:
        return language

    return "en"


def random_wrong_answers(
    correct,
    count=3,
):
    output = set()

    while len(output) < count:
        offset = random.choice(
            [-12, -9, -7, -5, -3, 2, 4, 6, 8, 11]
        )

        candidate = correct + offset

        if (
            candidate != correct
            and candidate >= 0
        ):
            output.add(candidate)

    return list(output)


def cognitive_question(
    language,
):
    language = get_language(
        language
    )

    template = random.choice(
        COGNITIVE_TEMPLATES
    )

    builder = template[
        "builder"
    ]

    if builder == "addition":

        a = random.randint(
            11,
            39,
        )

        b = random.randint(
            12,
            38,
        )

        correct = a + b

        question = {
            "fa": "⚡ سریع ولی دقیق: {} + {} چند میشه؟",
            "en": "⚡ Quick but accurate: what is {} + {}?",
            "ar": "⚡ بسرعة وبدقة: كم يساوي {} + {}؟",
        }[language].format(
            a,
            b,
        )

    elif builder == "subtraction":

        a = random.randint(
            40,
            90,
        )

        b = random.randint(
            11,
            35,
        )

        correct = a - b

        question = {
            "fa": "🧠 تمرکز روشنه؟ {} - {} چند میشه؟",
            "en": "🧠 Focus check: what is {} - {}?",
            "ar": "🧠 اختبار التركيز: كم يساوي {} - {}؟",
        }[language].format(
            a,
            b,
        )

    elif builder == "multiplication":

        a = random.randint(
            3,
            12,
        )

        b = random.randint(
            3,
            9,
        )

        correct = a * b

        question = {
            "fa": "🎯 یه ضرب کوتاه: {} × {} = ؟",
            "en": "🎯 Short multiplication: {} × {} = ?",
            "ar": "🎯 عملية ضرب قصيرة: {} × {} = ؟",
        }[language].format(
            a,
            b,
        )

    elif builder == "double":

        start = random.randint(
            2,
            6,
        )

        values = [
            start,
            start * 2,
            start * 4,
            start * 8,
        ]

        correct = (
            start * 16
        )

        question = {
            "fa": "🧩 عدد بعدی چیه؟ {}، {}، {}، {}، ؟",
            "en": "🧩 What comes next? {}, {}, {}, {}, ?",
            "ar": "🧩 ما الرقم التالي؟ {}، {}، {}، {}، ؟",
        }[language].format(
            *values
        )

    elif builder == "step":

        start = random.randint(
            2,
            15,
        )

        step = random.randint(
            3,
            8,
        )

        values = [
            start,
            start + step,
            start + step * 2,
            start + step * 3,
        ]

        correct = (
            start
            + step * 4
        )

        question = {
            "fa": "🔍 الگو رو بگیر: {}، {}، {}، {}، ؟",
            "en": "🔍 Catch the pattern: {}, {}, {}, {}, ?",
            "ar": "🔍 اكتشف النمط: {}، {}، {}، {}، ؟",
        }[language].format(
            *values
        )

    else:

        correct = 1

        if language == "fa":
            question = (
                "🧠 اگر A از B بزرگ‌تر باشد و B از C بزرگ‌تر باشد، کدام قطعاً درست است؟"
            )

            options = [
                ("A > C", 1),
                ("C > A", 0),
                ("A = C", 0),
                ("اطلاعات کافی نیست", 0),
            ]

        elif language == "ar":
            question = (
                "🧠 إذا كان A أكبر من B و B أكبر من C، فما العبارة الصحيحة بالتأكيد؟"
            )

            options = [
                ("A > C", 1),
                ("C > A", 0),
                ("A = C", 0),
                ("المعلومات غير كافية", 0),
            ]

        else:
            question = (
                "🧠 If A is greater than B and B is greater than C, what must be true?"
            )

            options = [
                ("A > C", 1),
                ("C > A", 0),
                ("A = C", 0),
                ("Not enough information", 0),
            ]

        random.shuffle(
            options
        )

        return {
            "type": "cognitive",
            "category": "cognitive",
            "question": question,
            "options": [
                text
                for text, _
                in options
            ],
            "correct_index": next(
                index
                for index, item
                in enumerate(options)
                if item[1] == 1
            ),
        }

    wrong = random_wrong_answers(
        correct,
    )

    values = [
        correct,
        *wrong,
    ]

    random.shuffle(
        values
    )

    return {
        "type": "cognitive",
        "category": "cognitive",
        "question": question,
        "options": [
            str(value)
            for value in values
        ],
        "correct_index": (
            values.index(
                correct
            )
        ),
    }


def behavioral_question(
    item,
    language,
):
    return {
        "type": "behavior",
        "id": item["id"],
        "category": item["category"],
        "question": item[language],
        "positive": item["positive"],
        "critical": item["critical"],
        "options": None,
    }


def build_test(
    language,
):
    language = get_language(
        language
    )

    mental = [
        item
        for item
        in BEHAVIOR_BANK
        if item["category"]
        == "mental"
    ]

    emotion = [
        item
        for item
        in BEHAVIOR_BANK
        if item["category"]
        == "emotion"
    ]

    discipline = [
        item
        for item
        in BEHAVIOR_BANK
        if item["category"]
        == "discipline"
    ]

    selected = []

    selected.extend(
        random.sample(
            mental,
            2,
        )
    )

    selected.extend(
        random.sample(
            emotion,
            2,
        )
    )

    selected.extend(
        random.sample(
            discipline,
            2,
        )
    )

    random.shuffle(
        selected
    )

    questions = [
        behavioral_question(
            item,
            language,
        )
        for item in selected
    ]

    questions.extend(
        cognitive_question(
            language
        )
        for _ in range(3)
    )

    random.shuffle(
        questions
    )

    return questions


def score_behavior_answer(
    question,
    answer_yes,
):
    if question["positive"]:
        return (
            100
            if answer_yes
            else 0
        )

    return (
        0
        if answer_yes
        else 100
    )


def average(values):
    if not values:
        return 0

    return round(
        sum(values)
        / len(values)
    )


def calculate_report(
    questions,
    answers,
):
    mental = []
    emotion = []
    discipline = []
    cognitive = []

    critical_reasons = []

    for question, answer in zip(
        questions,
        answers,
    ):
        if (
            question["type"]
            == "cognitive"
        ):
            correct = (
                answer
                == question[
                    "correct_index"
                ]
            )

            cognitive.append(
                100
                if correct
                else 0
            )

            continue

        answer_yes = bool(
            answer
        )

        value = score_behavior_answer(
            question,
            answer_yes,
        )

        category = question[
            "category"
        ]

        if category == "mental":
            mental.append(value)

        elif category == "emotion":
            emotion.append(value)

        elif category == "discipline":
            discipline.append(value)

        if question["critical"]:
            risky = (
                not answer_yes
                if question["positive"]
                else answer_yes
            )

            if risky:
                critical_reasons.append(
                    question["id"]
                )

    mental_score = average(
        mental
    )

    emotion_score = average(
        emotion
    )

    discipline_score = average(
        discipline
    )

    cognitive_score = average(
        cognitive
    )

    overall = round(
        mental_score * 0.25
        + emotion_score * 0.25
        + discipline_score * 0.30
        + cognitive_score * 0.20
    )

    if overall >= 75:
        level = 3

    elif overall >= 50:
        level = 2

    else:
        level = 1

    return {
        "mental_score":
            mental_score,

        "emotion_score":
            emotion_score,

        "discipline_score":
            discipline_score,

        "cognitive_score":
            cognitive_score,

        "overall_score":
            overall,

        "level":
            level,

        "critical_flag":
            bool(
                critical_reasons
            ),

        "critical_reasons":
            critical_reasons,
    }


def bar(
    score,
):
    filled = round(
        score / 10
    )

    return (
        "█" * filled
        + "░" * (
            10 - filled
        )
    )