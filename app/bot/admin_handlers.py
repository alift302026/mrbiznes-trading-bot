import logging
import re
from typing import Optional

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    ContextTypes,
)

from app.core.config import (
    ADMIN_IDS,
)

from app.services.admin_service import (
    audit,
    audit_history,
    broadcast_targets,
    change_points,
    dashboard_stats,
    find_user,
    get_admin_user,
    give_vip,
    recent_users,
    remove_vip,
    set_ban,
    user_stats,
)

from app.services.support_service import (
    admin_reply,
    close_ticket,
    get_ticket,
    open_tickets,
    ticket_messages,
)

logger = logging.getLogger(
    __name__
)

MENU_BUTTON_TEXTS = {
    "📊 بازارها",
    "📡 سیگنال‌ها",
    "🔔 آلارم‌ها",
    "🧠 PLT تحلیل چارت",
    "🌍 سشن‌های بازار",
    "📓 ژورنال معاملاتی",
    "🧠 روانشناسی ترید",
    "💎 VIP و پرداخت",
    "🎁 رفرال و امتیاز",
    "📈 عملکرد ماهانه",
    "🏦 صرافی‌های ما",
    "🎧 پشتیبانی",
    "🤝 درباره ما",
    "👤 حساب من",
    "🛡 مدیریت",
}


def to_english_digits(text: str) -> str:
    if not text:
        return ""
    trans = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    return str(text).translate(trans)


def extract_int(text: str) -> Optional[int]:
    clean = to_english_digits(str(text)).strip()
    match = re.search(r"[-+]?\d+", clean)
    if match:
        try:
            return int(match.group(0))
        except ValueError:
            return None
    return None


def parse_vip_days(text: str) -> Optional[int]:
    if not text:
        return None
    raw = to_english_digits(str(text)).strip().lower()

    if "یک سال" in text or "1 سال" in raw or "یکسال" in text or "1year" in raw or "1 year" in raw:
        return 365
    if "شش ماه" in text or "6 ماه" in raw or "6ماه" in text or "نیم سال" in text or "6 month" in raw:
        return 180
    if "سه ماه" in text or "3 ماه" in raw or "3ماه" in text or "3 month" in raw:
        return 90
    if "دو ماه" in text or "2 ماه" in raw or "2ماه" in text or "2 month" in raw:
        return 60
    if "یک ماه" in text or "1 ماه" in raw or "1ماه" in text or "یکماه" in text or "1 month" in raw:
        return 30
    if "یک هفته" in text or "1 هفته" in raw or "1هفته" in text or "1 week" in raw:
        return 7

    match = re.search(r"\d+", raw)
    if match:
        try:
            val = int(match.group(0))
            if 1 <= val <= 3650:
                return val
        except ValueError:
            pass
    return None


def vip_duration_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("💎 ۳۰ روز (۱ ماه)", callback_data=f"admin_vipdays_{telegram_id}_30"),
                InlineKeyboardButton("💎 ۶۰ روز (۲ ماه)", callback_data=f"admin_vipdays_{telegram_id}_60"),
            ],
            [
                InlineKeyboardButton("💎 ۹۰ روز (۳ ماه)", callback_data=f"admin_vipdays_{telegram_id}_90"),
                InlineKeyboardButton("💎 ۱۸۰ روز (۶ ماه)", callback_data=f"admin_vipdays_{telegram_id}_180"),
            ],
            [
                InlineKeyboardButton("💎 ۳۶۵ روز (۱ سال)", callback_data=f"admin_vipdays_{telegram_id}_365"),
            ],
            [
                InlineKeyboardButton("⬅️ بازگشت به کاربر", callback_data=f"admin_user_{telegram_id}"),
            ],
        ]
    )


# ============================================================
# SECURITY
# ============================================================

def is_admin(
    telegram_id,
):

    return (
        telegram_id
        in ADMIN_IDS
    )


async def deny(
    update,
):

    if update.callback_query:

        await update.callback_query.answer(
            "⛔ Access denied",
            show_alert=True,
        )

    elif update.message:

        await update.message.reply_text(
            "⛔ Access denied"
        )


# ============================================================
# HOME
# ============================================================

