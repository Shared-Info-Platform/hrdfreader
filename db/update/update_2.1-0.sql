
-- für's Anlegen von Tabellen/Indizes
\set TBSDATANAME tbs_ :DBNAME _data
\set TBSINDEXNAME tbs_ :DBNAME _index


\echo '=> Neue Tabellen für den HRDF-Importer'
\echo '=> Tabelle HRDF_BFKOORD_TAB'
CREATE TABLE HRDF_BFKOORD_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid	integer	NOT NULL,
  stopno				integer	NOT NULL,
  longitude_geo	numeric	NOT NULL,
  latitude_geo		numeric	NOT NULL,
  altitude_geo		integer	NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_BFKOORD_TAB ADD CONSTRAINT PK_HRDF_BFKOORD_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
COMMENT ON TABLE HRDF_BFKOORD_TAB IS 'Geo-Koordinaten einer Haltestelle (BFKOORD)';
COMMENT ON COLUMN HRDF_BFKOORD_TAB.stopno is 'Eindeutige Nr der Haltestelle';
COMMENT ON COLUMN HRDF_BFKOORD_TAB.longitude_geo is 'Längengrad der Haltestelle (x-Koordinate)';
COMMENT ON COLUMN HRDF_BFKOORD_TAB.latitude_geo is 'Breitengrad der Haltestelle (y-Koordinate)';
COMMENT ON COLUMN HRDF_BFKOORD_TAB.altitude_geo is 'Geographische Höhe der Haltestelle (z-Koordinate, Meter über NN)';
CREATE INDEX IDX01_HRDF_BFKOORD_TAB ON HRDF_BFKOORD_TAB (fk_eckdatenid, stopno) TABLESPACE :TBSINDEXNAME;

