#!/usr/bin/env python3

import sys
from .db_conn import get_db_conn
from .report_radverkehr import report_top10
from .my_exc import NoData

def run_test():
    # hardcoded date for tests (reflects data in test DB)
    str_date = '2026-10-03'

    conn = get_db_conn()

    # https://www.psycopg.org/psycopg3/docs/advanced/rows.html#row-factories
    from psycopg.rows import dict_row
    cur = conn.cursor(row_factory=dict_row)

    conn.execute("SET TIME ZONE 'Europe/Berlin';")

    try:
        df = report_top10(cur, date=str_date)
    except NoData:
        print(f'No data in DB for date={str_date}. Not writing report.')
        return False

    print(df)

    print('TODO: add code comparing DataFrame with expected outcome')

    return True


if __name__=='__main__':
    ok = run_test()

    # UNIX: non-zero exit code signals error condition
    if not ok:
        sys.exit(1)
    sys.exit(0)
