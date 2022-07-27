-- für's Anlegen von Tabellen/Indizes
\set TBSDATANAME tbs_ :DBNAME _data
\set TBSINDEXNAME tbs_ :DBNAME _index

\encoding utf-8

\echo '=> Neue Indizes für BahnhofGleis-View'
CREATE INDEX IDX02_HRDF_BAHNHOF_TAB ON HRDF_BAHNHOF_TAB (fk_eckdatenid, stopno) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_GLEIS_TAB ON HRDF_GLEIS_TAB (fk_eckdatenid, stopno) TABLESPACE :TBSINDEXNAME;

INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.4-5', 'update_2.4-5.sql', '1', 'Neue Indizes für BahnhofGleis-View');