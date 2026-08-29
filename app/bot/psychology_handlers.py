from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    ContextTypes,
)

from app.engines.psychology.readiness_engine import (
    bar,
    build_test,
    calculate_report,
)

from app.services.psychology_service import (
    averages,
    calculate_streak,
    delete_psychology_history,
    history,
    latest_assessment,
    save_assessment,
)

from app.services.user_service import (
    get_user,
)


def lang(
    telegram_id,
):
    user = get_user(
        telegram_id
    )

    if (
        user
        and user.language
        in {
            "fa",
            "en",
            "ar",
        }
    ):
        return user.language

    return "en"


def home_keyboard(
    language,
):
    labels = {
        "fa": {
            "start": "🚀 بزن بریم تست امروز",
            "latest": "🎯 نتیجه آخر من",
            "progress": "📈 پیشرفت من",
            "history": "📜 تاریخچه",
            "privacy": "🔐 حریم خصوصی",
        },

        "en": {
            "start": "🚀 Start Today's Check",
            "latest": "🎯 My Latest Result",
            "progress": "📈 My Progress",
            "history": "📜 History",
            "privacy": "🔐 Privacy",
        },

        "ar": {
            "start": "🚀 ابدأ اختبار اليوم",
            "latest": "🎯 آخر نتيجة",
            "progress": "📈 تقدمي",
            "history": "📜 السجل",
            "privacy": "🔐 الخصوصية",
        },
    }[language]

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    labels["start"],
                    callback_data="psy_start",
                )
            ],
            [
                InlineKeyboardButton(
                    labels["latest"],
                    callback_data="psy_latest",
                ),
                InlineKeyboardButton(
                    labels["progress"],
                    callback_data="psy_progress",
                ),
            ],
            [
                InlineKeyboardButton(
                    labels["history"],
                    callback_data="psy_history",
                ),
                InlineKeyboardButton(
                    labels["privacy"],
                    callback_data="psy_privacy",
                ),
            ],
        ]
    )


def intro(
    language,
):
    if language == "fa":
        return (
            "🧠 ALIFT TRADER READINESS\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "خب تریدر، قبل اینکه بازار تو رو امتحان کنه، "
            "ببینیم خودت امروز چند چندی 😎\n\n"
            "این یه تست سرگرمی الکی نیست.\n\n"
            "ساختارش با الهام از اصول شناخته‌شده سنجش "
            "استرس، کیفیت استراحت، توجه، کنترل هیجان، "
            "انضباط و مدیریت ریسک طراحی شده.\n\n"
            "🎯 ۹ مرحله\n"
            "🧠 ۶ سؤال رفتاری متغیر\n"
            "⚡ ۳ چالش هوشیاری متغیر\n"
            "🔀 سؤال‌ها و ترتیبشان تغییر می‌کنند\n"
            "⏱ حدود ۶۰ تا ۹۰ ثانیه\n\n"
            "آخرش یه گزارش خشک تحویلت نمی‌دیم؛ "
            "Mental، Focus، Discipline، Emotion و "
            "Level امروزت رو می‌بینی.\n\n"
            "⚠️ این ابزار تست IQ، تشخیص پزشکی یا "
            "توصیه مالی نیست."
        )

    if language == "ar":
        return (
            "🧠 ALIFT TRADER READINESS\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "قبل أن يختبرك السوق، دعنا نرى مدى "
            "جاهزيتك اليوم 😎\n\n"
            "9 مراحل قصيرة، تشمل السلوك والانضباط "
            "والتركيز والوعي المعرفي.\n\n"
            "الأسئلة تتغير في كل مرة.\n\n"
            "⚠️ ليست هذه أداة IQ أو تشخيصاً طبياً "
            "أو توصية مالية."
        )

    return (
        "🧠 ALIFT TRADER READINESS\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "Before the market tests you, "
        "let's see how ready you are today 😎\n\n"
        "This isn't a random entertainment quiz.\n\n"
        "Its structure is inspired by established "
        "principles of stress, rest, attention, "
        "emotional control, discipline and risk awareness.\n\n"
        "🎯 9 stages\n"
        "🧠 6 rotating behavioral questions\n"
        "⚡ 3 rotating cognitive challenges\n"
        "🔀 Questions and options change\n"
        "⏱ Around 60–90 seconds\n\n"
        "⚠️ This is not an IQ test, medical diagnosis "
        "or financial advice."
    )


async def psychology_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    language = lang(
        update.effective_user.id
    )

    await update.message.reply_text(
        intro(language),
        reply_markup=home_keyboard(
            language
        ),
    )


