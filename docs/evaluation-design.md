# Evaluation design (AI layer)

## Ground truth
`mapping.json` of UAV-SEAD: 1,396 labeled flights. Flights with exactly one clean label are used:
Normal 899, External Position 192, Altitude 73, Mechanical 41, Global Position 39 (total 1,244).
Multi-label flights and the 141 `Uncategorized` flights are excluded by decision.
After path checks the usable pool is 1,125 flights (110 skipped session paths, 6 without a date folder, 3 not found).

## Sample
`data/sample.json`: 50 flights, stratified by (class, has_gps), seed 42, 37 distinct dates.

| GPS | Class | Flights |
|---|---|---|
| with | Global Position | 12 |
| with | External Position | 5 |
| with | Normal | 4 |
| with | Mechanical | 3 |
| without | Altitude | 8 |
| without | External Position | 6 |
| without | Mechanical | 6 |
| without | Normal | 6 |

## Leakage risk
GPS presence reveals the class: in the pool, Global Position flights always have GPS (39/39) and Altitude flights never do (0/68).
A model could classify from "is there GPS data" alone. Controls: report metrics separately for the with-GPS and without-GPS groups,
and do not put identifiers (`flight_date`, `flight_id`, ranges) into the prompt.

## Metrics
Per-class precision, recall, F1, support and the confusion matrix (`src/bina/metrics.py`). With 50 flights the per-class
numbers are small-sample estimates, report them with their counts.
