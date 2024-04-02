-- für's Anlegen von Tabellen/Indizes
\set TBSDATANAME tbs_ :DBNAME _data
\set TBSINDEXNAME tbs_ :DBNAME _index

\encoding utf-8

\echo '=> Erweiterung der Tabelle HRDF_ECKDATEN_TAB um die Spalte "importstatus"'
ALTER TABLE HRDF.hrdf_eckdaten_tab ADD COLUMN importstatus varchar(20) NULL;
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.importstatus is 'Status des Imports dieser Daten (ok,running,error)';
-- setzen von bestehenden Importen auf ok
UPDATE HRDF.HRDF_ECKDATEN_TAB SET importstatus = 'ok' WHERE importstatus is NULL;
-- Sichern der zukünftigen Einträge
ALTER TABLE HRDF.HRDF_ECKDATEN_TAB ALTER COLUMN importstatus SET DEFAULT 'running';
ALTER TABLE HRDF.HRDF_ECKDATEN_TAB ALTER COLUMN importstatus SET NOT NULL;

\echo '=> Neue Tabelle zur Update-Historie der Datenbank'
CREATE TABLE HRDF_UPDATEHISTORY_TAB
(
  id				SERIAL			NOT NULL,
  databaseVersion varchar(10) NOT NULL,
  scriptName	varchar(100)	NOT NULL,
  scriptVersion varchar(10)   NOT NULL,
  description   varchar       NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_UPDATEHISTORY_TAB ADD CONSTRAINT PK_HRDF_UPDATEHISTORY_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
COMMENT ON TABLE HRDF_UPDATEHISTORY_TAB IS 'Update Historie der Datenbank';
COMMENT ON COLUMN HRDF_UPDATEHISTORY_TAB.databaseVersion is 'Dateiname der Importdatei';
COMMENT ON COLUMN HRDF_UPDATEHISTORY_TAB.scriptName is 'Name des Script, das ausgeführt wurde';
COMMENT ON COLUMN HRDF_UPDATEHISTORY_TAB.scriptVersion is 'Version des Script, das ausgeführt wurde';
COMMENT ON COLUMN HRDF_UPDATEHISTORY_TAB.description is 'Beschreibung der Änderungen';