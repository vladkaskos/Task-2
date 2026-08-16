# Proof-of-Concept: Face Access

Минимальный PoC для задания по системе распознавания лиц на проходной.

## Что проверяет PoC

PoC подтверждает один вертикальный сценарий принятия решения:
mock-событие с камеры -> проверка качества -> mock liveness ->
mock identification -> `allow / manual_review / deny` -> demo-команда
турникету -> запись в audit log.

Обязательные сценарии:
- `e-1001` — happy path: уверенное совпадение -> `allow`;
- `e-1004` — risky path: два близких кандидата -> `manual_review`,
  турникет автоматически не открывается.

Дополнительно:
- `e-1002` — плохое качество -> `manual_review`;
- `e-1003` — возможный spoofing -> `deny`;
- `e-1005` — offline + устаревший edge-кеш -> `manual_review`.

## Что здесь намеренно НЕ реализовано

В соответствии с ограничениями задания PoC:
- не является production-ready системой контроля доступа;
- не содержит реальных фотографий сотрудников и реальных биометрических данных;
- не обучает собственную face recognition модель;
- не интегрируется с реальным турникетом;
- не использует Kubernetes, feature store или сложную MLOps-инфраструктуру;
- не содержит отдельный UI охраны;
- не реализует подробную юридическую логику;
- не моделирует полноценную multi-site инфраструктуру.

## Что является mock

Входные JSON используют референсный формат из задания.
Результаты CV/ML-компонентов находятся в `mock_models.py`.

Mock-значения имитируют:
- face detection;
- quality assessment;
- passive liveness / anti-spoofing;
- embedding + ANN identification.

В целевой архитектуре эти mock-компоненты заменяются готовыми
предобученными CV-моделями и локальным ANN-индексом на edge.

## Демонстрационные правила

- качество кадра: `quality_score >= 0.70`;
- liveness: `liveness_score >= 0.80`;
- `allow`: `match_score >= 0.82` и отрыв от второго кандидата `>= 0.12`;
- пограничные совпадения -> `manual_review`;
- возможный spoofing -> `deny`;
- offline с кешем старше 15 минут -> `manual_review`.

Пороги являются assumptions для PoC. В production они должны быть
подобраны на validation set с учётом FAR/FRR и цены false accept.

## Запуск

Требуется Python 3.10+. Внешние библиотеки не нужны.

Из корня репозитория:

```bash
python poc/app.py --demo
```

Один сценарий:

```bash
python poc/app.py poc/demo_events/e-1001.json
```


## Графический интерфейс

Для более наглядной демонстрации добавлен простой интерфейс на `Tkinter`.
Он не является production UI охраны и нужен только для demo-пути.

Запуск из корня репозитория:

```bash
python poc/ui.py
```

В интерфейсе можно выбрать один из пяти референсных сценариев и увидеть:
- входное событие;
- решение `allow / manual_review / deny`;
- команду `open / do_not_open`;
- необходимость ручной проверки;
- причины решения;
- quality, liveness, match score и latency.

## Smoke-test

```bash
python poc/test_smoke.py
```

Ожидаемый результат:

```text
All smoke tests passed
```

## Audit log

После запуска решения записываются в:

```text
poc/data/access.log
```

В audit log сохраняются решение, причины, scores, demo-команда турникету,
degraded mode и latency.

## Важное ограничение

`turnstile_command = open` — только демонстрация того, какую команду система
сформировала бы. Никакой физический турникет PoC не открывает.
