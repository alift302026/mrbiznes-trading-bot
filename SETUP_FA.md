# 🚀 راهنمای کامل روشن کردن ربات MrBiznes

این راهنما برای این نوشته شده که ربات را از صفر روشن کنید و بفهمید
ایراد از کجاست. سه حالت داریم:

| حالت | سرور | پروکسی لازم است؟ | توصیه |
|---|---|---|---|
| **۰** | **GitHub Actions** (هیچ سروری لازم نیست) | ❌ نه | ✅ سریع‌ترین راه برای تست و حتی ۲۴ ساعته |
| **الف** | Railway (خارج ایران) | ❌ نه | ✅ گزینه‌ی حرفه‌ای ۲۴ ساعته |
| **ب** | VPS / سرور داخل ایران (ISP) | ✅ بله (SOCKS5/HTTP) | فقط اگر سرور داخل ایران باشد |
| **ج** | کامپیوتر خودتان (تست) | ✅ بله اگر اینترنت ایران است | برای تست سریع |

---

## ۰) چک کردن سریع ربات (قبل از هر کاری)

داخل پوشه پروژه این را اجرا کنید:

```bash
python scripts/doctor.py
```

خروجی می‌گوید: توکن هست یا نه، پکیج‌ها نصب‌اند یا نه، اینترنت سرور به
تلگرام می‌رسد یا نه، پروکسی کار می‌کند یا نه، و **شناسه تلگرام
کاربران ثبت‌شده** را هم نشان می‌دهد.

بعد از روشن شدن ربات، از داخل تلگرام هم می‌توانید چک کنید:

| دستور | کار |
|---|---|
| `/id` | شناسه عددی تلگرام خودتان (برای `ADMIN_IDS`) |
| `/ping` | سرعت پاسخ‌دهی ربات |
| `/diag` | گزارش کامل سلامت — **فقط ادمین** |

---

## ۰) بدون هیچ سروری: اجرای ربات روی GitHub Actions ⭐ (سریع‌ترین راه)

سرورهای گیت‌هاب بیرون ایران هستند؛ هم به تلگرام دسترسی دارند و هم
لازم نیست هیچ VPS یا پلتفرمی بخرید. مخزن شما **public** است، پس
دقایق اجرا **رایگان و نامحدود** است.

**۲ کار دستی لازم است (حدود ۲ دقیقه):**

