-- für's Anlegen von Tabellen/Indizes
\set TBSDATANAME tbs_ :DBNAME _data
\set TBSINDEXNAME tbs_ :DBNAME _index

\encoding utf-8

\echo '=> Neue VDV-Mapping-Tabellen'
/*
\brief  table for VDV Linien-Mapping
*/
CREATE TABLE HRDF_VDVLinienMapping_TAB
(
  id			SERIAL		NOT NULL,
  operationalno	varchar(6)	NOT NULL,
  lineno		varchar(8)	NOT NULL,
  linienID		varchar(20)	NULL,
  linienText	varchar(50) NULL,
  creationdatetime timestamp with time zone NOT NULL DEFAULT(now())
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_VDVLinienMapping_TAB ADD CONSTRAINT PK_HRDF_VDVLinienMapping_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
COMMENT ON TABLE HRDF_VDVLinienMapping_TAB IS 'Mapping-Tabelle für Linien';
COMMENT ON COLUMN HRDF_VDVLinienMapping_TAB.operationalno IS 'HRDF-Verwaltungsnummer';
COMMENT ON COLUMN HRDF_VDVLinienMapping_TAB.lineno IS 'HRDF-Liniennummer';
COMMENT ON COLUMN HRDF_VDVLinienMapping_TAB.linienID IS 'Zu verwendende LinienID (technischer Linienschlüssel) ohne Betreiberkennung im VDV';
COMMENT ON COLUMN HRDF_VDVLinienMapping_TAB.linienText IS 'Zu verwendender LinienText im VDV';
COMMENT ON COLUMN HRDF_VDVLinienMapping_TAB.creationdatetime IS 'Zeitpunkt der Erstellung des Eintrags';
CREATE INDEX IDX01_HRDF_VDVLinienMapping_TAB ON HRDF_VDVLinienMapping_TAB (operationalno, lineno) TABLESPACE :TBSINDEXNAME;

/*
\brief  table for VDV Betreiber-Mapping
*/
CREATE TABLE HRDF_VDVBetreiberMapping_TAB
(
  id				SERIAL		NOT NULL,
  operationalno		varchar(6)	NOT NULL,
  UICLaendercode	varchar(5)	NOT NULL,
  GONr				varchar(20)	NOT NULL,
  GOAbk				varchar(20) NULL,
  creationdatetime timestamp with time zone NOT NULL DEFAULT(now())
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_VDVBetreiberMapping_TAB ADD CONSTRAINT PK_HRDF_VDVBetreiberMapping_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
COMMENT ON TABLE HRDF_VDVBetreiberMapping_TAB IS 'Mapping-Tabelle für Betreiber';
COMMENT ON COLUMN HRDF_VDVBetreiberMapping_TAB.operationalno IS 'HRDF-Verwaltungsnummer';
COMMENT ON COLUMN HRDF_VDVBetreiberMapping_TAB.UICLaendercode IS 'UIC Laendercode';
COMMENT ON COLUMN HRDF_VDVBetreiberMapping_TAB.GONr IS 'Geschäftsorganisations NR';
COMMENT ON COLUMN HRDF_VDVBetreiberMapping_TAB.GOAbk IS 'Geschäftsorganisations Abkürzung';
COMMENT ON COLUMN HRDF_VDVBetreiberMapping_TAB.creationdatetime IS 'Zeitpunkt der Erstellung des Eintrags';
CREATE INDEX IDX01_HRDF_VDVBetreiberMapping_TAB ON HRDF_VDVBetreiberMapping_TAB (operationalno) TABLESPACE :TBSINDEXNAME;



INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.4-2', 'update_2.4-2.sql', '1', 'Neue VDV-Mapping-Tabellen');