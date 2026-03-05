#!/usr/bin/env python3

import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

env = Environment(
        loader=FileSystemLoader('templates'),
        autoescape=select_autoescape(['html', 'xml'])
)

template = env.get_template('report.html')

rendered_page = template.render(
    report_date='2026-03-01',
    report_timestamp=datetime.datetime.now(),
    img_totals='<img src="totals.png" width="50%">'
)

with open('report/report.html', 'w', encoding='utf-8') as f:
    f.write(rendered_page)