\echo '=> Tabelle HRDF_DURCHBI_TAB'
CREATE TABLE HRDF_DURCHBI_TAB
(
  id				SERIAL			NOT NULL,
  fk_eckdatenid	integer		NOT NULL,
  tripno1			integer		NOT NULL,
  operationalno1	varchar(6)	NOT NULL,
  laststopno1		integer		NOT NULL,
  tripno2			integer		NOT NULL,
  operationalno2	varchar(6)	NOT NULL,
  bitfieldno		integer		NOT NULL,
  firststopno2		integer		NULL,
  attribute			varchar(1)	NULL,
  comment			varchar		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_DURCHBI_TAB ADD CONSTRAINT PK_HRDF_DURCHBI_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
COMMENT ON TABLE HRDF_DURCHBI_TAB IS 'Durchbindung einer Fahrt (DURCHBI)';
COMMENT ON COLUMN HRDF_DURCHBI_TAB.tripno1 IS 'Fahrtnummer 1';
COMMENT ON COLUMN HRDF_DURCHBI_TAB.operationalno1 IS 'Verwaltung für Fahrt 1';
COMMENT ON COLUMN HRDF_DURCHBI_TAB.laststopno1 IS 'letzter Halt der Fahrt 1';
COMMENT ON COLUMN HRDF_DURCHBI_TAB.tripno2 IS 'Fahrtnummer 2';
COMMENT ON COLUMN HRDF_DURCHBI_TAB.operationalno2 IS 'Verwaltung für Fahrt 2';
COMMENT ON COLUMN HRDF_DURCHBI_TAB.bitfieldno IS 'Verkehrstagebitfeldnummer';
COMMENT ON COLUMN HRDF_DURCHBI_TAB.firststopno2 IS 'erster Halt der Fahrt 2';
COMMENT ON COLUMN HRDF_DURCHBI_TAB.attribute IS 'Attribut zur Markierung der Durchbindung';
COMMENT ON COLUMN HRDF_DURCHBI_TAB.comment IS 'Kommentar';
CREATE INDEX IDX01_HRDF_DURCHBI_TAB ON HRDF_DURCHBI_TAB (fk_eckdatenid, tripno1, operationalno1) TABLESPACE :TBSINDEXNAME;

\echo '=> Tabelle HRDF_UMSTEIGB_TAB'
CREATE TABLE HRDF_UMSTEIGB_TAB
(
  id				SERIAL			NOT NULL,
  fk_eckdatenid	integer		NOT NULL,
  stopno				integer		NOT NULL,
  transfertime1	integer		NOT NULL,
  transfertime2	integer		NOT NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_UMSTEIGB_TAB ADD CONSTRAINT PK_HRDF_UMSTEIGB_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
COMMENT ON TABLE HRDF_UMSTEIGB_TAB IS 'Haltestellenbezogene Umsteigezeiten (UMSTEIGB)';
COMMENT ON COLUMN HRDF_UMSTEIGB_TAB.stopno IS 'Eindeutige Nr der Haltestelle';
COMMENT ON COLUMN HRDF_UMSTEIGB_TAB.transfertime1 IS 'Umsteigezeit in Minuten zwischen IC und IC max 60 Min';
COMMENT ON COLUMN HRDF_UMSTEIGB_TAB.transfertime2 IS 'Umsteigezeit in Minuten zwischen allen anderen Gattungskombinationen';
CREATE INDEX IDX01_HRDF_UMSTEIGB_TAB ON HRDF_UMSTEIGB_TAB (fk_eckdatenid, stopno) TABLESPACE :TBSINDEXNAME;

\echo '=> Tabelle HRDF_BFPRIOS_TAB'
CREATE TABLE HRDF_BFPRIOS_TAB
(
  id				SERIAL			NOT NULL,
  fk_eckdatenid	integer		NOT NULL,
  stopno				integer		NOT NULL,
  transferprio		integer		NOT NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_BFPRIOS_TAB ADD CONSTRAINT PK_HRDF_BFPRIOS_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
COMMENT ON TABLE HRDF_BFPRIOS_TAB IS 'Bahnhofsumsteigeprioritäten (BFPRIOS)';
COMMENT ON COLUMN HRDF_BFPRIOS_TAB.stopno IS 'Eindeutige Nr der Haltestelle';
COMMENT ON COLUMN HRDF_BFPRIOS_TAB.transferprio IS 'Umsteigepriorität der Haltestelle (0-16 => 0 ist höchste Prio)';
CREATE INDEX IDX01_HRDF_BFPRIOS_TAB ON HRDF_BFPRIOS_TAB (fk_eckdatenid, stopno) TABLESPACE :TBSINDEXNAME;

\echo '=> Tabelle HRDF_METABHF_TAB'
CREATE TABLE HRDF_METABHF_TAB
(
  id				SERIAL			NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  stopnoFrom			integer		NOT NULL,
  stopnoTo				integer		NOT NULL,
  transfertimeMin		integer		NOT NULL,
  transfertimeSec		integer		NULL,
  attributecode		varchar[]	NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_METABHF_TAB ADD CONSTRAINT PK_HRDF_METABHF_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
COMMENT ON TABLE HRDF_METABHF_TAB IS 'Übergangsbeziehung zwischen Haltestellen (METABHF)';
COMMENT ON COLUMN HRDF_METABHF_TAB.stopnoFrom IS 'Eindeutige Nr der Haltestelle von';
COMMENT ON COLUMN HRDF_METABHF_TAB.stopnoTo IS 'Eindeutige Nr der Haltestelle nach';
COMMENT ON COLUMN HRDF_METABHF_TAB.transfertimeMin IS 'Dauer des Übergangs in Minuten';
COMMENT ON COLUMN HRDF_METABHF_TAB.transfertimeSec IS 'Zusätzliche Dauer in Sekunden';
COMMENT ON COLUMN HRDF_METABHF_TAB.attributecode IS 'Beliebige Attributcodes';
CREATE INDEX IDX01_HRDF_METABHF_TAB ON HRDF_METABHF_TAB (fk_eckdatenid, stopnoFrom) TABLESPACE :TBSINDEXNAME;

\echo '=> Tabelle HRDF_METABHFGRUPPE_TAB'
CREATE TABLE HRDF_METABHFGRUPPE_TAB
(
  id				SERIAL			NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  stopgroupno			integer		NOT NULL,
  stopmember			integer[]	NOT NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_METABHFGRUPPE_TAB ADD CONSTRAINT PK_HRDF_METABHFGRUPPE_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
COMMENT ON TABLE HRDF_METABHFGRUPPE_TAB IS 'Haltestellengruppen (METABHF Gruppen)';
COMMENT ON COLUMN HRDF_METABHFGRUPPE_TAB.stopgroupno IS 'Eindeutige Nr der Haltestellengruppe';
COMMENT ON COLUMN HRDF_METABHFGRUPPE_TAB.stopmember IS 'Liste der zugehörigen Haltestellen';
CREATE INDEX IDX01_HRDF_METABHFGRUPPE_TAB ON HRDF_METABHFGRUPPE_TAB (fk_eckdatenid, stopgroupno) TABLESPACE :TBSINDEXNAME;

\echo '=> Erweiterungen der Tagesfahrplantabelle'
ALTER TABLE HRDF_DailyTimeTable_TAB ADD COLUMN longitude_geo numeric NULL;
ALTER TABLE HRDF_DailyTimeTable_TAB ADD COLUMN latitude_geo numeric NULL;
ALTER TABLE HRDF_DailyTimeTable_TAB ADD COLUMN altitude_geo integer NULL;
ALTER TABLE HRDF_DailyTimeTable_TAB ADD COLUMN transfertime1 integer NULL;
ALTER TABLE HRDF_DailyTimeTable_TAB ADD COLUMN transfertime2 integer NULL;
ALTER TABLE HRDF_DailyTimeTable_TAB ADD COLUMN transferprio integer NULL;
ALTER TABLE HRDF_DailyTimeTable_TAB ADD COLUMN tripno_continued integer NULL;
ALTER TABLE HRDF_DailyTimeTable_TAB ADD COLUMN operationalno_continued varchar(6) NULL;
ALTER TABLE HRDF_DailyTimeTable_TAB ADD COLUMN stopno_continued integer NULL;
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.longitude_geo is 'Längengrad der Haltestelle (x-Koordinate)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.latitude_geo is 'Breitengrad der Haltestelle (y-Koordinate)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.altitude_geo is 'Geographische Höhe der Haltestelle (z-Koordinate, Meter über NN)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.transfertime1 IS 'Umsteigezeit in Minuten zwischen IC und IC max 60 Min';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.transfertime2 IS 'Umsteigezeit in Minuten zwischen allen anderen Gattungskombinationen';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.transferprio IS 'Umsteigepriorität der Haltestelle (0-16 => 0 ist höchste Prio)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.tripno_continued IS 'FahrtNr für Durchbindung; fährt weiter als';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.operationalno_continued	IS 'Verwaltungsnummer für Durchbindung; fährt weiter als';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.stopno_continued	IS 'HaltestellenNr für Durchbindung; kann unterschiedlich zum Halt sein';

