#!/usr/bin/env python3
"""Print Athena verification SQL for a list of flights.

Input: a text file with one raw CSV file name per line, in the form
``<flight_date>_<HH>_<MM>_<SS>_<topic>_0.csv`` (e.g. a `mech_files.txt` listing).
Usage: python scripts/make_verification_sql.py mech_files.txt battery_status voltage_v
"""
import re
import sys

from bina.sqlgen import count_and_avg


def main(path: str, table: str, column: str) -> None:
    pat = re.compile(rf"^(\d{{4}}-\d{{2}}-\d{{2}})_(\d{{2}}_\d{{2}}_\d{{2}}_{re.escape(table)}_0)\.csv$")
    pairs = []
    with open(path) as fh:
        for line in fh:
            m = pat.match(line.strip())
            if m:
                pairs.append((m.group(1), m.group(2)))
    print(f"-- flights in list: {len(pairs)}")
    count_sql, avg_sql = count_and_avg(f"bina_db.{table}", column, pairs)
    print(count_sql + "\n\n" + avg_sql)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
