import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from app import process

BASE_DIR = Path(__file__).resolve().parent
EVENT_DIR = BASE_DIR / "demo_events"

SCENARIOS = [
    ("Типовой проход", "e-1001.json"),
    ("Плохое качество", "e-1002.json"),
    ("Попытка spoofing", "e-1003.json"),
    ("Неоднозначный случай", "e-1004.json"),
    ("Offline + старый кеш", "e-1005.json"),
]

DECISION_LABELS = {
    "allow": "РАЗРЕШИТЬ ПРОХОД",
    "manual_review": "РУЧНАЯ ПРОВЕРКА",
    "deny": "ОТКАЗАТЬ",
}

REASON_RU = {
    "quality_ok": "Качество кадра достаточное",
    "liveness_ok": "Проверка живого лица пройдена",
    "match_above_allow_threshold": "Совпадение выше порога допуска",
    "margin_ok": "Отрыв от второго кандидата достаточный",
    "low_quality": "Низкое качество кадра",
    "retry_frame_or_use_card": "Нужен повторный кадр или карта",
    "liveness_failed": "Проверка живого лица не пройдена",
    "possible_spoofing": "Возможна попытка подмены лица",
    "low_confidence_or_small_margin": "Недостаточная уверенность распознавания",
    "offline": "Центральный сервис недоступен",
    "stale_edge_cache": "Локальный кеш устарел",
    "access_status_not_trusted": "Актуальность права доступа не подтверждена",
    "match_too_low": "Слишком низкая уверенность совпадения",
    "face_not_detected": "Лицо не обнаружено",
    "offline_fresh_cache": "Offline-режим, локальный кеш актуален",
}


class FaceAccessDemo(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Face Access PoC")
        self.geometry("960x620")
        self.minsize(900, 560)

        self.selected_file = tk.StringVar(value=SCENARIOS[0][1])

        self._build_ui()
        self._show_input(SCENARIOS[0][1])

    def _build_ui(self):
        main = ttk.Frame(self, padding=16)
        main.pack(fill="both", expand=True)

        title = ttk.Label(
            main,
            text="PoC системы распознавания лиц на проходной",
            font=("Arial", 16, "bold"),
        )
        title.pack(anchor="w")

        subtitle = ttk.Label(
            main,
            text="Выберите сценарий и запустите проверку. Реальная биометрия не используется — CV/ML-сигналы замоканы.",
        )
        subtitle.pack(anchor="w", pady=(4, 14))

        content = ttk.Frame(main)
        content.pack(fill="both", expand=True)

        # Left panel
        left = ttk.LabelFrame(content, text="Сценарии", padding=12)
        left.pack(side="left", fill="y", padx=(0, 12))

        for label, filename in SCENARIOS:
            ttk.Radiobutton(
                left,
                text=label,
                value=filename,
                variable=self.selected_file,
                command=lambda f=filename: self._show_input(f),
            ).pack(anchor="w", pady=6)

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=10)

        ttk.Button(
            left,
            text="Запустить проверку",
            command=self.run_selected,
        ).pack(fill="x", pady=(0, 6))

        ttk.Button(
            left,
            text="Запустить все",
            command=self.run_all,
        ).pack(fill="x")

        # Right panel
        right = ttk.Frame(content)
        right.pack(side="left", fill="both", expand=True)

        input_box = ttk.LabelFrame(right, text="Входное событие", padding=8)
        input_box.pack(fill="both", expand=True)

        self.input_text = tk.Text(input_box, height=12, wrap="none")
        self.input_text.pack(fill="both", expand=True)

        result_box = ttk.LabelFrame(right, text="Результат", padding=8)
        result_box.pack(fill="both", expand=True, pady=(12, 0))

        self.decision_label = ttk.Label(
            result_box,
            text="Решение ещё не принято",
            font=("Arial", 15, "bold"),
        )
        self.decision_label.pack(anchor="w", pady=(0, 8))

        self.summary_label = ttk.Label(result_box, text="")
        self.summary_label.pack(anchor="w", pady=(0, 8))

        self.result_text = tk.Text(result_box, height=11, wrap="word")
        self.result_text.pack(fill="both", expand=True)

    def _show_input(self, filename):
        path = EVENT_DIR / filename
        data = json.loads(path.read_text(encoding="utf-8"))
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", json.dumps(data, ensure_ascii=False, indent=2))

    def run_selected(self):
        filename = self.selected_file.get()
        result = process(str(EVENT_DIR / filename))
        self._render_result(result)

    def run_all(self):
        results = []
        for label, filename in SCENARIOS:
            result = process(str(EVENT_DIR / filename))
            results.append(
                f"{label}: {result['decision']} / {result['turnstile_command']}"
            )
        messagebox.showinfo("Результаты всех сценариев", "\n".join(results))
        # Show final scenario in detail
        self.selected_file.set(SCENARIOS[-1][1])
        self._show_input(SCENARIOS[-1][1])
        self._render_result(process(str(EVENT_DIR / SCENARIOS[-1][1])))

    def _render_result(self, result):
        decision = result["decision"]
        self.decision_label.config(
            text=f"Решение: {DECISION_LABELS.get(decision, decision)}"
        )

        review_text = "Да" if result["requires_human_review"] else "Нет"
        self.summary_label.config(
            text=(
                f"Команда турникету: {result['turnstile_command']}   |   "
                f"Ручная проверка: {review_text}   |   "
                f"Latency: {result['latency_ms']} ms"
            )
        )

        reasons = [REASON_RU.get(r, r) for r in result["reasons"]]

        details = [
            f"event_id: {result['event_id']}",
            f"employee_id: {result['employee_id']}",
            f"match_score: {result['match_score']}",
            f"margin_to_second_best: {result['margin_to_second_best']}",
            f"quality_score: {result['quality']['quality_score']}",
            f"liveness_score: {result['quality']['liveness_score']}",
            f"degraded_mode: {result['degraded_mode']}",
            "",
            "Причины решения:",
        ]
        details.extend(f"• {reason}" for reason in reasons)
        details.append("")
        details.append(f"audit_id: {result['audit_id']}")

        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", "\n".join(details))


if __name__ == "__main__":
    app = FaceAccessDemo()
    app.mainloop()
