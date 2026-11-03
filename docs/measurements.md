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

## Cost (credits, as of 3.11.2026)
About $5.96 used, $175.01 remaining. Largest items: KMS $2.60, Glue $1.53, S3 $0.85. KMS keys bill monthly per key
whether or not they are used.
