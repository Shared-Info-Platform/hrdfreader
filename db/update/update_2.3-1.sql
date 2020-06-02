
-- für's Anlegen von Tabellen/Indizes
\set TBSDATANAME tbs_ :DBNAME _data
\set TBSINDEXNAME tbs_ :DBNAME _index

\encoding utf-8

\echo '=> Korrektur des Index-Namen IDX03_HRDF_DailyTimeTable_TAB'
DROP INDEX IF EXISTS IDX03_HRDF_HRDF_DailyTimeTable_TAB_TAB;
DROP INDEX IF EXISTS IDX03_HRDF_DailyTimeTable_TAB;
CREATE INDEX IDX03_HRDF_DailyTimeTable_TAB ON HRDF_DailyTimeTable_TAB (fk_eckdatenid, lineno varchar_pattern_ops) TABLESPACE :TBSINDEXNAME;

\echo '=> Korrektur der Indizes der Tabelle HRDF_FPLANFAHRTGR_TAB'
DROP INDEX IF EXISTS IDX01_HRDF_FPLANFahrtGR_TAB;
CREATE INDEX IDX01_HRDF_FPLANFahrtGR_TAB ON HRDF_FPLANFahrtGR_TAB (fk_fplanfahrtid) TABLESPACE :TBSINDEXNAME;

\echo '=> Fehlende Indizies auf fk_eckdatenid angelegt'
CREATE INDEX IDX02_HRDF_FPLANFahrtGR_TAB ON HRDF_FPLANFahrtGR_TAB (fk_eckdatenid) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_FPLANFahrtC_TAB ON HRDF_FPLANFahrtC_TAB (fk_eckdatenid) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_FPLANFahrtSH_TAB ON HRDF_FPLANFahrtSH_TAB (fk_eckdatenid) TABLESPACE :TBSINDEXNAME;