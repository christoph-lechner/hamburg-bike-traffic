#!/usr/bin/env python3

import matplotlib.pyplot as plt
from pathlib import Path
import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from db_conn import get_db_conn
from plot_radverkehr import plot_city,plot_traffic_dailytotal
from report_radverkehr import html_report_top10

def main(outdir):
    date = '2026-03-04'
    conn = get_db_conn()

    # https://www.psycopg.org/psycopg3/docs/advanced/rows.html#row-factories
    from psycopg.rows import dict_row
    cur = conn.cursor(row_factory=dict_row)

    ### TEST: write .png file ###
    # With caller-provided axes handle, we have more control over the plot's appearance (but this means extra work)
    fig,hax = plt.subplots(figsize=(12,8))
    plot_city(hax)
    plot_traffic_dailytotal(cur, date=date, hax=hax)
    hax.set_xlabel('longitude')
    hax.set_ylabel('latitude')
    plt.savefig(outdir / 'totals.png', dpi=150, bbox_inches='tight')
    plt.show()

    html_top10 = html_report_top10()

    #####
    # Produce HTML file
    #####
    env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=select_autoescape(['html', 'xml'])
    )

    template = env.get_template('report.html')

    rendered_page = template.render(
        report_date=date,
        report_timestamp=datetime.datetime.now(),
        fn_img_totals='totals.png',
        table_top10=html_top10,
    )

    with open('report/report.html', 'w', encoding='utf-8') as f:
        f.write(rendered_page)


if __name__=='__main__':
    outdir = Path('report/')
    main(outdir)
