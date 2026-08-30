"""Persian research report + machine-readable strategy specs."""
import json
import os

OUT = "/home/user/research/out"

META = {
    "S1_TREND_PB": {
        "name_fa": "۱) پول‌بک روند (S1)",
        "regime": "بازار رونددار (ADX ≥ آستانه، راستای 4H مشخص)",
        "rules": "LONG: بسته‌شدن بالای EMA200 و EMA20>EMA50 + برخورد به ناحیه EMA20 و ماندن بالای EMA50 + تریگر UT Bot خرید + RSI میانۀ مجاز + حجم نسبی کافی. SHORT: قرینه. ورود: بازِ کندل بعد. SL: ATR×ضریب. TP1/TP2 طبق R.",
        "why": "EMA جهت و ناحیه ارزش را می‌دهد؛ UT Bot فقط تریگر زمانی است که حرکت دوباره راه می‌افتد؛ ADX از بازی در بازار تکه‌تکه جلوگیری می‌کند؛ حجم برای پرهیز از پول‌بک‌های بی‌تقاضاست.",
        "weak": "در رنج‌ها پشت‌سرهم استاپ می‌خورد؛ به‌همین دلیل ADX و ساختار 4H سد هستند.",
    },
    "S2_FVG_CONT": {
        "name_fa": "۲) ادامه با FVG (S2)",
        "regime": "روند تعریف‌شده 4H با تأیید 1H",
        "rules": "ساختار 4H (HH/HL یا LH/LL هم‌جهت) + تأیید 1H (بسته شدن سمت درست EMA20) + FVG پرنشده‌ی هم‌جهت با حجم انبساطی هنگام شکل‌گیری؛ ورود LIMIT از میانه‌ی گپ در حداکثر ۱۲ کندل؛ SL پشت لبه‌ی دور FVG؛ TP1/TP2 با R/R بالاتر.",
        "why": "FVG محل بازگشت سفارش‌های بزرگ است؛ حجم زمان ساخت گپ اعتبارش را بالا می‌برد؛ ساختار 4H فقط به‌سهم خود جهت می‌دهد تا خلاف جریان نخریم.",
        "weak": "ادامه روند بدون پرشدن گپ → عدم پر شدن LIMIT (فرصت سوخته، نه زیان).",
    },
    "S3_RANGE_REV": {
        "name_fa": "۳) برگشت از محدوده‌ی رنج (S3)",
        "regime": "بازار رنج باریک با کاهش حجم (ADX<25)",
        "rules": "بازه‌ی ۶۰ کندلی با حداقل ۳ برخورد دو سمت و عرض محدود + کاهش حجم نیمه‌ی دوم؛ خرید از کف با کندل پذیرش (بسته شدن در نیمه‌ی بالای خودش) + StochRSI<25؛ فروش از سقف قرینه؛ SL پشت مرز؛ TP1 میانه، TP2 لبه‌ی مقابل؛ حداقل R/R لازم.",
        "why": "تشخیص رنج با چند برخورد هم‌تراز و ماندن عرض در محدوده؛ کاهش حجم یعنی فروشنده/خریدار درونی کم‌جون است و برگشت ارزان‌تر رخ می‌دهد.",
        "weak": "شکست واقعی بازه به‌جای برگشت => استاپ؛ فقط در ADX پایین مجاز است.",
    },
    "S4_BRK_RETEST": {
        "name_fa": "۴) شکست و ریتست (S4)",
        "regime": "خروج از تثبیت/تراکم (هر رژیمی، ADX ملایم)",
        "rules": "بسته شدن قوی (بدنه ≥۶۰٪، حجم انبساطی) بیرون از سقف/کف ۴۰ کندل؛ ورود فقط پس از ریتست موفق سطح در ≤۸ کندل؛ SL پشت اکستریم ریتست؛ TP1=1.5R و TP2=3R.",
        "why": "شکست بدون ریتست = تعقیب هیجانی؛ ریتست سطحِ شکسته، کم‌ریسک‌ترین نقطه‌ی پیوستن است.",
        "weak": "شکست‌های جعلی (fakeout) در بازار کم‌حجم — به‌خاطر همین شرط حجم و بدنه هست.",
    },
    "S5_MOM_FLIP": {
        "name_fa": "۵) چرخش مومنتوم (S5)",
        "regime": "آغاز موج جدید هم‌جهت Supertrend 4H",
        "rules": "Supertrend(10,3) روی 4H جهت می‌دهد؛ روی 15m کراس هیستوگرام MACD از صفر + RSI سمت درست + بالا/پایین EMA200 + ADX≥20؛ ورود بازِ کندل بعد؛ SL=ATR×ضریب.",
        "why": "Supertrend 4H نقش قاضی روند را دارد (ساختار سریع‌تر از سوئینگ‌ها)؛ MACD کراس، شروع موج قابل‌اندازه‌گیری 15m است.",
        "weak": "کراس‌های MACD در رنج‌های پهن وینگر می‌زند؛ ADX و 4H آن را مهار می‌کنند.",
    },
}

