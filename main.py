import os

from dotenv import load_dotenv
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.services.user_service import (
    get_or_create_user,
    save_phone_number,
)


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    telegram_user = update.effective_user

    user, created = get_or_create_user(
        telegram_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
    )

    # اگر کاربر هنوز شماره تلفن ثبت نکرده
    if not user.phone_number:
        contact_button = KeyboardButton(
            text="📱 ارسال شماره تلفن",
            request_contact=True,
        )

        keyboard = ReplyKeyboardMarkup(
            [[contact_button]],
            resize_keyboard=True,
            one_time_keyboard=True,
        )

        if created:
            message = (
                f"سلام {telegram_user.first_name} 👋\n\n"
                "به Alift Trader خوش آمدید 🚀\n\n"
                "حساب اولیه شما با موفقیت ایجاد شد ✅\n\n"
                "برای تکمیل ثبت‌نام، لطفاً شماره تلفن متعلق "
                "به حساب تلگرام خود را از طریق دکمه زیر ارسال کنید."
            )
        else:
            message = (
                f"سلام {telegram_user.first_name} 👋\n\n"
                "ثبت‌نام شما هنوز کامل نشده است.\n"
                "لطفاً شماره تلفن خود را از طریق دکمه زیر ارسال کنید."
            )

        await update.message.reply_text(
            message,
            reply_markup=keyboard,
        )

        return

    # کاربری که قبلاً ثبت‌نام کرده
    await update.message.reply_text(
        f"سلام {telegram_user.first_name} 👋\n\n"
        "خوش برگشتی به Alift Trader ✅",
        reply_markup=ReplyKeyboardRemove(),
    )


async def receive_contact(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    contact = update.message.contact
    telegram_user = update.effective_user

    if not contact:
        await update.message.reply_text(
            "❌ شماره تلفن دریافت نشد."
        )
        return

    # جلوگیری از ثبت شماره شخص دیگر
    if contact.user_id != telegram_user.id:
        await update.message.reply_text(
            "❌ لطفاً فقط شماره متعلق به حساب تلگرام "
            "خودتان را ارسال کنید."
        )
        return

    saved = save_phone_number(
        telegram_id=telegram_user.id,
        phone_number=contact.phone_number,
    )

    if not saved:
        await update.message.reply_text(
            "❌ حساب کاربری پیدا نشد.\n"
            "لطفاً ابتدا /start را بزنید."
        )
        return

    await update.message.reply_text(
        "✅ ثبت‌نام با موفقیت تکمیل شد.\n\n"
        "📱 شماره تلفن شما ثبت شد.\n"
        "👤 سطح حساب: Normal\n\n"
        "به Alift Trader خوش آمدید 🚀",
        reply_markup=ReplyKeyboardRemove(),
    )


def main():
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN not found in .env")
        return

    print("Starting Alift Trader Bot...")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.CONTACT,
            receive_contact,
        )
    )

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()