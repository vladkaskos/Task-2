from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from app import process


def run(name):
    return process(str(HERE / "demo_events" / name))


def test_happy_path():
    result = run("e-1001.json")
    assert result["decision"] == "allow"
    assert result["turnstile_command"] == "open"
    assert result["requires_human_review"] is False


def test_low_quality():
    result = run("e-1002.json")
    assert result["decision"] == "manual_review"
    assert result["turnstile_command"] == "do_not_open"


def test_spoofing():
    result = run("e-1003.json")
    assert result["decision"] == "deny"
    assert result["turnstile_command"] == "do_not_open"


def test_low_confidence():
    result = run("e-1004.json")
    assert result["decision"] == "manual_review"
    assert result["turnstile_command"] == "do_not_open"


def test_offline_stale_cache():
    result = run("e-1005.json")
    assert result["decision"] == "manual_review"
    assert result["turnstile_command"] == "do_not_open"
    assert result["degraded_mode"] is True


if __name__ == "__main__":
    test_happy_path()
    test_low_quality()
    test_spoofing()
    test_low_confidence()
    test_offline_stale_cache()
    print("All smoke tests passed")
