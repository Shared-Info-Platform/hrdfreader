
-- für's Anlegen von Tabellen/Indizes
\set TBSDATANAME tbs_ :DBNAME _data
\set TBSINDEXNAME tbs_ :DBNAME _index

\encoding utf-8

\echo '=> Erweiterung der Tabelle HRDF_TripCount_Operator_TAB'
ALTER TABLE HRDF.HRDF_TripCount_Operator_TAB ADD COLUMN lineno varchar(8) NULL;
ALTER TABLE HRDF.HRDF_TripCount_Operator_TAB ADD COLUMN categorycode varchar(8) NULL;

\echo '=> Anpassung von Indizes für die Verwendung mit Like'
DROP INDEX IF EXISTS IDX02_HRDF_tripcount_line_TAB;
CREATE INDEX IDX02_HRDF_tripcount_line_TAB ON HRDF_tripcount_line_TAB (fk_eckdatenid,lineno varchar_pattern_ops) TABLESPACE :TBSINDEXNAME;
DROP INDEX IF EXISTS IDX03_HRDF_HRDF_DailyTimeTable_TAB_TAB;
CREATE INDEX IDX03_HRDF_HRDF_DailyTimeTable_TAB_TAB ON HRDF_DailyTimeTable_TAB (fk_eckdatenid, lineno varchar_pattern_ops) TABLESPACE :TBSINDEXNAME;