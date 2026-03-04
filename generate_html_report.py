#!/usr/bin/env python3

import matplotlib.pyplot as plt
from pathlib import Path
from db_conn import get_db_conn
from plot_radverkehr import plot_city,plot_traffic_dailytotal

def main(outdir):
    conn = get_db_conn()

    # https://www.psycopg.org/psycopg3/docs/advanced/rows.html#row-factories
    from psycopg.rows import dict_row
    cur = conn.cursor(row_factory=dict_row)

    ### TEST: write .png file ###
    # With caller-provided axes handle, we have more control over the plot's appearance (but this means extra work)
    fig,hax = plt.subplots(figsize=(12,8))
    plot_city(hax)
    plot_traffic_dailytotal(cur, date='2026-03-04', hax=hax)
    hax.set_xlabel('longitude')
    hax.set_ylabel('latitude')
    plt.savefig(outdir / 'totals.png', dpi=150, bbox_inches='tight')
    plt.show()


if __name__=='__main__':
    outdir = Path('report/')
    main(outdir)
