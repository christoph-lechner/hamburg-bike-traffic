#!/usr/bin/env python3

import sys
from .db_conn import get_db_conn
from .report_radverkehr import report_top10
from .my_exc import NoData
import pandas as pd
from pandas.testing import assert_frame_equal

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

    print('Analytical SQL query gave: ')
    print(df)

    # Expected result in timezone Europe/Berlin
    expected = pd.DataFrame([
        {'iot_id':2, 'total':142, 'n_days_in_top10':1},
        {'iot_id':1, 'total':11,  'n_days_in_top10':3},
        # incorrect test row (should break the test)
        # {'iot_id':4, 'total':13,  'n_days_in_top10':1}
    ])
    print('This is what we expect:')
    print(expected)

    # ignoring row order
    sort_cols = list(expected.columns)
    expected = expected.sort_values(by=sort_cols).reset_index(drop=True)
    actual =   df.sort_values(by=sort_cols).reset_index(drop=True)

    assert_frame_equal(actual, expected) # raises exception if there is a problem
    return True


if __name__=='__main__':
    ok = run_test()

    # UNIX: non-zero exit code signals error condition
    if not ok:
        sys.exit(1)
    sys.exit(0)
