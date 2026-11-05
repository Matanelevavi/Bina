# Measurements

## CSV vs Parquet in Athena
Query: average and count over the same 46 Mechanical flights, one run each.

| Format | DataScannedInBytes |
|---|---|
| CSV | 1,492,495 |
| Parquet (partitioned) | 72,996 |

About 20.4x less data scanned. Caveats: small sample, one run each, averages equal up to floating-point noise
(20.72241941395046 vs 20.722419413950448). Athena bills by bytes scanned, so this ratio is a cost ratio too, but the absolute
amounts here are tiny.

## Glue runs (after re-encryption with the curated key)
All four finished SUCCEEDED. Job-to-duration mapping follows the order in which results were recorded.
| Job | Duration | Partitions |
|---|---|---|
| bina-battery-status-etl | 220 s | 151 |
| bina-actuator-outputs-etl | 319 s | 151 |
| bina-sensor-combined-etl | 542 s | 151 |
| bina-vehicle-gps-position-etl | 107 s | 23 |

## Column types: string to numeric (5.11.2026)
`spark.read.csv(header=True)` without a schema reads every column as `string`, so most curated columns were text.
The jobs now cast numeric columns before writing Parquet. Checked with a before/after query on the same table.

| Table | Rows before / after | Non-null counts | Data scanned before / after |
|---|---|---|---|
| actuator_outputs | 15,319,361 / 15,319,361 | `output[0]`, `output[7]`, `timestamp` unchanged | 107.36 MB / 85.18 MB |
| battery_status | 343,137 / 343,137 | 5 cast columns unchanged (`max_cell_voltage_delta` 331,396) | 7.41 MB / 7.47 MB |
| sensor_combined | 37,928,479 / 37,928,479 | `gyro_rad[0]`, `accelerometer_m_s2[2]` unchanged; barometer columns 1,448,678 / 1,448,678 | 593.95 MB / 580.26 MB |

Reading: no values were lost in the columns that were checked, and the scan size did **not** change consistently
(-21%, +0.8% and -2.3% on the three tables). The benefit of the cast is correct types and simpler queries, not a guaranteed
cost saving. Limits: one run each, only some columns were checked, and a cast of a bad string yields `NULL`
(a `NaN` would not show up in a `COUNT`). In `sensor_combined` the barometer columns are non-null in only 1,448,678 of 37,928,479 rows (3.8%).

## Cost (credits, as of 3.11.2026)
About $5.96 used, $175.01 remaining. Largest items: KMS $2.60, Glue $1.53, S3 $0.85. KMS keys bill monthly per key
whether or not they are used.
