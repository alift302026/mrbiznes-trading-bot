import json

from datetime import (
    datetime,
    timedelta,
)

from sqlalchemy import (
    delete,
    desc,
    select,
)

from app.models.database import (
    SessionLocal,
)

from app.models.psychology import (
    EndOfDayCheck,
    PsychologyAssessment,
)


def save_assessment(
    telegram_id,
    questions,
    answers,
    report,
):
    with SessionLocal() as db:

        item = PsychologyAssessment(
            telegram_id=telegram_id,

            mental_score=report[
                "mental_score"
            ],

            cognitive_score=report[
                "cognitive_score"
            ],

            discipline_score=report[
                "discipline_score"
            ],

            emotion_score=report[
                "emotion_score"
            ],

            overall_score=report[
                "overall_score"
            ],

            level=report[
                "level"
            ],

            critical_flag=report[
                "critical_flag"
            ],

            critical_reasons=json.dumps(
                report[
                    "critical_reasons"
                ],
                ensure_ascii=False,
            ),

            question_set=json.dumps(
                questions,
                ensure_ascii=False,
            ),

            answers=json.dumps(
                answers,
                ensure_ascii=False,
            ),
        )

        db.add(item)
        db.commit()
        db.refresh(item)

        return item


def latest_assessment(
    telegram_id,
):
    with SessionLocal() as db:

        return db.scalar(
            select(
                PsychologyAssessment
            )
            .where(
                PsychologyAssessment.telegram_id
                == telegram_id
            )
            .order_by(
                desc(
                    PsychologyAssessment.created_at
                )
            )
            .limit(1)
        )


def history(
    telegram_id,
    limit=15,
):
    with SessionLocal() as db:

        return list(
            db.scalars(
                select(
                    PsychologyAssessment
                )
                .where(
                    PsychologyAssessment.telegram_id
                    == telegram_id
                )
                .order_by(
                    desc(
                        PsychologyAssessment.created_at
                    )
                )
                .limit(limit)
            ).all()
        )


def today_assessment(
    telegram_id,
):
    now = datetime.utcnow()

    start = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    with SessionLocal() as db:

        return db.scalar(
            select(
                PsychologyAssessment
            )
            .where(
                PsychologyAssessment.telegram_id
                == telegram_id,

                PsychologyAssessment.created_at
                >= start,
            )
            .order_by(
                desc(
                    PsychologyAssessment.created_at
                )
            )
            .limit(1)
        )


def calculate_streak(
    telegram_id,
):
    items = history(
        telegram_id,
        limit=60,
    )

    if not items:
        return 0

    unique_dates = sorted(
        {
            item.created_at.date()
            for item in items
        },
        reverse=True,
    )

    streak = 1

    current = unique_dates[0]

    for date in unique_dates[1:]:

        if (
            current - date
        ).days == 1:

            streak += 1
            current = date

        else:
            break

    return streak


def averages(
    telegram_id,
    days=7,
):
    cutoff = (
        datetime.utcnow()
        - timedelta(
            days=days
        )
    )

    with SessionLocal() as db:

        items = list(
            db.scalars(
                select(
                    PsychologyAssessment
                )
                .where(
                    PsychologyAssessment.telegram_id
                    == telegram_id,

                    PsychologyAssessment.created_at
                    >= cutoff,
                )
            ).all()
        )

    if not items:
        return None

    count = len(items)

    return {
        "mental":
            round(
                sum(
                    item.mental_score
                    for item in items
                )
                / count
            ),

        "cognitive":
            round(
                sum(
                    item.cognitive_score
                    for item in items
                )
                / count
            ),

        "discipline":
            round(
                sum(
                    item.discipline_score
                    for item in items
                )
                / count
            ),

        "emotion":
            round(
                sum(
                    item.emotion_score
                    for item in items
                )
                / count
            ),

        "overall":
            round(
                sum(
                    item.overall_score
                    for item in items
                )
                / count
            ),
    }


def save_eod(
    telegram_id,
    followed_plan,
    respected_stop,
    emotional_trade,
):
    with SessionLocal() as db:

        item = EndOfDayCheck(
            telegram_id=telegram_id,
            followed_plan=followed_plan,
            respected_stop=respected_stop,
            emotional_trade=emotional_trade,
        )

        db.add(item)
        db.commit()


def delete_psychology_history(
    telegram_id,
):
    with SessionLocal() as db:

        db.execute(
            delete(
                PsychologyAssessment
            ).where(
                PsychologyAssessment.telegram_id
                == telegram_id
            )
        )

        db.execute(
            delete(
                EndOfDayCheck
            ).where(
                EndOfDayCheck.telegram_id
                == telegram_id
            )
        )

        db.commit()