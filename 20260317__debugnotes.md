2026-03-17, 12:27

Investigation of data issues. Fresh data is no longer added to the database (also in Azure Databricks).

## Crash signature:
Running the program manually from the command line (using the `dev` database).
The JSON response was archived.
```
Traceback (most recent call last):
  File "/home/cl/work/fahrrad/./loader_radverkehr.py", line 176, in <module>
    main(ndays=args.ndays, is_scheduled=args.is_scheduled)
  File "/home/cl/work/fahrrad/./loader_radverkehr.py", line 146, in main
    ndata_from_source += process_data(data, cb=my_row_cb)
  File "/home/cl/work/fahrrad/procdata.py", line 109, in process_data
    cb(obs)
  File "/home/cl/work/fahrrad/./loader_radverkehr.py", line 99, in process_data_cb_sqlinsert
    cur.execute(
  File "/home/cl/work/fahrrad/scratch_venv/lib/python3.10/site-packages/psycopg/cursor.py", line 117, in execute
    raise ex.with_traceback(None)
psycopg.errors.UniqueViolation: duplicate key value violates unique constraint "stg_iot_id_name_str_phenomenontime_key"
DETAIL:  Key (iot_id, name, str_phenomenontime)=(12522, Verkehrszählstelle 7438910, 2026-03-14T19:45:00Z/2026-03-14T19:59:59Z) already exists.
```

## Investigation of the Issue
loader_radverkehr.py was modified:
- staging table no longer TEMPORARY
- remove UNIQUE constraint in DDL definition of staging table
- commit to DB before merge operation and exit script

SQL query analyzing staging table:
```
SELECT * FROM stg WHERE iot_id=12522 AND str_phenomenontime LIKE '2026-03-14T19:45:00Z%';
```
-> two rows are returned, which is incorrect.

### How many rows violate the condition?
Query (the columns in the `GROUP BY` are those in the `UNIQUE` constraint of the staging table).
```
SELECT
	iot_id,name,str_phenomenonTime,COUNT(*)
FROM stg
GROUP BY iot_id,name,str_phenomenonTime
HAVING COUNT(*)>1;
```
-> The only reported row is the one that originally triggered the issue appears more than one.