def behavior_keyboard(
    index,
    language,
):
    yes = {
        "fa": "✅ آره، کاملاً",
        "en": "✅ Yep",
        "ar": "✅ نعم",
    }[language]

    no = {
        "fa": "❌ نه، راستش",
        "en": "❌ Not really",
        "ar": "❌ لا",
    }[language]

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    yes,
                    callback_data=(
                        "psy_b_{}_1"
                    ).format(index),
                ),
                InlineKeyboardButton(
                    no,
                    callback_data=(
                        "psy_b_{}_0"
                    ).format(index),
                ),
            ]
        ]
    )


def cognitive_keyboard(
    index,
    question,
):
    rows = []

    options = question[
        "options"
    ]

    for option_index in range(
        0,
        len(options),
        2,
    ):
        row = []

        for i in range(
            option_index,
            min(
                option_index + 2,
                len(options),
            ),
        ):
            row.append(
                InlineKeyboardButton(
                    options[i],
                    callback_data=(
                        "psy_c_{}_{}"
                    ).format(
                        index,
                        i,
                    ),
                )
            )

        rows.append(row)

    return InlineKeyboardMarkup(
        rows
    )


def encouragement(
    language,
    index,
):
    fa = [
        "🔥 شروع کردیم!",
        "👌 خوب اومدی جلو.",
        "🎯 تمرکزت رو نگه دار.",
        "⚡ حالا یه کم جذاب‌تر!",
        "😎 نصف راه رو خوردیم.",
        "🧠 هنوز باهامی؟ عالیه.",
        "🚀 فقط سه مرحله دیگه.",
        "🔥 یکی مونده بعد این!",
        "🏁 سؤال آخر؛ بزن تمومش کنیم!",
    ]

    en = [
        "🔥 We're on!",
        "👌 Nice, keep going.",
        "🎯 Stay focused.",
        "⚡ Let's make it interesting.",
        "😎 Halfway there.",
        "🧠 Still with me? Great.",
        "🚀 Just a few left.",
        "🔥 Almost there.",
        "🏁 Final one. Finish strong!",
    ]

    ar = [
        "🔥 بدأنا!",
        "👌 ممتاز، استمر.",
        "🎯 حافظ على تركيزك.",
        "⚡ الآن يصبح الأمر أكثر إثارة.",
        "😎 قطعنا نصف الطريق.",
        "🧠 ممتاز، استمر معنا.",
        "🚀 بقي القليل.",
        "🔥 اقتربنا من النهاية.",
        "🏁 السؤال الأخير!",
    ]

    source = {
        "fa": fa,
        "en": en,
        "ar": ar,
    }[language]

    return source[
        min(
            index,
            8,
        )
    ]


async def show_question(
    query,
    user_id,
    index,
    questions,
):
    language = lang(
        user_id
    )

    question = questions[
        index
    ]

    progress = (
        "●" * index
        + "○" * (
            9 - index
        )
    )

    if language == "fa":
        header = (
            "{}\n"
            "{}\n\n"
            "مرحله {} از ۹\n\n"
            "{}"
        ).format(
            encouragement(
                language,
                index,
            ),
            progress,
            index + 1,
            question["question"],
        )

    elif language == "ar":
        header = (
            "{}\n"
            "{}\n\n"
            "المرحلة {} من 9\n\n"
            "{}"
        ).format(
            encouragement(
                language,
                index,
            ),
            progress,
            index + 1,
            question["question"],
        )

    else:
        header = (
            "{}\n"
            "{}\n\n"
            "Stage {} of 9\n\n"
            "{}"
        ).format(
            encouragement(
                language,
                index,
            ),
            progress,
            index + 1,
            question["question"],
        )

    if (
        question["type"]
        == "behavior"
    ):
        keyboard = (
            behavior_keyboard(
                index,
                language,
            )
        )

    else:
        keyboard = (
            cognitive_keyboard(
                index,
                question,
            )
        )

    await query.edit_message_text(
        header,
        reply_markup=keyboard,
    )


def level_text(
    language,
    level,
):
    if language == "fa":
        return {
            3: "🟢 LEVEL 3 — آمادگی بالا",
            2: "🟠 LEVEL 2 — آمادگی متوسط",
            1: "🔴 LEVEL 1 — آمادگی پایین",
        }[level]

    if language == "ar":
        return {
            3: "🟢 LEVEL 3 — استعداد مرتفع",
            2: "🟠 LEVEL 2 — استعداد متوسط",
            1: "🔴 LEVEL 1 — استعداد منخفض",
        }[level]

    return {
        3: "🟢 LEVEL 3 — HIGH READINESS",
        2: "🟠 LEVEL 2 — MODERATE",
        1: "🔴 LEVEL 1 — LOW READINESS",
    }[level]