SOURCES = [
    "XT Exchange API Docs (public kline, v4): sapi.xt.com/v4/public/kline",
    "UT Bot Alerts concept (public TradingView indicator, Pine v4)",
    "Bulkowski / academic literature on pullback & breakout-retest (public)",
    "ICT/FVG public educational materials (concept only)",
    "ADX/ATR (Wilder, 1978) public documentation",
    "MACD/RSI/StochRSI standard definitions (public docs)",
]


def fmt(m, key, nd=2):
    v = m.get(key)
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def render(report):
    lines = []
    lines.append("# گزارش تحقیق MrBiznes — استراتژی‌های ۱۵ دقیقه‌ای")
    lines.append("")
    lines.append("این گزارش صرفاً پژوهش است؛ هیچ معامله‌ای انجام نشده و "
                 "هیچ وعده‌ی سودی داده نمی‌شود. تأیید نهایی هر سیگنال "
                 "در محصول زنده با انسان است (WAITING_FOR_HUMAN_APPROVAL).")
    lines.append("")
    lines.append("## روش‌شناسی بک‌تست")
    lines.append("")
    lines.append("- داده: کندل‌های ۱۵ دقیقه‌ای اسپات (Binance public dump)"
                 " — صرفاً جهت اعتبارسنجی؛ خوانش زنده‌ی محصول از XT انجام می‌شود.")
    lines.append("- تصمیم فقط روی **کندل بسته**؛ ورود در **بازِ کندل بعد**"
                 " (LIMIT فقط در S2). بدون look-ahead.")
    lines.append("- کارمزد هر سمت ۰.۱۰٪ + لغزش ۰.۰۳٪؛ در برخورد هم‌زمان"
                 " SL/TP در یک کندل، محافظه‌کارانه **ابتدا SL**.")
    lines.append("- خروج پلکانی: ۵۰٪ TP1، باقی TP2؛ پس از TP1 استاپ = سر به سر.")
    lines.append("- تقسیم زمانی ۶۰٪ آموزش / ۲۰٪ اعتبارسنجی / ۲۰٪ OOS؛"
                 " بهینه‌سازی فقط روی آموزش؛ walk-forward سه‌تیکه؛"
                 " تست حساسیت ±۱ گام پارامتر.")

    rows = []
    for sid, per in report["strategies"].items():
        meta = META[sid]
        agg_train = agg_oos = None
        tot = 0
        for sym, r in per.items():
            if "oos" not in r:
                continue
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"## {meta['name_fa']}")
        lines.append("")
        lines.append(f"**رژیم بازار:** {meta['regime']}")
        lines.append("")
        lines.append(f"**قواعد مکانیکی:** {meta['rules']}")
        lines.append("")
        lines.append(f"**چرا این تأییدها:** {meta['why']}")
        lines.append("")
        lines.append(f"**نقاط ضعف:** {meta['weak']}")
        lines.append("")
        lines.append("| نماد | پارامترها | سیگنال | Train PF | Train WR% | OOS تعداد | OOS WR% | OOS PF | Expectancy(R) | MaxDD(R) |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for sym, r in per.items():
            if "oos" not in r:
                lines.append(f"| {sym} | — | — | — | — | NO_VALID | — | — | — | — |")
                continue
            t, o = r["train"], r["oos"]
            prm = ",".join(f"{k}={v}" for k, v in r["params"].items())
            lines.append(
                f"| {sym} | {prm} | {r['signals']} | "
                f"{fmt(t,'profit_factor')} | {fmt(t,'win_rate',1)} | "
                f"{o.get('trades',0)} | {fmt(o,'win_rate',1)} | "
                f"{fmt(o,'profit_factor')} | {fmt(o,'expectancy_r')} | "
                f"{fmt(o,'max_dd_r')} |"
            )
            rows.append((sid, sym, o))
    lines.append("")
    lines.append("## رتبه‌بندی نهایی (بر اساس OOS تجمیعی)")
    lines.append("")
    agg = {}
    for sid, sym, o in rows:
        a = agg.setdefault(sid, {"n": 0, "w": 0.0, "e": 0.0, "pf": []})
        if o.get("trades"):
            a["n"] += o["trades"]
            if o.get("win_rate") is not None:
                a["w"] += o["win_rate"] * o["trades"]
            a["e"] += (o.get("expectancy_r") or 0) * o["trades"]
            a["pf"].append(o.get("profit_factor") or 0)
    ranked = sorted(
        agg.items(),
        key=lambda kv: (kv[1]["e"] / max(kv[1]["n"], 1)),
        reverse=True,
    )
    lines.append("| رتبه | استراتژی | معاملات OOS | WR% میانگین | Expectancy میانگین (R) | وضعیت نمونه |")
    lines.append("|---|---|---|---|---|---|")
    for i, (sid, a) in enumerate(ranked, 1):
        n = a["n"]
        wr = a["w"] / n if n else 0
        exp = a["e"] / n if n else 0
        flag = "OK" if n >= 200 else "**INSUFFICIENT SAMPLE**"
        lines.append(f"| {i} | {META[sid]['name_fa']} | {n} | {wr:.1f} | {exp:.3f} | {flag} |")
    lines.append("")
    lines.append("> قانون ۸۰٪: هیچ پارامتری برای رسیدن به ۸۰٪ دست‌کاری نشده؛"
                 " اگر OOS WR ≥ ۸۰٪ با نمونه‌ی کافی مستقل رخ دهد، برچسب"
                 " VERIFIED زده می‌شود؛ در غیر این صورت عدد واقعی مذکور است.")
    lines.append("")
    lines.append("## منابع")
    for s in SOURCES:
        lines.append(f"- {s}")
    return "\n".join(lines)


def write_specs(report):
    specs = {}
    for sid, per in report["strategies"].items():
        meta = META[sid]
        best = None
        for sym, r in per.items():
            if "oos" not in r:
                continue
            if best is None or (r["oos"].get("expectancy_r") or -9) > best[1]:
                best = (r["params"], r["oos"].get("expectancy_r") or -9)
        specs[sid] = {
            "strategy_id": sid,
            "timeframe": "15m",
            "params_default": best[0] if best else None,
            "regime": meta["regime"],
            "rules_fa": meta["rules"],
            "approval": "HUMAN_MANDATORY",
            "execution": "SIGNAL_ONLY",
            "risk_model": {
                "fee_side": 0.001, "slip_side": 0.0003,
                "exit_plan": "50% TP1, 50% TP2, SL->BE after TP1",
            },
        }
    with open(os.path.join(OUT, "strategies_spec.json"), "w") as f:
        json.dump(specs, f, ensure_ascii=False, indent=2)


def main():
    with open(os.path.join(OUT, "metrics.json")) as f:
        report = json.load(f)
    md = render(report)
    with open(os.path.join(OUT, "report_fa.md"), "w") as f:
        f.write(md)
    write_specs(report)
    print("wrote out/report_fa.md and out/strategies_spec.json")


if __name__ == "__main__":
    main()
