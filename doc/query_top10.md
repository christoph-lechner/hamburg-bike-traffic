When listing yesterday's top-10 counter stations, another interesting number to report is for how long the station has been in the top-10. This is a "consecutive streak" problem. 

A more complex, but similar problem is the island problem. See for instance: https://medium.com/analytics-vidhya/sql-classic-problem-identifying-gaps-and-islands-across-overlapping-date-ranges-5681b5fcdb8

## Preparations
```
SELECT iot_id, DATE(t_start) AS date, SUM(result) AS total, ROW_NUMBER() OVER (PARTITION BY DATE(t_start) ORDER BY SUM(result) DESC) AS r
FROM bikeproj_zaehlstellen
WHERE richtung<>'Querschnitt'
GROUP BY iot_id,date
ORDER BY date ASC, total DESC, iot_id ASC;
```

In postgreSQL, to filter on `ROW_NUMBER()`, we use a CTE.
The following query gives us the daily "Top 10":
```
WITH q AS (
	SELECT iot_id, DATE(t_start) AS date, SUM(result) AS total, ROW_NUMBER() OVER (PARTITION BY DATE(t_start) ORDER BY SUM(result) DESC) AS r
	FROM bikeproj_zaehlstellen
	WHERE richtung<>'Querschnitt'
	GROUP BY iot_id,date
)
SELECT *
FROM q
WHERE r<=10
ORDER BY date ASC, total DESC, iot_id ASC;
```

Note that we do not care about the count and the rank within the top10, so these columns are omitted in the following.

```
WITH daily_top10 AS (
	WITH q AS (
		SELECT iot_id, DATE(t_start) AS date, SUM(result) AS total, ROW_NUMBER() OVER (PARTITION BY DATE(t_start) ORDER BY SUM(result) DESC) AS r
		FROM bikeproj_zaehlstellen
		WHERE richtung<>'Querschnitt'
		GROUP BY iot_id,date
	)
	SELECT date,iot_id
	FROM q
	WHERE
		-- only the daily "top 10"
		r<=10 AND
		-- only complete days (the query was developed on 2026-Feb-21)
		date<='2026-02-20'
	ORDER BY date ASC, total DESC, iot_id ASC
), most_recent_top10 AS (
	SELECT * FROM daily_top10 WHERE date='2026-02-20'
)
SELECT * FROM most_recent_top10;
```

## Step 2: Developing the Final Query
```
WITH daily_top10 AS (
	WITH q AS (
		SELECT iot_id, DATE(t_start) AS date, SUM(result) AS total, ROW_NUMBER() OVER (PARTITION BY DATE(t_start) ORDER BY SUM(result) DESC) AS r
		FROM bikeproj_zaehlstellen
		WHERE richtung<>'Querschnitt'
		GROUP BY iot_id,date
	)
	SELECT date,iot_id
	FROM q
	WHERE
		-- only the daily "top 10"
		r<=10 AND
		-- only complete days (the query was developed on 2026-Feb-21)
		date<='2026-02-20'
	ORDER BY date ASC, total DESC, iot_id ASC
), most_recent_top10 AS (
	SELECT * FROM daily_top10 WHERE date='2026-02-20'
)
SELECT r10.*,d10.*, ROW_NUMBER() OVER (PARTITION BY d10.iot_id ORDER BY d10.date DESC)
FROM most_recent_top10 r10
LEFT JOIN daily_top10 d10 ON r10.iot_id=d10.iot_id
ORDER BY d10.date DESC, r10.iot_id ASC;
```

Final query:
```
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
		-- only complete days (the query was developed on 2026-Feb-21)
		date<='2026-02-20'
	ORDER BY date ASC, total DESC, iot_id ASC
), most_recent_top10 AS (
	SELECT * FROM daily_top10 WHERE date='2026-02-20'
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
```
