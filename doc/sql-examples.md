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

There are two types of counters: Those that count only traffic in one direction and those that count traffic in any direction (type: "Querschnitt", computed by summing the values of the directional counters). The latter can be identified by checking in the JSON data: `properties/richtung=="Querschnitt"`. For additional details, see [this document from the website of the City of Hamburg](https://www.hamburg.de/resource/blob/192590/f6f59a9a9e8ba55063736c36224c54fe/schematischer-aufbau-der-datenerfassung-und-aggregation-data.pdf).

Let's have a look at a set of counters in close proximity:
```
SELECT iot_id,name,richtung,longitude,latitude,COUNT(*),SUM(result) FROM bikeproj_zaehlstellen WHERE ABS(longitude-9.9470)<0.0005 GROUP BY iot_id,name,richtung,longitude,latitude LIMIT 10;
+--------+----------------------------+---------------+-----------+-----------+-------+------+
| iot_id | name                       | richtung      | longitude | latitude  | count | sum  |
|--------+----------------------------+---------------+-----------+-----------+-------+------|
| 9522   | Verkehrszählstelle 6253980 | Querschnitt   | 9.947273  | 53.548772 | 1001  | 5315 |
| 9523   | Verkehrszählstelle 6253981 | Ost nach West | 9.947275  | 53.548861 | 1001  | 2573 |
| 9524   | Verkehrszählstelle 6253982 | West nach Ost | 9.947271  | 53.548682 | 1001  | 2742 |
+--------+----------------------------+---------------+-----------+-----------+-------+------+
SELECT 3
Time: 0.058s
```

