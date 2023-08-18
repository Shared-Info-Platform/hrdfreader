-- für's Anlegen von Tabellen/Indizes
\set TBSDATANAME tbs_ :DBNAME _data
\set TBSINDEXNAME tbs_ :DBNAME _index

\encoding utf-8

\echo '=> Neue Tabelle für die Linieninformationen'
CREATE TABLE HRDF_LINIE_TAB
(
  id 			SERIAL			NOT NULL,
  fk_eckdatenid	integer	NOT NULL,
  line_index varchar(8) NOT NULL,
  line_key varchar(256) NOT NULL,
  number_intern	varchar(256) NULL,
  name_short		varchar(256) NULL,
  name_short_index		varchar(128)	NULL,
  name_long	varchar(256) NULL,
  name_long_index varchar(256) NULL,
  color_font varchar(20) NULL,
  color_back varchar(20) NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_LINIE_TAB ADD CONSTRAINT PK_HRDF_LINIE_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_linie_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_LINIE_TAB IS 'Erweiterte Liniendaten';
COMMENT ON COLUMN HRDF_LINIE_TAB.line_index IS 'Linien-Index';
COMMENT ON COLUMN HRDF_LINIE_TAB.line_key IS 'Linienschluessel';
COMMENT ON COLUMN HRDF_LINIE_TAB.number_intern IS 'Interne Liniennummer';
COMMENT ON COLUMN HRDF_LINIE_TAB.name_short IS 'Kurzname';
COMMENT ON COLUMN HRDF_LINIE_TAB.name_short_index IS 'Index für Kurzname';
COMMENT ON COLUMN HRDF_LINIE_TAB.name_long IS 'Langname';
COMMENT ON COLUMN HRDF_LINIE_TAB.name_long_index IS 'Index für Langname';
COMMENT ON COLUMN HRDF_LINIE_TAB.color_font IS 'Schriftfarbe';
COMMENT ON COLUMN HRDF_LINIE_TAB.color_back IS 'Hintergrundfarbe';

\echo '=> Neue Indizes'
CREATE INDEX IDX01_HRDF_LINIE_TAB ON HRDF_LINIE_TAB (fk_eckdatenid, line_index) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_LINIE_TAB ON HRDF_LINIE_TAB (fk_eckdatenid, line_key) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX03_HRDF_LINIE_TAB ON HRDF_LINIE_TAB (fk_eckdatenid, name_short) TABLESPACE :TBSINDEXNAME;

INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.4-6', 'update_2.4-6.sql', '1', 'Neue Tabelle und Indizes für Linien-Informationen');