def admin_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📊 Dashboard",
                    callback_data="admin_dashboard",
                ),
                InlineKeyboardButton(
                    "👥 Users",
                    callback_data="admin_users",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔎 Search User",
                    callback_data="admin_search",
                ),
                InlineKeyboardButton(
                    "🎫 Support",
                    callback_data="admin_tickets",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📢 Broadcast",
                    callback_data="admin_broadcast",
                ),
                InlineKeyboardButton(
                    "📜 Audit Log",
                    callback_data="admin_audit",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔄 Refresh",
                    callback_data="admin_home",
                )
            ],
        ]
    )


def admin_home_text():

    return (
        "🛡 MrBiznes ADMIN CENTER\n"
        "━━━━━━━━━━━━━━━━\n\n"

        "مرکز مدیریت MrBiznes\n\n"

        "📊 آمار سیستم\n"
        "👥 مدیریت کاربران\n"
        "💎 مدیریت VIP\n"
        "⛔ Ban / Unban\n"
        "⭐ مدیریت امتیاز\n"
        "🎫 تیکت‌های پشتیبانی\n"
        "📢 Broadcast\n"
        "📜 Audit Log"
    )


async def admin_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    admin_id = (
        update.effective_user.id
    )

    if not is_admin(
        admin_id
    ):

        await deny(
            update
        )

        return

    clear_admin_input(
        context
    )

    await update.message.reply_text(
        admin_home_text(),
        reply_markup=(
            admin_keyboard()
        ),
    )


# ============================================================
# DASHBOARD
# ============================================================

def dashboard_text():

    stats = dashboard_stats()

    return (
        "📊 MrBiznes DASHBOARD\n"
        "━━━━━━━━━━━━━━━━\n\n"

        f"👥 Users: {stats['users']}\n"
        f"✅ Active Users: {stats['active_users']}\n"
        f"⛔ Banned: {stats['banned']}\n"
        f"💎 VIP: {stats['vip']}\n\n"

        f"🔔 Alerts: {stats['alerts']}\n"
        f"🟢 Active Alerts: {stats['active_alerts']}\n\n"

        f"🎁 Referrals: {stats['referrals']}\n"
        f"🔎 Crypto Searches: {stats['searches']}\n"
        f"🎫 Open Tickets: {stats['open_tickets']}"
    )


# ============================================================
# USER
# ============================================================

def user_text(
    user,
):

    stats = user_stats(
        user.telegram_id
    )

    username = (
        f"@{user.username}"
        if user.username
        else "-"
    )

    vip_expire = "-"

    if user.vip_expires_at:

        vip_expire = (
            user.vip_expires_at.strftime(
                "%Y/%m/%d %H:%M"
            )
        )

    return (
        "👤 USER CONTROL\n"
        "━━━━━━━━━━━━━━━━\n\n"

        f"🆔 {user.telegram_id}\n"
        f"👤 {user.first_name or '-'}\n"
        f"🔗 {username}\n\n"

        f"💎 Plan: {user.membership_type.upper()}\n"
        f"📅 VIP Expire: {vip_expire}\n"
        f"⭐ Points: {user.points}\n\n"

        f"🔔 Alerts: {stats['alerts']}\n"
        f"🟢 Active Alerts: {stats['active_alerts']}\n"
        f"🎁 Referrals: {stats['referrals']}\n"
        f"🔎 Searches: {stats['searches']}\n"
        f"🎫 Tickets: {stats['tickets']}\n\n"

        f"⛔ Banned: {'YES' if user.is_banned else 'NO'}"
    )