def report_text(
    language,
    report,
    streak,
):
    if language == "fa":
        critical = ""

        if report[
            "critical_flag"
        ]:
            critical = (
                "\n\n⚠️ هشدار انضباطی\n"
                "حداقل یک پاسخ پرریسک شناسایی شد. "
                "امتیاز کلی بالا هم این هشدار را حذف نمی‌کند."
            )

        return (
            "🧠 ALIFT READINESS REPORT\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "🧘 آمادگی ذهنی\n"
            "{} {} / 100\n\n"
            "⚡ هوشیاری شناختی\n"
            "{} {} / 100\n\n"
            "🛡 انضباط و ریسک\n"
            "{} {} / 100\n\n"
            "🔥 کنترل هیجان\n"
            "{} {} / 100\n\n"
            "🎯 امتیاز نهایی\n"
            "{} {} / 100\n\n"
            "{}\n\n"
            "🔥 Discipline Streak: {} روز"
            "{}\n\n"
            "⚠️ این گزارش ابزار خودارزیابی است، "
            "نه مجوز معامله یا تضمین سود."
        ).format(
            bar(
                report["mental_score"]
            ),
            report["mental_score"],

            bar(
                report["cognitive_score"]
            ),
            report["cognitive_score"],

            bar(
                report["discipline_score"]
            ),
            report["discipline_score"],

            bar(
                report["emotion_score"]
            ),
            report["emotion_score"],

            bar(
                report["overall_score"]
            ),
            report["overall_score"],

            level_text(
                language,
                report["level"],
            ),

            streak,

            critical,
        )

    if language == "ar":
        return (
            "🧠 ALIFT READINESS REPORT\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "🧘 الاستعداد الذهني: {}/100\n"
            "⚡ اليقظة المعرفية: {}/100\n"
            "🛡 الانضباط والمخاطر: {}/100\n"
            "🔥 التحكم العاطفي: {}/100\n\n"
            "🎯 النتيجة: {}/100\n"
            "{}\n\n"
            "🔥 الاستمرارية: {} يوم\n\n"
            "⚠️ هذا تقييم ذاتي وليس توصية مالية."
        ).format(
            report["mental_score"],
            report["cognitive_score"],
            report["discipline_score"],
            report["emotion_score"],
            report["overall_score"],
            level_text(
                language,
                report["level"],
            ),
            streak,
        )

    return (
        "🧠 ALIFT READINESS REPORT\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "🧘 Mental Readiness\n"
        "{} {}/100\n\n"
        "⚡ Cognitive Alertness\n"
        "{} {}/100\n\n"
        "🛡 Risk Discipline\n"
        "{} {}/100\n\n"
        "🔥 Emotional Control\n"
        "{} {}/100\n\n"
        "🎯 OVERALL\n"
        "{} {}/100\n\n"
        "{}\n\n"
        "🔥 Discipline Streak: {} days\n\n"
        "⚠️ This is a self-assessment tool, "
        "not trading permission or a profit guarantee."
    ).format(
        bar(
            report["mental_score"]
        ),
        report["mental_score"],

        bar(
            report["cognitive_score"]
        ),
        report["cognitive_score"],

        bar(
            report["discipline_score"]
        ),
        report["discipline_score"],

        bar(
            report["emotion_score"]
        ),
        report["emotion_score"],

        bar(
            report["overall_score"]
        ),
        report["overall_score"],

        level_text(
            language,
            report["level"],
        ),

        streak,
    )


