#!/usr/bin/env python3

import pandas as pd
import datetime
from db_conn import get_db_conn

def report_top10(cur, date = '2026-03-03'):
    # see file 'query_top10.md' for information about this query
    cur.execute(
        """
        WITH daily_top10 AS (
            WITH q AS (
                SELECT iot_id, DATE(t_start) AS date, SUM(result) AS total, ROW_NUMBER() OVER (PARTITION BY DATE(t_start) ORDER BY SUM(result) DESC) AS r
                FROM bikeproj_zaehlstellen
                WHERE richtung<>'Querschnitt'
                GROUP BY iot_id,date
            )
            SELECT date,iot_id,total
            FROM q
            WHERE
                -- only the daily "top 10"
                r<=10 AND
                -- only complete days
                date<=%s
            ORDER BY date ASC, total DESC, iot_id ASC
        ), most_recent_top10 AS (
            SELECT * FROM daily_top10 WHERE date=%s
        ), j10 AS (
            -- "joint table"
            SELECT r10.date AS date, r10.iot_id AS iot_id, d10.date AS date2, d10.iot_id AS iot_id2, ROW_NUMBER() OVER (PARTITION BY d10.iot_id ORDER BY d10.date DESC) AS n
            FROM most_recent_top10 r10
            LEFT JOIN daily_top10 d10 ON r10.iot_id=d10.iot_id
            ORDER BY d10.date DESC, r10.iot_id ASC
        ), days_in_top10 AS (
            -- For each counter: find number of days with consecutive "Top 10" listing
            SELECT iot_id,MAX(n) AS n_days_in_top10
            FROM j10
            -- KEY IDEA: Condition is met for all days of consecutive streak (looking from today/yesterday back into historic data)
            WHERE date2=date-(n-1)*(INTERVAL '1 DAY')
            GROUP BY iot_id
        )
        SELECT t.iot_id,t.total,d.n_days_in_top10
        FROM most_recent_top10 t
        INNER JOIN days_in_top10 d ON d.iot_id=t.iot_id
        ORDER BY t.total DESC;
        """,
        (date,date)
    )
    res_rows = cur.fetchall()
    if len(res_rows)==0:
        print(f'Info: No data in DB for date={date}. Not drawing plot.')
        return

    df = pd.DataFrame(res_rows)
    return(df)

def html_report_top10(*, str_date=None, verbose=False):
    """
    Expected format of string: YYYY-MM-DD
    """
    conn = get_db_conn()

    # https://www.psycopg.org/psycopg3/docs/advanced/rows.html#row-factories
    from psycopg.rows import dict_row
    cur = conn.cursor(row_factory=dict_row)

    if str_date is None:
        str_yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        str_yesterday = str_date
    df = report_top10(cur, date=str_yesterday)
    if verbose:
        print(f'Reporting Top10 for {str_yesterday}:')
        print(df)

    html_table = df.style.hide(axis='index') \
        .background_gradient(subset=['total', 'n_days_in_top10']) \
        .to_html(index=False)

    return(html_table)

if __name__=='__main__':
    html_report_top10(verbose=True)
