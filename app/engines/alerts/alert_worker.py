from app.engines.alerts.market_alert_engine import (
    evaluate_alert,
    fetch_market_snapshot,
)

from app.services.alert_service import (
    active_alerts,
    mark_triggered,
    update_alert_state,
)

from app.services.user_service import (
    get_user,
)


def build_alert_message(
    alert,
    snapshot,
    language,
):
    price = snapshot[
        "price"
    ]

    rsi = snapshot[
        "rsi"
    ]

    if language == "fa":
        return (
            "🚨 MrBiznes MARKET ALERT\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "🪙 {}\n"
            "⏱ {}\n\n"
            "🔔 شرط آلارم فعال شد\n\n"
            "Type: {}\n"
            "💵 Price: {:,.8f}\n"
            "📊 RSI: {:.2f}\n\n"
            "Alert ID: #{}\n\n"
            "⚠️ این پیام صرفاً اطلاع‌رسانی است."
        ).format(
            alert.symbol,
            alert.timeframe,
            alert.alert_type,
            price,
            rsi,
            alert.id,
        )

    if language == "ar":
        return (
            "🚨 MrBiznes MARKET ALERT\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "🪙 {}\n"
            "⏱ {}\n\n"
            "🔔 تم تفعيل شرط التنبيه\n\n"
            "💵 السعر: {:,.8f}\n"
            "📊 RSI: {:.2f}\n\n"
            "Alert #{}"
        ).format(
            alert.symbol,
            alert.timeframe,
            price,
            rsi,
            alert.id,
        )

    return (
        "🚨 MrBiznes MARKET ALERT\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "🪙 {}\n"
        "⏱ {}\n\n"
        "🔔 Alert condition triggered\n\n"
        "Type: {}\n"
        "💵 Price: {:,.8f}\n"
        "📊 RSI: {:.2f}\n\n"
        "Alert ID: #{}\n\n"
        "⚠️ Informational alert only."
    ).format(
        alert.symbol,
        alert.timeframe,
        alert.alert_type,
        price,
        rsi,
        alert.id,
    )


async def market_alert_job(
    context,
):
    alerts = active_alerts()

    if not alerts:
        return

    # یک بار دریافت دیتا برای
    # هر Symbol + Timeframe
    snapshots = {}

    for alert in alerts:
        key = (
            alert.symbol,
            alert.timeframe,
        )

        try:
            if key not in snapshots:
                snapshots[key] = (
                    await fetch_market_snapshot(
                        alert.symbol,
                        alert.timeframe,
                    )
                )

            snapshot = (
                snapshots[key]
            )

            triggered, state = (
                evaluate_alert(
                    alert,
                    snapshot,
                )
            )

            one_shot = (
                alert.alert_type
                in {
                    "price_above",
                    "price_below",
                }
            )

            if alert.alert_type in {
                "ema_bull",
                "ema_bear",
                "macd_bull",
                "macd_bear",
            }:
                should_send = (
                    triggered
                )

            else:
                should_send = (
                    triggered
                    and
                    alert.last_state
                    != state
                )

            if should_send:
                user = get_user(
                    alert.telegram_id
                )

                language = (
                    user.language
                    if (
                        user
                        and user.language
                        in {
                            "fa",
                            "en",
                            "ar",
                        }
                    )
                    else "en"
                )

                message = (
                    build_alert_message(
                        alert,
                        snapshot,
                        language,
                    )
                )

                await context.bot.send_message(
                    chat_id=(
                        alert.telegram_id
                    ),
                    text=message,
                )

                mark_triggered(
                    alert.id,
                    state,
                    disable=one_shot,
                )

            else:
                update_alert_state(
                    alert.id,
                    state,
                )

        except Exception as exc:
            print(
                "MARKET ALERT WORKER ERROR:",
                alert.id,
                alert.symbol,
                repr(exc),
            )