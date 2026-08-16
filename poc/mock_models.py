"""
Mock outputs for the reference events from the assignment.

No real biometric data and no real CV model are used in this PoC.
In the target architecture these values are produced by:
face detection -> quality assessment -> liveness -> embedding -> ANN search.
"""

MOCK_OUTPUTS = {
    "e-1001": {
        "face_detected": True,
        "quality_score": 0.90,
        "liveness_score": 0.96,
        "employee_id": "emp-4821",
        "match_score": 0.86,
        "second_best_score": 0.64,
    },
    "e-1002": {
        "face_detected": True,
        "quality_score": 0.48,
        "liveness_score": 0.88,
        "employee_id": None,
        "match_score": 0.0,
        "second_best_score": 0.0,
    },
    "e-1003": {
        "face_detected": True,
        "quality_score": 0.87,
        "liveness_score": 0.22,
        "employee_id": "emp-4821",
        "match_score": 0.91,
        "second_best_score": 0.50,
    },
    "e-1004": {
        "face_detected": True,
        "quality_score": 0.75,
        "liveness_score": 0.92,
        "employee_id": "emp-4821",
        "match_score": 0.80,
        "second_best_score": 0.76,
    },
    "e-1005": {
        "face_detected": True,
        "quality_score": 0.91,
        "liveness_score": 0.95,
        "employee_id": "emp-1033",
        "match_score": 0.88,
        "second_best_score": 0.59,
    },
}


def infer_mock(event_id: str) -> dict:
    if event_id not in MOCK_OUTPUTS:
        raise KeyError(f"No mock outputs for event_id={event_id}")
    return MOCK_OUTPUTS[event_id]
