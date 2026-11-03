# Architecture

```
 UAV-SEAD (Hugging Face)          raw bucket (SSE-KMS key A, versioned)
 ULog -> CSV per flight   --->    <flight_date>/<flight>_<topic>_0.csv
                                          |
                                  Glue ETL (4 jobs: battery_status, actuator_outputs,
                                  sensor_combined, vehicle_gps_position)
                                          |
                                  curated bucket (SSE-KMS key B)
                                  Parquet, partitioned by flight_date
                                          |
                          Glue Crawlers -> Data Catalog (bina_db)
                                          |
                                      Athena (workgroup `primary`)
                                          |
                          Bedrock (Claude Haiku) - anomaly-type classifier
                                          |
                          evaluation vs ground truth (src/bina/metrics.py)
```

## Security
- Two customer-managed KMS keys (raw and curated), the Glue role policy grants both.
- S3 versioning on, CloudTrail multi-region trail with **data events only on raw and curated buckets**.
- Read-only role `bina-athena-reader` (assumed with MFA).

## Glue job pattern (verified behaviour)
- Input glob `.../*/*<topic>*.csv` matches exactly one folder level (`<date>/<file>`).
- `flight_date` is taken from the path, `flight_id` from the file name without `.csv`.
- `voltage_v` and `current_a` are cast to double.
- Output: `mode("overwrite").partitionBy("flight_date")`.

## Known limitation: skipped files
110 flights (8.8%) live in `<date>/sessNNN/logNNN/` (depth 3 or more) and are **silently skipped** by the glob.
`bina.paths.parse_raw_key` encodes this rule. 46 `mechanical-test` files were moved to `experiments/mechanical-test/`
so the glob does not pick them up. Fixing the glob (and making `flight_id` include the session) is deferred.
