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

## Findings that changed the prompt input (5.11.2026)
Per-flight check over all 1,234 (flight_date, flight_id) pairs in `battery_status`:
`temperature` is constant 0 in 989 flights (80%) and `max_cell_voltage_delta` in 1,188 (96%); none is all-NULL.
So "no data" is encoded as 0. Decision: drop `max_cell_voltage_delta`, and write a constant-0 `temperature` as
`n/a (not reported)`. Assumption (not verified at the source): a constant 0 for a whole flight means not reported.
Open risk: if temperature is only reported in some periods or hardware, its presence could leak the class
like GPS does; to be checked per group once results exist.
Also: `flight_id` alone is not unique (1,204 distinct ids vs 1,234 date/id pairs), so joins must use `flight_date` too.

## Prompt input (`src/bina/features.py`)
Each flight is reduced to min/max/mean/std for 6 battery signals (7 before `max_cell_voltage_delta` was dropped). Measured on the 50-flight sample (Athena):
`scale`, `remaining`, `discharged_mah` exist in 50/50 flights, `temperature` in 47/50, `max_cell_voltage_delta` in 48/50.
Rows per flight range 52 to 1,029 and duration 25.6 to 515 s, so raw rows are not sent.
Missing signals are written as `n/a (no data)` (never 0), partial gaps are reported as a count, and `flight_date`,
`flight_id` and time ranges are excluded. The prompt builder is tested, but **no Bedrock call has been made yet**.
