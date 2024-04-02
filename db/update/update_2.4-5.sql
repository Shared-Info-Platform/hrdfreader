-- für's Anlegen von Tabellen/Indizes
\set TBSDATANAME tbs_ :DBNAME _data
\set TBSINDEXNAME tbs_ :DBNAME _index

\encoding utf-8

\echo '=> Neue Indizes für BahnhofGleis-View'
CREATE INDEX IDX02_HRDF_BAHNHOF_TAB ON HRDF_BAHNHOF_TAB (fk_eckdatenid, stopno) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_GLEIS_TAB ON HRDF_GLEIS_TAB (fk_eckdatenid, stopno) TABLESPACE :TBSINDEXNAME;
DROP INDEX IF EXISTS IDX07_HRDF_HRDF_DailyTimeTable_TAB_TAB;
DROP INDEX IF EXISTS IDX07_HRDF_DailyTimeTable_TAB;
CREATE INDEX IDX07_HRDF_DailyTimeTable_TAB ON HRDF_DailyTimeTable_TAB (fk_eckdatenid, operatingday, stopident) TABLESPACE :TBSINDEXNAME;
ALTER INDEX IDX01_HRDF_HRDF_DailyTimeTable_TAB_TAB RENAME TO IDX01_HRDF_DailyTimeTable_TAB;
ALTER INDEX IDX02_HRDF_HRDF_DailyTimeTable_TAB_TAB RENAME TO IDX02_HRDF_DailyTimeTable_TAB;
ALTER INDEX IDX03_HRDF_HRDF_DailyTimeTable_TAB_TAB RENAME TO IDX03_HRDF_DailyTimeTable_TAB;
ALTER INDEX IDX04_HRDF_HRDF_DailyTimeTable_TAB_TAB RENAME TO IDX04_HRDF_DailyTimeTable_TAB;
ALTER INDEX IDX05_HRDF_HRDF_DailyTimeTable_TAB_TAB RENAME TO IDX05_HRDF_DailyTimeTable_TAB;
ALTER INDEX IDX06_HRDF_HRDF_DailyTimeTable_TAB_TAB RENAME TO IDX06_HRDF_DailyTimeTable_TAB;

ALTER SEQUENCE IF EXISTS hrdf_attribut_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_bahnhof_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_bfkoord_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_bfprios_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_bitfeld_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_dailytimetable_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_durchbi_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_eckdaten_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrt_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrta_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrtc_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrtg_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrtgr_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrti_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrtl_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrtlaufweg_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrtr_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrtsh_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrtve_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_gleis_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_infotext_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_linesperstop_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_metabhf_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_metabhfgruppe_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_richtung_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_tripcount_line_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_tripcount_operator_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_umsteigb_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_updatehistory_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_vdvbetreibermapping_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_vdvlinienmapping_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_zugart_tab_id_seq	CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_zugartkategorie_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_zugartklasse_tab_id_seq CYCLE;
ALTER SEQUENCE IF EXISTS hrdf_zugartoption_tab_id_seq CYCLE;

\echo '=> Neue Tabelle für die Haltestellen-Fahrt-Statistik'
CREATE TABLE HRDF_StopTripCountStats_TAB
(
  id 			SERIAL			NOT NULL,
  operatingday	timestamp with time zone	NOT NULL,
  stopgroupno	integer			NOT NULL,
  stopident		varchar(100)	NOT NULL,
  stopname		varchar(500)	NOT NULL,
  departureCnt	integer			NOT NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_StopTripCountStats_TAB ADD CONSTRAINT PK_HRDF_StopTripCountStats_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_stoptripcountstats_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_StopTripCountStats_TAB IS 'Statistikdaten zu Fahrten pro Haltestellen';
COMMENT ON COLUMN HRDF_StopTripCountStats_TAB.operatingday IS 'Betriebsttag';
COMMENT ON COLUMN HRDF_StopTripCountStats_TAB.stopgroupno IS 'Haltestellenngruppe (Metabhfgruppe)';
COMMENT ON COLUMN HRDF_StopTripCountStats_TAB.stopident IS 'Haltestellenkennung';
COMMENT ON COLUMN HRDF_StopTripCountStats_TAB.stopname IS 'Name der Haltestelle';
COMMENT ON COLUMN HRDF_StopTripCountStats_TAB.departureCnt IS 'Anzahl der Abfahrten an der Haltestelle';


INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.4-5', 'update_2.4-5.sql', '2', 'Neue Indizes für BahnhofGleis-View und DailyTimeTable; Sequence cycle; Haltestellenstatistik');