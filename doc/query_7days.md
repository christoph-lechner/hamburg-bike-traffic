```
WITH query_params AS (
	SELECT '2026-03-03 21:00:00+00'::timestamptz AS t0
), q AS (
	SELECT iot_id,t_start,result,EXTRACT(EPOCH FROM ((SELECT t0 FROM query_params)-t_start)) AS age_seconds
	FROM bikeproj_zaehlstellen
	WHERE
		richtung<>'Querschnitt'
		-- Filtering of data supported by index: First, coarseTemporal cut *8 days* before NOW() to curb amount of processed data
		-- 8 days: avoids any potential issues with queries submitted just after midnight (when looking back 7 days + a few hours might extend into a 8th day)
		AND t_start>=DATE((SELECT t0 FROM query_params)-8*(INTERVAL '1 DAY'))
		AND t_start<=(SELECT t0 FROM query_params)
	ORDER BY t_start DESC
)
SELECT * FROM q;
```

```
WITH query_params AS (
	SELECT '2026-03-03 21:00:00+00'::timestamptz AS t0
), q AS (
	SELECT iot_id,t_start,result,EXTRACT(EPOCH FROM ((SELECT t0 FROM query_params)-t_start)) AS age_seconds
	FROM bikeproj_zaehlstellen
	WHERE
		richtung<>'Querschnitt'
		-- Filtering of data supported by index: First, coarseTemporal cut *8 days* before NOW() to curb amount of processed data
		-- 8 days: avoids any potential issues with queries submitted just after midnight (when looking back 7 days + a few hours might extend into a 8th day)
		AND t_start>=DATE((SELECT t0 FROM query_params)-8*(INTERVAL '1 DAY'))
		
		-- Also prevents negative values of 'age_seconds'
		AND t_start<=(SELECT t0 FROM query_params)
	ORDER BY t_start DESC
), auxtbl AS (
	SELECT
		iot_id,age_seconds,
		(CASE WHEN age_seconds<=3*3600 THEN result ELSE NULL END) AS result_today,
		(CASE WHEN age_seconds >3*3600 THEN result ELSE NULL END) AS result_historic
	FROM q
	WHERE
		MOD(age_seconds,86400)<=3*3600
		AND age_seconds<=(7*86400+3*3600)
)
SELECT * FROM auxtbl;
```

## Approaching complete dev version of query
First (more-or-less complete) development version of the query. The issue is that if a new counter is added, the computation of the average value of previous 7 days is incorrect.
```
WITH query_params AS (
	SELECT '2026-02-27 09:00:00+00'::timestamptz AS t0
), q AS (
	SELECT iot_id,t_start,result,EXTRACT(EPOCH FROM ((SELECT t0 FROM query_params)-t_start)) AS age_seconds
	FROM bikeproj_zaehlstellen
	WHERE
		richtung<>'Querschnitt'
		-- Filtering of data supported by index: First, coarseTemporal cut *8 days* before NOW() to curb amount of processed data
		-- 8 days: avoids any potential issues with queries submitted just after midnight (when looking back 7 days + a few hours might extend into a 8th day)
		AND t_start>=DATE((SELECT t0 FROM query_params)-8*(INTERVAL '1 DAY'))
		
		-- Also prevents negative values of 'age_seconds'
		AND t_start<=(SELECT t0 FROM query_params)
	ORDER BY t_start DESC
), auxtbl AS (
	SELECT
		iot_id,age_seconds,
		(CASE WHEN age_seconds<=3*3600 THEN result ELSE NULL END) AS result_today,
		(CASE WHEN age_seconds >3*3600 THEN result ELSE NULL END) AS result_historic
	FROM q
	WHERE
		MOD(age_seconds,86400)<=3*3600
		AND age_seconds<=(7*86400+3*3600)
), qq AS (
	SELECT iot_id,SUM(result_today) AS s_today,SUM(result_historic) AS s_historic
	FROM auxtbl
	GROUP BY iot_id
)
SELECT *,s_today::float/(s_historic::float/7.) FROM qq WHERE s_today>=10 AND s_historic>=10 ORDER BY (s_today::float/s_historic) DESC;
```