async def psychology_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = (
        update.callback_query
    )

    if query is None:
        return

    await query.answer()

    user_id = (
        query.from_user.id
    )

    language = lang(
        user_id
    )

    data = query.data

    if data == "psy_start":

        questions = build_test(
            language
        )

        context.user_data[
            "psy_questions"
        ] = questions

        context.user_data[
            "psy_answers"
        ] = []

        await show_question(
            query,
            user_id,
            0,
            questions,
        )

        return

    if (
        data.startswith(
            "psy_b_"
        )
        or data.startswith(
            "psy_c_"
        )
    ):
        parts = data.split(
            "_"
        )

        if len(parts) != 4:
            return

        mode = parts[1]

        index = int(
            parts[2]
        )

        value = int(
            parts[3]
        )

        questions = (
            context.user_data
            .get(
                "psy_questions"
            )
        )

        answers = (
            context.user_data
            .get(
                "psy_answers"
            )
        )

        if (
            not questions
            or answers is None
        ):
            return

        if (
            len(answers)
            != index
        ):
            return

        if mode == "b":
            answers.append(
                bool(value)
            )

        else:
            answers.append(
                value
            )

        next_index = (
            index + 1
        )

        if next_index < 9:
            await show_question(
                query,
                user_id,
                next_index,
                questions,
            )
            return

        report = (
            calculate_report(
                questions,
                answers,
            )
        )

        save_assessment(
            telegram_id=user_id,
            questions=questions,
            answers=answers,
            report=report,
        )

        context.user_data.pop(
            "psy_questions",
            None,
        )

        context.user_data.pop(
            "psy_answers",
            None,
        )

        streak = calculate_streak(
            user_id
        )

        await query.edit_message_text(
            report_text(
                language,
                report,
                streak,
            ),
            reply_markup=(
                home_keyboard(
                    language
                )
            ),
        )

        return

    if data == "psy_latest":
        item = latest_assessment(
            user_id
        )

        if not item:
            text = {
                "fa": "هنوز تستی ثبت نکردی 😄",
                "en": "No check recorded yet 😄",
                "ar": "لم تسجل اختباراً بعد 😄",
            }[language]

        else:
            report = {
                "mental_score":
                    item.mental_score,

                "cognitive_score":
                    item.cognitive_score,

                "discipline_score":
                    item.discipline_score,

                "emotion_score":
                    item.emotion_score,

                "overall_score":
                    item.overall_score,

                "level":
                    item.level,

                "critical_flag":
                    item.critical_flag,
            }

            text = report_text(
                language,
                report,
                calculate_streak(
                    user_id
                ),
            )

        await query.edit_message_text(
            text,
            reply_markup=home_keyboard(
                language
            ),
        )
        return

    if data == "psy_progress":
        avg = averages(
            user_id,
            7,
        )

        if not avg:
            text = {
                "fa": "برای نمودار پیشرفت، چند روز باهامون Check-in کن 😉",
                "en": "Check in for a few days to build your progress profile 😉",
                "ar": "قم بالتقييم لعدة أيام لبناء ملف تقدمك 😉",
            }[language]

        else:
            text = (
                "📈 7-DAY PERSONAL AVERAGE\n"
                "━━━━━━━━━━━━━━━━\n\n"
                "Mental: {}/100\n"
                "Cognitive: {}/100\n"
                "Discipline: {}/100\n"
                "Emotion: {}/100\n\n"
                "Overall: {}/100\n\n"
                "🔥 Streak: {}"
            ).format(
                avg["mental"],
                avg["cognitive"],
                avg["discipline"],
                avg["emotion"],
                avg["overall"],
                calculate_streak(
                    user_id
                ),
            )

        await query.edit_message_text(
            text,
            reply_markup=home_keyboard(
                language
            ),
        )
        return

    if data == "psy_history":
        items = history(
            user_id,
            10,
        )

        if not items:
            text = {
                "fa": "📜 هنوز تاریخچه‌ای نداری.",
                "en": "📜 No history yet.",
                "ar": "📜 لا يوجد سجل حتى الآن.",
            }[language]

        else:
            lines = [
                "📜 READINESS HISTORY",
                "━━━━━━━━━━━━━━━━",
                "",
            ]

            for item in items:
                icon = (
                    "🟢"
                    if item.level == 3
                    else
                    "🟠"
                    if item.level == 2
                    else
                    "🔴"
                )

                lines.append(
                    "{} {} | {}/100 | L{}".format(
                        icon,
                        item.created_at.strftime(
                            "%Y/%m/%d"
                        ),
                        item.overall_score,
                        item.level,
                    )
                )

            text = "\n".join(
                lines
            )

        await query.edit_message_text(
            text,
            reply_markup=home_keyboard(
                language
            ),
        )
        return

    if data == "psy_privacy":
        labels = {
            "fa": (
                "🔐 پاسخ‌های این بخش برای ساخت تاریخچه شخصی "
                "Readiness ذخیره می‌شوند.\n\n"
                "می‌تونی هر زمان کل تاریخچه رو حذف کنی."
            ),
            "en": (
                "🔐 Your answers are stored to build your personal "
                "readiness history.\n\nYou can delete the history anytime."
            ),
            "ar": (
                "🔐 يتم حفظ إجاباتك لبناء سجل الاستعداد الشخصي.\n\n"
                "يمكنك حذف السجل في أي وقت."
            ),
        }

        await query.edit_message_text(
            labels[language],
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🗑 Delete History",
                            callback_data="psy_delete",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ Back",
                            callback_data="psy_home",
                        )
                    ],
                ]
            ),
        )
        return

    if data == "psy_delete":
        delete_psychology_history(
            user_id
        )

        await query.edit_message_text(
            {
                "fa": "✅ تاریخچه روانشناسی و Readiness حذف شد.",
                "en": "✅ Psychology and readiness history deleted.",
                "ar": "✅ تم حذف سجل الاستعداد.",
            }[language],
            reply_markup=home_keyboard(
                language
            ),
        )
        return

    if data == "psy_home":
        await query.edit_message_text(
            intro(language),
            reply_markup=home_keyboard(
                language
            ),
        )