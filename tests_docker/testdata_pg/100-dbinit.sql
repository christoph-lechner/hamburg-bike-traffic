-- Remarks:
-- 1) _h is UNIQUE hash value computed in the ingestion pipeline. Here we just use unique dummy values
-- 2) Only assigning fields that are required for the test
INSERT INTO bikeproj_zaehlstellen (_h, iot_id, richtung, t_start, t_end, result) VALUES ('1', 1, 'beispiel_richtung', '2026-10-01 23:45:00+02:00', '2026-10-01 23:59:59+02:00', 3);
INSERT INTO bikeproj_zaehlstellen (_h, iot_id, richtung, t_start, t_end, result) VALUES ('2', 1, 'beispiel_richtung', '2026-10-02 00:15:00+02:00', '2026-10-02 00:29:59+02:00', 10);
INSERT INTO bikeproj_zaehlstellen (_h, iot_id, richtung, t_start, t_end, result) VALUES ('3', 1, 'beispiel_richtung', '2026-10-02 23:45:00+02:00', '2026-10-02 23:59:59+02:00', 7);
INSERT INTO bikeproj_zaehlstellen (_h, iot_id, richtung, t_start, t_end, result) VALUES ('4', 1, 'beispiel_richtung', '2026-10-03 00:15:00+02:00', '2026-10-03 00:29:59+02:00', 5);
INSERT INTO bikeproj_zaehlstellen (_h, iot_id, richtung, t_start, t_end, result) VALUES ('5', 1, 'beispiel_richtung', '2026-10-03 00:30:00+02:00', '2026-10-03 00:44:59+02:00', 6);
INSERT INTO bikeproj_zaehlstellen (_h, iot_id, richtung, t_start, t_end, result) VALUES ('6', 2, 'beispiel_richtung', '2026-10-03 12:15:00+02:00', '2026-10-03 12:29:59+02:00', 42);
INSERT INTO bikeproj_zaehlstellen (_h, iot_id, richtung, t_start, t_end, result) VALUES ('7', 2, 'beispiel_richtung', '2026-10-03 14:15:00+02:00', '2026-10-03 14:29:59+02:00', 100);

-- Expected result
-- $ ./run_test.sh 
--    iot_id  total  n_days_in_top10
-- 0       2    142                1
-- 1       1     11                3
