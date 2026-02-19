What is the earliest data point we have for each counter station?
```
SELECT iot_id,MIN(t_start) FROM bikeproj_zaehlstellen GROUP BY iot_id ORDER BY iot_id;
```

```
SELECT DATE(t_start) AS date,SUM(result) AS total FROM bikeproj_zaehlstellen GROUP BY date ORDER BY date;
```

```
SELECT DATE(timestamp) AS date, COUNT(*) FROM bikeproj_weather GROUP BY date ORDER BY date;
```

There are two types of counters: Those that count only traffic in one direction and those that count traffic in any direction (type: "Querschnitt", computed by summing the values of the directional counters). The latter can be identified by checking in the JSON data:
properties/richtung=="Querschnitt"
```
SELECT iot_id,name,longitude,latitude,COUNT(*),SUM(result) FROM bikeproj_zaehlstellen WHERE ABS(longitude-9.9470)<0.0005 GROUP BY iot_id,name,longitude,latitude LIMIT 10;
+--------+----------------------------+-----------+-----------+-------+------+
| iot_id | name                       | longitude | latitude  | count | sum  |
|--------+----------------------------+-----------+-----------+-------+------|
| 9522   | Verkehrszählstelle 6253980 | 9.947273  | 53.548772 | 1735  | 8004 |
| 9523   | Verkehrszählstelle 6253981 | 9.947275  | 53.548861 | 1735  | 4043 |
| 9524   | Verkehrszählstelle 6253982 | 9.947271  | 53.548682 | 1735  | 3961 |
+--------+----------------------------+-----------+-----------+-------+------+
SELECT 3
Time: 0.111s
```


Relative comparison of total bike traffic counted on two days (one day without snow, one day with snow):
```
WITH qq AS (
	WITH q AS (
		SELECT iot_id,DATE(t_start) AS date,latitude,longitude,SUM(result) AS s FROM bikeproj_zaehlstellen
		WHERE DATE(t_start)='2026-02-11' OR DATE(t_start)='2026-02-16'
		GROUP BY iot_id,date,latitude,longitude
		ORDER BY iot_id,date
	)
	SELECT
		iot_id,
		SUM((CASE WHEN date='2026-02-11' THEN s END)) AS s1,
		SUM((CASE WHEN date='2026-02-16' THEN s END)) AS s2
	FROM q
	GROUP BY iot_id
)
SELECT iot_id,s1,s2,s2/s1 AS r
FROM qq
WHERE s1>0 AND s1 IS NOT NULL AND s2 IS NOT NULL;
```

