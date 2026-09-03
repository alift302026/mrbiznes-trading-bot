"""Tests for the PLT Range Scanner's DEDICATED API key handling.

The cron scanner must use its own separate credential file
(.env.plt_range_scanner / PLT_SCANNER_LIVECOINWATCH_API_KEY),
independent from the bot's shared .env / LIVECOINWATCH_API_KEY.
"""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCANNER_PATH = REPO_ROOT / "plt_range_scanner.py"

spec = importlib.util.spec_from_file_location("plt_range_scanner", SCANNER_PATH)
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _clean_env(monkeypatch):
    monkeypatch.delenv("PLT_SCANNER_LIVECOINWATCH_API_KEY", raising=False)
    monkeypatch.delenv("LIVECOINWATCH_API_KEY", raising=False)


# ============================================================
# precedence
# ============================================================

def test_dedicated_env_var_wins(monkeypatch, tmp_path):
    _clean_env(monkeypatch)
    dedicated_file = _write(tmp_path / "dedicated.env", "PLT_SCANNER_LIVECOINWATCH_API_KEY=file-key\n")
    shared_file = _write(tmp_path / "shared.env", "LIVECOINWATCH_API_KEY=shared-key\n")

    monkeypatch.setenv("PLT_SCANNER_LIVECOINWATCH_API_KEY", "env-dedicated-key")

    assert scanner.resolve_lcw_key(dedicated_file, shared_file) == "env-dedicated-key"


def test_dedicated_file_key_beats_shared(monkeypatch, tmp_path):
    _clean_env(monkeypatch)
    dedicated_file = _write(
        tmp_path / "dedicated.env",
        "PLT_SCANNER_LIVECOINWATCH_API_KEY=dedicated-file-key\n",
    )
    shared_file = _write(tmp_path / "shared.env", "LIVECOINWATCH_API_KEY=shared-key\n")

    assert scanner.resolve_lcw_key(dedicated_file, shared_file) == "dedicated-file-key"


def test_dedicated_file_accepts_generic_name_inside_it(monkeypatch, tmp_path):
    _clean_env(monkeypatch)
    dedicated_file = _write(tmp_path / "dedicated.env", "LIVECOINWATCH_API_KEY=inside-dedicated\n")
    shared_file = _write(tmp_path / "shared.env", "LIVECOINWATCH_API_KEY=shared\n")

    assert scanner.resolve_lcw_key(dedicated_file, shared_file) == "inside-dedicated"


def test_shared_key_is_legacy_fallback(monkeypatch, tmp_path):
    _clean_env(monkeypatch)
    dedicated_file = tmp_path / "missing.env"
    shared_file = _write(tmp_path / "shared.env", "LIVECOINWATCH_API_KEY=shared-key\n")

    assert scanner.resolve_lcw_key(dedicated_file, shared_file) == "shared-key"


def test_shared_env_var_used_when_no_files(monkeypatch, tmp_path):
    _clean_env(monkeypatch)
    monkeypatch.setenv("LIVECOINWATCH_API_KEY", "shared-env-key")

    assert scanner.resolve_lcw_key(tmp_path / "a.env", tmp_path / "b.env") == "shared-env-key"


def test_empty_everywhere_returns_empty_string(monkeypatch, tmp_path):
    _clean_env(monkeypatch)

    assert scanner.resolve_lcw_key(tmp_path / "a.env", tmp_path / "b.env") == ""


# ============================================================
# dedicated file is wired into the module by default
# ============================================================

def test_module_uses_dedicated_env_file_path():
    assert scanner.DEDICATED_ENV_PATH.name == ".env.plt_range_scanner"
    assert scanner.DEDICATED_ENV_PATH.parent == scanner.BASE_DIR


def test_local_dedicated_env_file_exists():
    # created on install so the operator just pastes the key
    assert (REPO_ROOT / ".env.plt_range_scanner").exists()
    assert (REPO_ROOT / ".env.plt_range_scanner.example").exists()


def test_dedicated_file_is_git_ignored_but_example_is_not():
    import subprocess
    ignored = subprocess.run(
        ["git", "check-ignore", str(REPO_ROOT / ".env.plt_range_scanner")],
        capture_output=True, cwd=REPO_ROOT,
    )
    assert ignored.returncode == 0, "real dedicated env must stay git-ignored"

    example = subprocess.run(
        ["git", "check-ignore", str(REPO_ROOT / ".env.plt_range_scanner.example")],
        capture_output=True, cwd=REPO_ROOT,
    )
    assert example.returncode != 0, "example template must be committable"


