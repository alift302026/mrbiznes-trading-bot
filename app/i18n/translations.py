LANGUAGES = {
    "fa": "🇮🇷 فارسی",
    "en": "🇬🇧 English",
    "ar": "🇸🇦 العربية",
    "tr": "🇹🇷 Türkçe",
    "hi": "🇮🇳 हिन्दी",
    "zh": "🇨🇳 中文",
    "ja": "🇯🇵 日本語",
    "ms": "🇲🇾 Bahasa Melayu",
    "id": "🇮🇩 Bahasa Indonesia",
    "ng": "🇳🇬 English (Nigeria)",
}


TEXTS = {
    "fa": {
        "welcome": "به ALIFT TRADER خوش آمدید",
        "choose": "بخش موردنظر را انتخاب کنید:",
        "markets": "📊 بازارها",
        "signals": "📡 سیگنال‌ها",
        "alerts": "🔔 آلارم‌ها",
        "watchlist": "👁 واچ‌لیست",
        "sessions": "🌍 سشن‌ها",
        "news": "📰 اخبار",
        "psychology": "🧠 روانشناسی",
        "analysis": "🤖 تحلیل من",
        "trader_bot": "🤖 ربات تریدر",
        "exchange": "🔗 اتصال صرافی",
        "vip": "💎 VIP و پرداخت",
        "rewards": "🎁 رفرال و امتیاز",
        "education": "🎓 آموزش",
        "our_exchanges": "🏦 صرافی‌های ما",
        "about": "🤝 درباره ما",
        "account": "👤 حساب من",
        "language": "🌐 زبان",
        "support": "🎧 پشتیبانی",
        "admin": "🛡 مدیریت",
        "performance": "📈 عملکرد ماهانه",
    },

    "en": {
        "welcome": "Welcome to ALIFT TRADER",
        "choose": "Choose a section:",
        "markets": "📊 Markets",
        "signals": "📡 Signals",
        "alerts": "🔔 Alerts",
        "watchlist": "👁 Watchlist",
        "sessions": "🌍 Sessions",
        "news": "📰 News",
        "psychology": "🧠 Psychology",
        "analysis": "🤖 My Analysis",
        "trader_bot": "🤖 Trader Bot",
        "exchange": "🔗 Exchange Connection",
        "vip": "💎 VIP & Payment",
        "rewards": "🎁 Referral & Points",
        "education": "🎓 Education",
        "our_exchanges": "🏦 Our Exchanges",
        "about": "🤝 About Us",
        "account": "👤 My Account",
        "language": "🌐 Language",
        "support": "🎧 Support",
        "admin": "🛡 Admin",
        "performance": "📈 Monthly Performance",
    },
}


def t(lang, key):

    lang = (
        lang
        if lang in TEXTS
        else "en"
    )

    return (
        TEXTS.get(lang, {})
        .get(
            key,
            TEXTS["en"].get(
                key,
                key,
            ),
        )
    )