### کار ۱ — ساخت توکن ربات (اگر ندارید)
در تلگرام به [@BotFather](https://t.me/BotFather) پیام دهید:
`/newbot` → اسم و یوزرنیم بدهید → توکن شبیه
`123456789:AAH...` می‌گیرید.

### کار ۲ — گذاشتن توکن در Secrets
1. برو به:
   `https://github.com/alift302026/mrbiznes-trading-bot/settings/secrets/actions`
2. **New repository secret**
3. Name: `BOT_TOKEN`  ← دقیقا همین
4. Secret: توکن BotFather
5. **Add secret**

### کار ۳ — اضافه کردن فایل اجرا
1. برو به:
   `https://github.com/alift302026/mrbiznes-trading-bot/new/main/.github/workflows`
2. File name: `telegram-bot.yml`
3. محتوای فایل [`deploy/github-actions-telegram-bot.yml`](deploy/github-actions-telegram-bot.yml)
   را از خط `name:` به بعد کپی کنید و بچسبانید.
4. **Commit changes**

### کار ۴ — روشن کردن
1. برو به تب **Actions** → **Telegram Bot (no server)**
2. **Run workflow** → **Run workflow**
3. حدود ۱ دقیقه صبر کنید؛ در لاگ باید ببینید:
   `BOT RUNNING`
4. در تلگرام به ربات خودتان `/start` بدهید → `/id` → `/ping` → `/diag`

از این به بعد ربات **خودکار هر ۶ ساعت** روشن می‌شود و هر بار ~۵ ساعت
و ۴۸ دقیقه زنده می‌ماند (سقف یک Job در گیت‌هاب ۶ ساعت است). بین دو
اجرا چند دقیقه فاصله می‌افتد، ولی پیام‌های ارسالی گم نمی‌شوند و با
اجرای بعدی پردازش می‌شوند (`BOT_DROP_PENDING_UPDATES=0`).

### نکته‌های مهم این روش
- مخزن public است؛ **توکن را هیچ‌وقت داخل فایل یا چت نگذارید** —
  فقط در Secrets.
- اگر خواستید بررسی عضویت کانال را روشن کنید، در فایل
  `REQUIRED_CHANNEL: "off"` را به `"@MrBiznesMarket"` تغییر دهید.
- گیت‌هاب ورک‌فلوی زمان‌بندی‌شده را بعد از ۶۰ روز بی‌فعالیتی مخزن
  خاموش می‌کند؛ یک Commit بزنید تا دوباره فعال شود.
- برای اجرای ۲۴ ساعته‌ی بدون وقفه، حالت «الف» (Railway) یا «ب»
  (سرور) را ببینید.

---

## ۱) گرفتن شناسه تلگرام و تنظیم ادمین

۱. یک‌بار به ربات `/start` بدهید (باید عضو کانال اجباری باشید).
۲. `/id` را بزنید؛ ربات شناسه عددی شما را می‌گوید. مثلا `123456789`.
۳. همان عدد را در `ADMIN_IDS` بگذارید:

```
ADMIN_IDS=123456789
```

چند ادمین: `ADMIN_IDS=123456789,987654321`

۴. ربات را ری‌استارت کنید. با `/diag` باید گزارش سلامت را ببینید.

> اگر `/diag` گفت «فقط برای ادمین»، یعنی عدد را اشتباه گذاشته‌اید یا
> ربات را ری‌استارت نکرده‌اید.

---

## الف) روشن کردن روی Railway (خارج ایران — بدون پروکسی) ⭐

سرورهای Railway بیرون ایران هستند، پس فیلترینگ تلگرام وجود ندارد و
**نیازی به پروکسی نیست**.

### ۱. اتصال مخزن
1. وارد [railway.app](https://railway.app) شوید و با گیت‌هاب لاگین کنید.
2. `New Project` → `Deploy from GitHub repo` →
   `alift302026/mrbiznes-trading-bot`
3. اگر پرسید از کدام برنچ، `main` را انتخاب کنید (بعد از مرج شدن
   تغییرات).

### ۲. متغیرها (Variables)
در سرویس → تب `Variables` این‌ها را اضافه کنید:

| متغیر | مقدار |
|---|---|
| `BOT_TOKEN` | توکن ربات از @BotFather |
| `ADMIN_IDS` | شناسه عددی تلگرام شما |
| `REQUIRED_CHANNEL` | `@MrBiznesMarket` |
| `REQUIRED_CHANNEL_URL` | `https://t.me/MrBiznesMarket` |
| `XT_API_KEY` / `XT_SECRET_KEY` | برای بازار و جستجوی کریپتو |
| `TWELVE_DATA_API_KEY` | برای فارکس |
| `OPENAI_API_KEY` | برای تحلیل چارت PLT |
| `LIVECOINWATCH_API_KEY` | اختیاری |
| `FINAL_SIGNALS_PUSH` | `1` برای ارسال سیگنال‌ها |

نیازی به تنظیم `BOT_PROXY_URL` نیست — خالی بگذارید.

### ۳. دستور اجرا
`Settings` → `Deploy` → **Start Command**:

```
python main.py
```

(اگر خالی بگذارید، Nixpacks خودش `python main.py` را حدس می‌زند، ولی
صریح گذاشتن مطمئن‌تر است.)

روی Railway نیازی به پورت/دامنه نیست؛ ربات با Long Polling کار می‌کند.

### ۴. سرویس دوم برای اسکنر PLT (اختیاری — کرون)
یک سرویس دیگر از همان مخزن بسازید و:

- **Start Command:** `python plt_range_scanner.py`
- **Cron Schedule:** `5 * * * *` (هر ساعت، دقیقه ۵ به وقت UTC)
- **Variables:** `TELEGRAM_BOT_TOKEN`، `PLT_RANGE_CHANNEL_ID` و…

جزئیات بیشتر در `RAILWAY_SETUP.md`.

### ۵. نکته مهم
> ⚠️ **یک ربات را هم‌زمان روی دو جا روشن نکنید** (مثلا Railway و
> کامپیوتر خودتان). تلگرام اجازه نمی‌دهد دو جا هم‌زمان پیام‌ها را
> بگیرند و خطای `Conflict: terminated by other getUpdates` می‌گیرید.
> هر بار فقط یک نسخه روشن باشد.

---

## ب) روشن کردن روی سرور داخل ایران (VPS/ISP) — با پروکسی

اگر سرور داخل ایران است، `api.telegram.org` فیلتر است و ربات بدون
پروکسی بالا نمی‌آید. ترتیب کار:

### ۱. آماده کردن پروکسی
یک پروکسی **SOCKS5** یا **HTTP** روی سرور (یا سرور دیگر) بالا بیاورید.
رایج‌ترین راه: نصب Xray/V2Ray روی سرور خارج و ساختن یک اینباند
SOCKS5 محلی، یا تونل SSH:

```bash
# نمونه تونل SSH: پورت 1080 روی سرور ایران به یک سرور خارج وصل می‌شود
ssh -N -D 0.0.0.0:1080 user@YOUR_FOREIGN_SERVER
```

> ⛔️ **پروکسی MTProto تلگرام برای ربات کار نمی‌کند.**
> MTProto فقط برای خود اپلیکیشن تلگرام است؛ ربات به Socket خام
> HTTPS به `api.telegram.org` نیاز دارد، یعنی SOCKS5 یا HTTP.

### ۲. نصب پروژه
```bash
cd /root
git clone https://github.com/alift302026/mrbiznes-trading-bot.git
cd mrbiznes-trading-bot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
nano .env
```

در `.env` این‌ها را پر کنید:

```
BOT_TOKEN=...
ADMIN_IDS=...
REQUIRED_CHANNEL=@MrBiznesMarket
BOT_PROXY_URL=socks5://127.0.0.1:1080
BOT_DROP_PENDING_UPDATES=1
BOT_CONNECT_TIMEOUT=20
BOT_READ_TIMEOUT=30
```

مقدار `BOT_DROP_PENDING_UPDATES=1` فقط برای بار اول خوب است تا
پیام‌های عقب‌افتاده‌ی زمان خاموشی روی هم نیفتد؛ بعدا می‌توانید `0`
کنید.

### ۳. تست
```bash
.venv/bin/python scripts/doctor.py     # باید همه ✅ باشد
.venv/bin/python main.py               # اجرای ربات
```

باید ببینید:

```
Network           : PROXY socks5://127.0.0.1:1080
BOT RUNNING
```

### ۴. اجرای دائمی با systemd
فایل `/etc/systemd/system/mrbiznes.service`:

```ini
[Unit]
Description=MrBiznes Trading Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/root/mrbiznes-trading-bot
EnvironmentFile=/root/mrbiznes-trading-bot/.env
ExecStart=/root/mrbiznes-trading-bot/.venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/mrbiznes.log
StandardError=append:/var/log/mrbiznes.log

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now mrbiznes
systemctl status mrbiznes
tail -f /var/log/mrbiznes.log
```

⚠️ اگر پروکسی روی همان سرور باشد، سرویس پروکسی هم باید قبل از ربات
بالا بیاید (`After=` و `Restart=always` کمک می‌کند).

### ۵. پروکسی برای بخش‌های دیگر (بازار/اخبار)
پیش‌فرض این است که `BOT_PROXY_URL` **فقط برای تلگرام** استفاده شود؛
چون بعضی پروکسی‌ها فقط اجازه‌ی تلگرام می‌دهند و اگر همه‌چیز را از آن‌ها
رد کنیم، تب‌های بازار/اخبار خراب می‌شوند.

اگر پروکسی‌تان عمومی است (مثلا تونل SSH یا Xray روی سرور خودتان) و
می‌خواهید اخبار/بازار/اسکنر هم از پروکسی رد شوند:

```
BOT_PROXY_FOR_ALL=1
```

---

## ج) اجرای تستی روی کامپیوتر خودتان

```bash
python -m venv .venv
# ویندوز:
.venv\Scripts\activate
# لینوکس/مک:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env      # و مقادیر را پر کنید
python scripts/doctor.py
python main.py
```

اگر اینترنت‌تان ایران است: `BOT_PROXY_URL` را پر کنید. اگر VPN روشن
است، خیلی وقت‌ها همان VPN کل ترافیک را می‌برد و پروکسی لازم نیست.

---

## عیب‌یابی خطاهای رایج

| پیام خطا | معنی | راه‌حل |
|---|---|---|
| `BOT_TOKEN is missing` / «متغیر BOT_TOKEN خالی است» | توکن تنظیم نشده | در `.env` یا Variables سرور مقدار بدهید |
| `Conflict: terminated by other getUpdates` | ربات جای دیگری هم روشن است | فقط یک نسخه را روشن بگذارید |
| `TimedOut` / `ConnectTimeout` / `NetworkError` | دسترسی به تلگرام نیست (فیلترینگ) | `BOT_PROXY_URL` را تنظیم کنید و `BOT_CONNECT_TIMEOUT=20` |
| `httpx[socks]` / `To use Socks5 proxies` | بسته `socksio` نیست | `pip install socksio` |
| «پروکسی MTProto برای ربات کار می‌کند» ❌ | نوع پروکسی اشتباه است | پروکسی SOCKS5 یا HTTP بسازید |
| `Unauthorized` | توکن اشتباه/باطل | توکن جدید از @BotFather |
| «❌ عضویت تأیید نشد» | ربات ادمین کانال نیست یا کاربر عضو نیست | ربات را ادمین کانال کنید |
| `/diag` می‌گوید «فقط برای ادمین» | `ADMIN_IDS` اشتباه است | `/id` را بزنید و همان عدد را بگذارید، بعد ری‌استارت |
| `pandas`/`numpy` نصب نمی‌شود | پایتون خیلی جدید/قدیمی | پایتون ۳.۱۱ یا ۳.۱۲ |
| بخش PLT می‌گوید کلید ندارد | `OPENAI_API_KEY` خالی است | کلید را ست کنید (بقیه ربات کار می‌کند) |

### لاگ‌ها
- اجرای دستی: خروجی ترمینال.
- systemd: `journalctl -u mrbiznes -f` یا `/var/log/mrbiznes.log`.
- Railway: تب `Logs`.

---

## چک‌لیست نهایی (۳۰ ثانیه‌ای)

- [ ] `BOT_TOKEN` درست است
- [ ] `ADMIN_IDS` شامل شناسه عددی من است
- [ ] `python scripts/doctor.py` → همه ✅
- [ ] فقط **یک** نسخه از ربات روشن است
- [ ] در تلگرام: `/ping` جواب می‌دهد و `/diag` گزارش سالم می‌دهد
- [ ] ربات ادمین کانال `@MrBiznesMarket` است
- [ ] (سرور ایران) `BOT_PROXY_URL` پر است و تست پروکسی ✅ است

---

## امنیت

- فایل `.env` را در گیت‌هاب، چت یا اسکرین‌شات نفرستید (در
  `.gitignore` هست).
- اگر توکن جایی لو رفت، در @BotFather → `/revoke` توکن جدید بگیرید.
- `ADMIN_IDS` را فقط برای افراد مطمئن پر کنید؛ ادمین به اطلاعات
  کاربران و پنل مدیریت دسترسی دارد.