def test_key_is_sent_as_lcw_header(monkeypatch, tmp_path):
    """The dedicated key must actually go out as x-api-key to LCW only."""
    _clean_env(monkeypatch)

    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b"[]"

    def fake_urlopen(request, timeout):
        captured["headers"] = dict(request.header_items())
        captured["url"] = request.full_url
        return FakeResponse()

    monkeypatch.setenv("PLT_SCANNER_LIVECOINWATCH_API_KEY", "dedicated-123")
    monkeypatch.setattr(scanner.urllib.request, "urlopen", fake_urlopen)

    scanner.lcw_top_universe()

    headers_lower = {k.lower(): v for k, v in captured["headers"].items()}
    assert headers_lower.get("x-api-key") == "dedicated-123"
    assert "api.livecoinwatch.com" in captured["url"]


def test_bitunix_requests_carry_no_api_key(monkeypatch, tmp_path):
    """Exchange calls must remain credential-free (read-only public)."""
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"code":0,"data":[]}'

    def fake_urlopen(request, timeout):
        captured["headers"] = dict(request.header_items())
        return FakeResponse()

    monkeypatch.setenv("PLT_SCANNER_LIVECOINWATCH_API_KEY", "dedicated-123")
    monkeypatch.setattr(scanner.urllib.request, "urlopen", fake_urlopen)

    scanner.fetch_closed_m15("BTCUSDT")

    headers_lower = {k.lower(): v for k, v in captured["headers"].items()}
    assert "x-api-key" not in headers_lower


def test_key_from_dedicated_file_reaches_lcw_header(monkeypatch, tmp_path):
    """End-to-end: key written ONLY in the dedicated FILE (no env var)
    must be picked up and sent as x-api-key to LiveCoinWatch."""
    _clean_env(monkeypatch)

    dedicated = _write(
        tmp_path / ".env.plt_range_scanner",
        "# scanner key\nPLT_SCANNER_LIVECOINWATCH_API_KEY=file-only-key-999\n",
    )

    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b"[]"

    def fake_urlopen(request, timeout):
        captured["headers"] = dict(request.header_items())
        return FakeResponse()

    monkeypatch.setattr(scanner.urllib.request, "urlopen", fake_urlopen)

    assert scanner.lcw_key_source(dedicated, tmp_path / "shared.env") == "dedicated-file"
    scanner.lcw_top_universe.__wrapped__ if hasattr(scanner.lcw_top_universe, "__wrapped__") else None

    # call with the dedicated file wired in
    key = scanner.resolve_lcw_key(dedicated, tmp_path / "shared.env")
    scanner.http_json(
        f"{scanner.LCW_BASE}/coins/list",
        payload={"currency": "USD"},
        api_key=key,
    )

    headers_lower = {k.lower(): v for k, v in captured["headers"].items()}
    assert headers_lower.get("x-api-key") == "file-only-key-999"


def test_cron_banner_reports_dedicated_file_source(monkeypatch, tmp_path, capsys):
    """scan() banner must announce the dedicated-file key source."""
    _clean_env(monkeypatch)

    dedicated = _write(
        tmp_path / ".env.plt_range_scanner",
        "PLT_SCANNER_LIVECOINWATCH_API_KEY=banner-key\n",
    )
    monkeypatch.setattr(scanner, "DEDICATED_ENV_PATH", dedicated)
    monkeypatch.setattr(
        scanner, "SHARED_ENV_PATH", tmp_path / "shared.env"
    )
    # no network in sandbox: universe falls back to majors
    monkeypatch.setattr(scanner, "lcw_top_universe", lambda: (_ for _ in ()).throw(RuntimeError("offline")))
    monkeypatch.setattr(scanner, "fetch_closed_m15", lambda symbol: [])
    monkeypatch.setattr(scanner, "bitunix_tradable_bases", lambda: None)

    scanner.scan()
    out = capsys.readouterr().out
    assert "LCW key          : dedicated-file" in out


def test_file_loaded_key_reports_true_origin(monkeypatch, tmp_path):
    """A key loaded from the dedicated file at import time must be
    reported as 'dedicated-file', not 'dedicated-env'."""
    _clean_env(monkeypatch)

    key = "PLT_SCANNER_LIVECOINWATCH_API_KEY"
    monkeypatch.setenv(key, "came-from-file")
    monkeypatch.setitem(scanner._ENV_ORIGIN, key, scanner.DEDICATED_ENV_PATH.name)

    source, value = next(iter(scanner._lcw_key_candidates(None, None)))
    assert source == "dedicated-file"
    assert value == "came-from-file"

    assert scanner.lcw_key_source() == "dedicated-file"


def test_real_env_var_still_reports_dedicated_env(monkeypatch):
    """A genuinely injected env var (no file origin) stays 'dedicated-env'."""
    _clean_env(monkeypatch)
    monkeypatch.setenv("PLT_SCANNER_LIVECOINWATCH_API_KEY", "true-env")

    source, value = next(iter(scanner._lcw_key_candidates(None, None)))
    assert source == "dedicated-env"
    assert value == "true-env"
