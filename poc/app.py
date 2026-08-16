import argparse
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from mock_models import infer_mock

# Demo thresholds. In production they must be calibrated on a validation set.
ALLOW_THRESHOLD = 0.82
MANUAL_THRESHOLD = 0.70
MIN_MARGIN = 0.12
MIN_QUALITY = 0.70
MIN_LIVENESS = 0.80
MAX_OFFLINE_CACHE_AGE_MIN = 15

BASE_DIR = Path(__file__).resolve().parent
LOG_PATH = BASE_DIR / "data" / "access.log"


def load_event(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_result(event, decision, signals, reasons, started_at):
    latency_ms = round((time.perf_counter() - started_at) * 1000, 2)
    match = signals.get("match_score", 0.0)
    second = signals.get("second_best_score", 0.0)

    return {
        "event_id": event["event_id"],
        "decision_id": f"d-{uuid.uuid4().hex[:8]}",
        "decision": decision,
        "employee_id": signals.get("employee_id"),
        "match_score": match,
        "margin_to_second_best": round(match - second, 3),
        "quality": {
            "face_detected": signals.get("face_detected", False),
            "quality_score": signals.get("quality_score", 0.0),
            "liveness_score": signals.get("liveness_score", 0.0),
        },
        "reasons": reasons,
        # No real turnstile integration: this is only a demo command.
        "turnstile_command": "open" if decision == "allow" else "do_not_open",
        "requires_human_review": decision == "manual_review",
        "degraded_mode": event.get("metadata", {}).get("network") != "online",
        "audit_id": f"a-{uuid.uuid4().hex[:8]}",
        "latency_ms": latency_ms,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }


def decide(event: dict) -> dict:
    started_at = time.perf_counter()
    signals = infer_mock(event["event_id"])
    reasons = []

    if not signals["face_detected"]:
        return build_result(
            event, "manual_review", signals,
            ["face_not_detected"], started_at
        )

    if signals["quality_score"] < MIN_QUALITY:
        return build_result(
            event, "manual_review", signals,
            ["low_quality", "retry_frame_or_use_card"], started_at
        )
    reasons.append("quality_ok")

    if signals["liveness_score"] < MIN_LIVENESS:
        return build_result(
            event, "deny", signals,
            reasons + ["liveness_failed", "possible_spoofing"], started_at
        )
    reasons.append("liveness_ok")

    metadata = event.get("metadata", {})
    if metadata.get("network") == "offline":
        cache_age = int(metadata.get("cache_age_minutes", 0))
        if cache_age > MAX_OFFLINE_CACHE_AGE_MIN:
            return build_result(
                event, "manual_review", signals,
                reasons + ["offline", "stale_edge_cache", "access_status_not_trusted"],
                started_at
            )
        reasons.append("offline_fresh_cache")

    match_score = signals["match_score"]
    margin = match_score - signals["second_best_score"]

    if signals["employee_id"] is None or match_score < MANUAL_THRESHOLD:
        return build_result(
            event, "deny", signals,
            reasons + ["match_too_low"], started_at
        )

    if match_score >= ALLOW_THRESHOLD and margin >= MIN_MARGIN:
        return build_result(
            event, "allow", signals,
            reasons + ["match_above_allow_threshold", "margin_ok"], started_at
        )

    return build_result(
        event, "manual_review", signals,
        reasons + ["low_confidence_or_small_margin"], started_at
    )


def write_audit(result: dict):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")


def process(path: str) -> dict:
    event = load_event(path)
    result = decide(event)
    write_audit(result)
    return result


def run_demo():
    demo_dir = BASE_DIR / "demo_events"
    for filename in (
        "e-1001.json",
        "e-1002.json",
        "e-1003.json",
        "e-1004.json",
        "e-1005.json",
    ):
        result = process(str(demo_dir / filename))
        print(f"\n=== {filename} ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Minimal face-access PoC")
    parser.add_argument("event", nargs="?", help="Path to input event JSON")
    parser.add_argument("--demo", action="store_true", help="Run all reference scenarios")
    args = parser.parse_args()

    if args.demo:
        run_demo()
    elif args.event:
        print(json.dumps(process(args.event), ensure_ascii=False, indent=2))
    else:
        parser.print_help()
