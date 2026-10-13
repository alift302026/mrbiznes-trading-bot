#!/usr/bin/env python3
"""
تست دود (smoke test) — بدون وصل شدن به تلگرام
==============================================

    python scripts/smoke_test.py

چه چیزی را چک می‌کند؟
    * همه ماژول‌های پروژه import می‌شوند
    * `build_application()` بدون خطا اپلیکیشن را می‌سازد
    * تعداد هندلرها و کارهای زمان‌بندی‌شده (workers) درست است
    * هندلرهای جدید /id و /diag و /ping ثبت شده‌اند
    * تنظیمات پروکسی درست خوانده می‌شود

هیچ درخواستی به تلگرام فرستاده نمی‌شود و توکن واقعی لازم نیست.
"""

from __future__ import annotations

import importlib
import os
import pkgutil
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# توکن فیک فقط برای ساخت اپلیکیشن (هیچ درخواستی فرستاده نمی‌شود)
os.environ.setdefault(
    "BOT_TOKEN",
    "123456789:AAHtest_token_only_for_smoke_test_1234567890",
)

failures: list[str] = []


def step(title: str) -> None:
    print(f"\n▶ {title}")


def main() -> int:

    print("=" * 50)
    print("  Smoke test — MrBiznes")
    print("=" * 50)

    # ------------------------------------------------------
    step("۱) import همه ماژول‌ها")

    import app

    failed_modules = []

    for module in pkgutil.walk_packages(
        app.__path__,
        prefix="app.",
    ):
        try:
            importlib.import_module(module.name)
        except Exception as exc:
            failed_modules.append(
                f"{module.name}: {type(exc).__name__}: {exc}"
            )

    if failed_modules:
        for item in failed_modules:
            print(f"  ❌ {item}")
        failures.append("import ماژول‌ها")
    else:
        print("  ✅ همه ماژول‌ها بدون خطا import شدند")

    # ------------------------------------------------------
    step("۲) ساخت اپلیکیشن (بدون تماس با تلگرام)")

    import main as bot_main

    try:
        application = bot_main.build_application()
        print("  ✅ build_application() موفق بود")

    except Exception:
        print("  ❌ build_application() خطا داد:")
        traceback.print_exc()
        failures.append("build_application")
        return 1

    handlers = application.handlers

    total_handlers = sum(
        len(group) for group in handlers.values()
    )

    print(f"  ℹ️ تعداد هندلرها: {total_handlers}")

    commands = sorted(
        command
        for group in handlers.values()
        for handler in group
        if hasattr(handler, "commands")
        for command in handler.commands
    )

    print(f"  ℹ️ دستورها: {', '.join('/' + c for c in commands)}")

    for required in ("start", "id", "diag", "ping"):
        if required in commands:
            print(f"  ✅ دستور /{required} ثبت شده است")
        else:
            print(f"  ❌ دستور /{required} ثبت نشده است")
            failures.append(f"دستور /{required}")

    # ------------------------------------------------------
    step("۳) کارهای زمان‌بندی‌شده (workers)")

    job_queue = application.job_queue

    if job_queue is None:
        print(
            "  ❌ Job Queue نیست — "
            '`pip install "python-telegram-bot[job-queue]"`'
        )
        failures.append("job queue")
    else:
        names = sorted(
            job.name or "?"
            for job in job_queue.jobs()
        )

        print(f"  ✅ Job Queue فعال: {', '.join(names)}")

        if len(names) < 3:
            print("  ⚠️ انتظار می‌رفت حداقل ۳ worker ثبت شود")
            failures.append("workers")

    # ------------------------------------------------------
    step("۴) تنظیمات پروکسی")

    from app.core.proxy import (
        get_proxy_url,
        mask_proxy,
        normalize_proxy_url,
    )

    samples = {
        "socks5://127.0.0.1:1080": "socks5://127.0.0.1:1080",
        "127.0.0.1:8080": "http://127.0.0.1:8080",
        "http://user:pass@1.2.3.4:3128":
            "http://user:pass@1.2.3.4:3128",
    }

    for raw, expected in samples.items():
        got = normalize_proxy_url(raw)

        if got == expected:
            print(f"  ✅ {raw}  →  {got}")
        else:
            print(f"  ❌ {raw}  →  {got} (انتظار: {expected})")
            failures.append("normalize_proxy_url")

    try:
        normalize_proxy_url("mtproto://1.2.3.4:443?secret=abc")
        print("  ❌ پروکسی MTProto رد نشد!")
        failures.append("mtproto rejection")
    except ValueError:
        print("  ✅ پروکسی MTProto با پیام واضح رد می‌شود")

    current = get_proxy_url()

    print(
        "  ℹ️ پروکسی فعلی: "
        + (mask_proxy(current) if current else "بدون پروکسی")
    )

    # ------------------------------------------------------
    print("\n" + "=" * 50)

    if failures:
        print("  ❌ نتیجه: ایراد دارد")
        for item in failures:
            print(f"     • {item}")
        return 1

    print("  ✅ نتیجه: همه‌چیز سالم است")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