def user_keyboard(
    user,
):

    telegram_id = (
        user.telegram_id
    )

    ban_text = (
        "✅ Unban"
        if user.is_banned
        else "⛔ Ban"
    )

    ban_action = (
        "unban"
        if user.is_banned
        else "ban"
    )

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💎 VIP +30d",
                    callback_data=(
                        f"admin_vip30_{telegram_id}"
                    ),
                ),
                InlineKeyboardButton(
                    "💎 VIP Custom",
                    callback_data=(
                        f"admin_vipcustom_{telegram_id}"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "❌ Remove VIP",
                    callback_data=(
                        f"admin_vipremove_{telegram_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    ban_text,
                    callback_data=(
                        f"admin_{ban_action}_{telegram_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "⭐ Change Points",
                    callback_data=(
                        f"admin_points_{telegram_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "🔄 Refresh User",
                    callback_data=(
                        f"admin_user_{telegram_id}"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Users",
                    callback_data="admin_users",
                )
            ],
        ]
    )


# ============================================================
# USERS LIST
# ============================================================

def users_keyboard(
    users,
):

    rows = []

    for user in users:

        plan = (
            "💎"
            if user.membership_type
            == "vip"
            else "👤"
        )

        banned = (
            "⛔"
            if user.is_banned
            else ""
        )

        username = (
            f"@{user.username}"
            if user.username
            else str(
                user.telegram_id
            )
        )

        rows.append(
            [
                InlineKeyboardButton(
                    (
                        f"{plan}{banned} "
                        f"{username}"
                    ),
                    callback_data=(
                        f"admin_user_{user.telegram_id}"
                    ),
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "🔎 Search User",
                callback_data="admin_search",
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                "⬅️ Admin",
                callback_data="admin_home",
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


# ============================================================
# SUPPORT
# ============================================================

def admin_ticket_keyboard(
    tickets,
):

    rows = []

    for ticket in tickets:

        icon = (
            "🟢"
            if ticket.status
            == "answered"
            else "🟡"
        )

        rows.append(
            [
                InlineKeyboardButton(
                    (
                        f"{icon} #{ticket.id} "
                        f"| {ticket.telegram_id}"
                    ),
                    callback_data=(
                        f"admin_ticket_{ticket.id}"
                    ),
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "⬅️ Admin",
                callback_data="admin_home",
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


def admin_ticket_text(
    ticket,
):

    messages = ticket_messages(
        ticket.id
    )

    lines = [
        f"🎫 TICKET #{ticket.id}",
        "━━━━━━━━━━━━━━━━",
        "",
        f"User: {ticket.telegram_id}",
        f"Category: {ticket.category}",
        f"Status: {ticket.status}",
        "",
    ]

    for message in messages[-15:]:

        sender = (
            "🛡 Admin"
            if message.sender_type
            == "admin"
            else "👤 User"
        )

        text = (
            message.message
            or ""
        )

        if len(text) > 800:

            text = (
                text[:800]
                + "..."
            )

        lines.append(
            f"{sender}:\n{text}\n"
        )

    return "\n".join(
        lines
    )


# ============================================================
# CALLBACK
# ============================================================

async def admin_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:
        return

    admin_id = (
        query.from_user.id
    )

    if not is_admin(
        admin_id
    ):

        await deny(
            update
        )

        return

    await query.answer()

    data = (
        query.data
        or ""
    )

    # HOME

    if data == "admin_home":

        clear_admin_input(
            context
        )

        await query.edit_message_text(
            admin_home_text(),
            reply_markup=(
                admin_keyboard()
            ),
        )

        return

    # DASHBOARD

    if data == "admin_dashboard":

        await query.edit_message_text(
            dashboard_text(),
            reply_markup=(
                admin_keyboard()
            ),
        )

        return

    # USERS

    if data == "admin_users":

        users = recent_users(
            20
        )

        await query.edit_message_text(
            (
                "👥 RECENT USERS\n"
                "━━━━━━━━━━━━━━━━\n\n"
                "آخرین 20 کاربر:"
            ),
            reply_markup=(
                users_keyboard(
                    users
                )
            ),
        )

        return

    # SEARCH USER

    if data == "admin_search":

        context.user_data[
            "admin_input"
        ] = {
            "mode":
                "search_user",
        }

        await query.edit_message_text(
            (
                "🔎 SEARCH USER\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "Telegram ID یا Username را بفرست.\n\n"

                "مثال:\n"
                "1432178804\n"
                "یا\n"
                "@username"
            )
        )

        return

    # USER

    if data.startswith(
        "admin_user_"
    ):

        try:

            telegram_id = int(
                data.replace(
                    "admin_user_",
                    "",
                    1,
                )
            )

        except ValueError:
            return

        user = get_admin_user(
            telegram_id
        )

        if user is None:

            await query.answer(
                "User not found",
                show_alert=True,
            )

            return

        await query.edit_message_text(
            user_text(
                user
            ),
            reply_markup=(
                user_keyboard(
                    user
                )
            ),
        )

        return

    # VIP 30 DAYS

    if data.startswith(
        "admin_vip30_"
    ):

        telegram_id = int(
            data.replace(
                "admin_vip30_",
                "",
                1,
            )
        )

        success = give_vip(
            admin_id,
            telegram_id,
            30,
        )

        user = get_admin_user(
            telegram_id
        )

        if not success or user is None:

            await query.answer(
                "VIP update failed",
                show_alert=True,
            )

            return

        try:
            await context.bot.send_message(
                chat_id=telegram_id,
                text=(
                    "💎 اشتراک VIP مستر بیزنس فعال شد!\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "✅ دسترسی حساب شما به مدت ۳۰ روز به سطح VIP ارتقا یافت.\n"
                    "از همراهی شما با مستر بیزنس سپاسگزاریم 🚀"
                ),
            )
        except Exception:
            pass

        await query.answer("✅ ۳۰ روز VIP با موفقیت فعال شد.", show_alert=True)
        await query.edit_message_text(
            user_text(user),
            reply_markup=(
                user_keyboard(user)
            ),
        )

        return

    # VIP PRESET DAYS (e.g. admin_vipdays_123456_90)
    if data.startswith("admin_vipdays_"):
        parts = data.replace("admin_vipdays_", "").split("_")
        if len(parts) == 2:
            try:
                target_id = int(parts[0])
                days = int(parts[1])
            except ValueError:
                return

            context.user_data.pop("admin_input", None)
            success = give_vip(admin_id, target_id, days)
            user = get_admin_user(target_id)
            if not success or user is None:
                await query.answer("خطا در اعمال VIP", show_alert=True)
                return

            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=(
                        "💎 اشتراک VIP مستر بیزنس فعال شد!\n"
                        "━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"✅ دسترسی حساب شما به مدت {days} روز به سطح VIP ارتقا یافت.\n"
                        "از همراهی شما با مستر بیزنس سپاسگزاریم 🚀"
                    ),
                )
            except Exception:
                pass

            await query.answer(f"✅ {days} روز VIP با موفقیت فعال شد.", show_alert=True)
            await query.edit_message_text(
                user_text(user),
                reply_markup=user_keyboard(user),
            )
            return

    # CUSTOM VIP

    if data.startswith(
        "admin_vipcustom_"
    ):

        telegram_id = int(
            data.replace(
                "admin_vipcustom_",
                "",
                1,
            )
        )

        context.user_data[
            "admin_input"
        ] = {
            "mode":
                "vip_days",

            "telegram_id":
                telegram_id,
        }

        await query.edit_message_text(
            (
                "💎 تعیین مدت اشتراک VIP\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👤 کاربر: {telegram_id}\n\n"
                "یکی از بازه‌های آماده زیر را انتخاب کنید یا تعداد روز دلخواه را تایپ کنید (مثلاً ۹۰ یا ۱ سال):"
            ),
            reply_markup=vip_duration_keyboard(telegram_id),
        )

        return

    # REMOVE VIP

    if data.startswith(
        "admin_vipremove_"
    ):

        telegram_id = int(
            data.replace(
                "admin_vipremove_",
                "",
                1,
            )
        )

        remove_vip(
            admin_id,
            telegram_id,
        )

        user = get_admin_user(
            telegram_id
        )

        if user:

            await query.edit_message_text(
                user_text(user),
                reply_markup=(
                    user_keyboard(
                        user
                    )
                ),
            )

        return

    # BAN

    if data.startswith(
        "admin_ban_"
    ):

        telegram_id = int(
            data.replace(
                "admin_ban_",
                "",
                1,
            )
        )

        if telegram_id == admin_id:

            await query.answer(
                "نمی‌توانی حساب Admin خودت را Ban کنی.",
                show_alert=True,
            )

            return

        set_ban(
            admin_id,
            telegram_id,
            True,
        )

        user = get_admin_user(
            telegram_id
        )

        if user:

            await query.edit_message_text(
                user_text(user),
                reply_markup=(
                    user_keyboard(
                        user
                    )
                ),
            )

        return

    # UNBAN

    if data.startswith(
        "admin_unban_"
    ):

        telegram_id = int(
            data.replace(
                "admin_unban_",
                "",
                1,
            )
        )

        set_ban(
            admin_id,
            telegram_id,
            False,
        )

        user = get_admin_user(
            telegram_id
        )

        if user:

            await query.edit_message_text(
                user_text(user),
                reply_markup=(
                    user_keyboard(
                        user
                    )
                ),
            )

        return

    # POINTS

    if data.startswith(
        "admin_points_"
    ):

        telegram_id = int(
            data.replace(
                "admin_points_",
                "",
                1,
            )
        )

        context.user_data[
            "admin_input"
        ] = {
            "mode":
                "points",

            "telegram_id":
                telegram_id,
        }

        await query.edit_message_text(
            (
                "⭐ CHANGE POINTS\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"User: {telegram_id}\n\n"

                "عدد را ارسال کن.\n\n"
                "افزایش:\n"
                "100\n\n"
                "کاهش:\n"
                "-50"
            )
        )

        return

    # SUPPORT TICKETS

    if data == "admin_tickets":

        tickets = open_tickets(
            50
        )

        await query.edit_message_text(
            (
                "🎫 SUPPORT TICKETS\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"Open: {len(tickets)}"
            ),
            reply_markup=(
                admin_ticket_keyboard(
                    tickets
                )
            ),
        )

        return

    # VIEW TICKET

    if data.startswith(
        "admin_ticket_"
    ):

        ticket_id = int(
            data.replace(
                "admin_ticket_",
                "",
                1,
            )
        )

        ticket = get_ticket(
            ticket_id
        )

        if ticket is None:
            return

        await query.edit_message_text(
            admin_ticket_text(
                ticket
            ),
            reply_markup=(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "✍️ Reply",
                                callback_data=(
                                    f"admin_ticketreply_{ticket.id}"
                                ),
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "✅ Close",
                                callback_data=(
                                    f"admin_ticketclose_{ticket.id}"
                                ),
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "⬅️ Tickets",
                                callback_data="admin_tickets",
                            )
                        ],
                    ]
                )
            ),
        )

        return

    # TICKET REPLY

    if data.startswith(
        "admin_ticketreply_"
    ):

        ticket_id = int(
            data.replace(
                "admin_ticketreply_",
                "",
                1,
            )
        )

        context.user_data[
            "admin_input"
        ] = {
            "mode":
                "ticket_reply",

            "ticket_id":
                ticket_id,
        }

        await query.edit_message_text(
            (
                f"✍️ REPLY TICKET #{ticket_id}\n\n"
                "پاسخ را ارسال کن."
            )
        )

        return

    # CLOSE TICKET

    if data.startswith(
        "admin_ticketclose_"
    ):

        ticket_id = int(
            data.replace(
                "admin_ticketclose_",
                "",
                1,
            )
        )

        close_ticket(
            ticket_id
        )

        audit(
            admin_id,
            "close_ticket",
            "ticket",
            ticket_id,
        )

        await query.edit_message_text(
            (
                f"✅ Ticket #{ticket_id} closed."
            ),
            reply_markup=(
                admin_keyboard()
            ),
        )

        return

    # BROADCAST

    if data == "admin_broadcast":

        context.user_data[
            "admin_input"
        ] = {
            "mode":
                "broadcast",
        }

        await query.edit_message_text(
            (
                "📢 BROADCAST\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "پیام موردنظر را ارسال کن.\n\n"

                "⚠️ پیام برای تمام کاربران فعال "
                "و غیر Ban ارسال می‌شود."
            )
        )

        return

    # AUDIT

    if data == "admin_audit":

        items = audit_history(
            25
        )

        lines = [
            "📜 ADMIN AUDIT LOG",
            "━━━━━━━━━━━━━━━━",
            "",
        ]

        if not items:

            lines.append(
                "No audit records."
            )

        for item in items:

            lines.append(
                (
                    f"#{item.id} | "
                    f"{item.action} | "
                    f"{item.target_id or '-'}"
                )
            )

        await query.edit_message_text(
            "\n".join(
                lines
            ),
            reply_markup=(
                admin_keyboard()
            ),
        )


# ============================================================
# ADMIN TEXT INPUT
# ============================================================

async def admin_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if (
        update.message is None
        or update.effective_user
        is None
    ):
        return False

    admin_id = (
        update.effective_user.id
    )

    if not is_admin(
        admin_id
    ):
        return False

    pending = (
        context.user_data.get(
            "admin_input"
        )
    )

    if not pending:
        return False

    text = (
        update.message.text
        or ""
    ).strip()

    # Check if admin pressed a main menu button or command or cancel
    if text in MENU_BUTTON_TEXTS or text.startswith("/") or text in {"انصراف", "لغو", "بازگشت", "cancel"}:
        context.user_data.pop("admin_input", None)
        if text in {"انصراف", "لغو", "بازگشت", "cancel"}:
            await update.message.reply_text("عملیات مدیریت لغو شد.", reply_markup=admin_keyboard())
            return True
        return False

    mode = pending[
        "mode"
    ]

    # SEARCH USER

    if mode == "search_user":

        user = find_user(
            text
        )

        context.user_data.pop(
            "admin_input",
            None,
        )

        if user is None:

            await update.message.reply_text(
                "❌ کاربر موردنظر یافت نشد.\n\n"
                "می‌توانید شناسه عددی (Telegram ID) یا یوزرنیم کاربر را ارسال کنید.",
                reply_markup=(
                    admin_keyboard()
                ),
            )

            return True

        await update.message.reply_text(
            user_text(
                user
            ),
            reply_markup=(
                user_keyboard(
                    user
                )
            ),
        )

        return True

    # VIP DAYS

    if mode == "vip_days":

        days = parse_vip_days(text)

        if days is None or days <= 0 or days > 3650:

            await update.message.reply_text(
                "❌ لطفاً تعداد روز را به صورت عدد معتبر ارسال کنید (مثلاً ۳۰ یا ۹۰ یا ۱ سال).\n"
                "برای انصراف کلمه «لغو» را ارسال کنید."
            )

            return True

        telegram_id = pending[
            "telegram_id"
        ]

        success = give_vip(
            admin_id,
            telegram_id,
            days,
        )

        context.user_data.pop(
            "admin_input",
            None,
        )

        user = get_admin_user(
            telegram_id
        )

        if (
            not success
            or user is None
        ):

            await update.message.reply_text(
                "❌ خطا در اعمال اشتراک VIP.",
                reply_markup=(
                    admin_keyboard()
                ),
            )

            return True

        try:
            await context.bot.send_message(
                chat_id=telegram_id,
                text=(
                    "💎 اشتراک VIP مستر بیزنس فعال شد!\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"✅ دسترسی حساب شما به مدت {days} روز به سطح VIP ارتقا یافت.\n"
                    "از همراهی شما با مستر بیزنس سپاسگزاریم 🚀"
                ),
            )
        except Exception:
            pass

        await update.message.reply_text(
            f"✅ اشتراک VIP به مدت {days} روز با موفقیت ثبت شد.",
            reply_markup=(
                user_keyboard(
                    user
                )
            ),
        )

        return True

    # POINTS

    if mode == "points":

        amount = extract_int(text)

        if amount is None:

            await update.message.reply_text(
                "❌ لطفاً مقدار امتیاز را به صورت عدد معتبر ارسال کنید (مثلاً ۵۰ یا -20).\n"
                "برای انصراف کلمه «لغو» را ارسال کنید."
            )

            return True

        telegram_id = pending[
            "telegram_id"
        ]

        success = change_points(
            admin_id,
            telegram_id,
            amount,
        )

        context.user_data.pop(
            "admin_input",
            None,
        )

        if not success:

            await update.message.reply_text(
                "❌ تغییر امتیاز انجام نشد.",
                reply_markup=(
                    admin_keyboard()
                ),
            )

            return True

        user = get_admin_user(
            telegram_id
        )

        await update.message.reply_text(
            (
                f"✅ امتیاز به‌روزرسانی شد.\n"
                f"موجودی جدید: {user.points}"
            ),
            reply_markup=(
                user_keyboard(
                    user
                )
            ),
        )

        return True

    # TICKET REPLY

    if mode == "ticket_reply":

        ticket_id = pending[
            "ticket_id"
        ]

        success = admin_reply(
            ticket_id,
            admin_id,
            text,
        )

        context.user_data.pop(
            "admin_input",
            None,
        )

        if not success:

            await update.message.reply_text(
                "❌ Reply failed.",
                reply_markup=(
                    admin_keyboard()
                ),
            )

            return True

        ticket = get_ticket(
            ticket_id
        )

        if ticket:

            try:

                await context.bot.send_message(
                    chat_id=(
                        ticket.telegram_id
                    ),
                    text=(
                        "🎧 MrBiznes SUPPORT\n"
                        "━━━━━━━━━━━━━━━━\n\n"
                        f"پاسخ جدید برای Ticket #{ticket_id}\n\n"
                        f"{text}"
                    ),
                )

            except Exception:
                pass

        audit(
            admin_id,
            "reply_ticket",
            "ticket",
            ticket_id,
        )

        await update.message.reply_text(
            "✅ Reply sent.",
            reply_markup=(
                admin_keyboard()
            ),
        )

        return True

    # BROADCAST

    if mode == "broadcast":

        if (
            len(text) < 1
            or len(text) > 4000
        ):

            await update.message.reply_text(
                "❌ پیام معتبر نیست."
            )

            return True

        context.user_data.pop(
            "admin_input",
            None,
        )

        targets = (
            broadcast_targets()
        )

        sent = 0
        failed = 0

        status = (
            await update.message.reply_text(
                (
                    "📢 Broadcast started...\n"
                    f"Targets: {len(targets)}"
                )
            )
        )

        for telegram_id in targets:

            try:

                await context.bot.send_message(
                    chat_id=telegram_id,
                    text=text,
                )

                sent += 1

            except Exception:

                failed += 1

        audit(
            admin_id,
            "broadcast",
            "system",
            None,
            (
                f"sent={sent}, "
                f"failed={failed}"
            ),
        )

        await status.edit_text(
            (
                "✅ BROADCAST COMPLETE\n"
                "━━━━━━━━━━━━━━━━\n\n"
                f"📤 Sent: {sent}\n"
                f"❌ Failed: {failed}"
            )
        )

        await update.message.reply_text(
            admin_home_text(),
            reply_markup=(
                admin_keyboard()
            ),
        )

        return True

    return False


# ============================================================
# DIRECT ADMIN COMMANDS
# ============================================================

async def admin_givevip_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    if user is None or not is_admin(user.id):
        return

    args = context.args or []
    if not args:
        await update.message.reply_text(
            "📌 راهنمای دستور اعطای VIP:\n"
            "`/givevip <ID_or_@username> [days]`\n\n"
            "مثال:\n"
            "`/givevip 123456789 30`\n"
            "`/givevip @username 60`\n"
            "`/givevip 123456789 1 سال`",
            parse_mode="Markdown",
        )
        return

    target = args[0].strip()
    days = 30
    if len(args) > 1:
        parsed_days = parse_vip_days(" ".join(args[1:]))
        if parsed_days:
            days = parsed_days

    found = find_user(target)
    target_id = None
    if found:
        target_id = found.telegram_id
    elif to_english_digits(target).isdigit():
        target_id = int(to_english_digits(target))

    if not target_id:
        await update.message.reply_text("❌ کاربر موردنظر یافت نشد.")
        return

    success = give_vip(user.id, target_id, days)
    if not success:
        await update.message.reply_text("❌ خطا در اعمال اشتراک VIP.")
        return

    updated = get_admin_user(target_id)
    # Try notifying user
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=(
                "💎 اشتراک VIP مستر بیزنس فعال شد!\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✅ دسترسی حساب شما با موفقیت به سطح VIP ارتقا یافت.\n"
                f"📅 مهلت اعتبار: {days} روز\n\n"
                "از همراهی شما با مستر بیزنس سپاسگزاریم 🚀"
            ),
        )
    except Exception:
        pass

    await update.message.reply_text(
        f"✅ اشتراک VIP برای کاربر {target_id} به مدت {days} روز با موفقیت فعال شد.",
        reply_markup=user_keyboard(updated) if updated else admin_keyboard(),
    )


async def admin_removevip_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user
    if user is None or not is_admin(user.id):
        return

    args = context.args or []
    if not args:
        await update.message.reply_text(
            "📌 راهنمای دستور حذف VIP:\n"
            "`/removevip <ID_or_@username>`",
            parse_mode="Markdown",
        )
        return

    target = args[0].strip()
    found = find_user(target)
    target_id = None
    if found:
        target_id = found.telegram_id
    elif to_english_digits(target).isdigit():
        target_id = int(to_english_digits(target))

    if not target_id:
        await update.message.reply_text("❌ کاربر موردنظر یافت نشد.")
        return

    remove_vip(user.id, target_id)
    updated = get_admin_user(target_id)
    await update.message.reply_text(
        f"✅ اشتراک VIP کاربر {target_id} غیرفعال شد.",
        reply_markup=user_keyboard(updated) if updated else admin_keyboard(),
    )


# ============================================================
# CLEAR
# ============================================================

def clear_admin_input(
    context,
):

    context.user_data.pop(
        "admin_input",
        None,
    )