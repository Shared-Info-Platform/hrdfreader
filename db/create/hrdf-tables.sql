/*
	SQL script to create hrdf - tables 
*/

\set TBSDATANAME tbs_ :DBNAME _data
\set TBSINDEXNAME tbs_ :DBNAME _index

/*
\brief	table that holds the update history of database
*/
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
ALTER SEQUENCE IF EXISTS hrdf_updatehistory_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_UPDATEHISTORY_TAB IS 'Update Historie der Datenbank';
COMMENT ON COLUMN HRDF_UPDATEHISTORY_TAB.databaseVersion is 'Dateiname der Importdatei';
COMMENT ON COLUMN HRDF_UPDATEHISTORY_TAB.scriptName is 'Name des Script, das ausgeführt wurde';
COMMENT ON COLUMN HRDF_UPDATEHISTORY_TAB.scriptVersion is 'Version des Script, das ausgeführt wurde';
COMMENT ON COLUMN HRDF_UPDATEHISTORY_TAB.description is 'Beschreibung der Änderungen';

/*
\brief	table for file ECKDATEN (with extensions)
*/
CREATE TABLE HRDF_ECKDATEN_TAB
(
  id				SERIAL			NOT NULL,
  importFileName	varchar(100)	NOT NULL,
  importDateTime	timestamp with time zone NOT NULL,
  validFrom			date			NOT NULL,
  validTo			date			NOT NULL,
  descriptionhrdf	varchar			NULL,
  description		varchar			NULL,
  creationdatetime	timestamp with time zone NULL,
  hrdfversion		varchar(10)		NULL,
  exportsystem		varchar(20)		NULL,
  deleteFlag		bool			NULL,
  inactive		bool			NULL,
  ttgenerated		date[]			NULL,
  importstatus		varchar(20)		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_ECKDATEN_TAB ADD CONSTRAINT PK_HRDF_ECKDATEN_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_eckdaten_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_ECKDATEN_TAB IS 'Eckdaten der Fahrplanperiode';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.importFileName is '+ Dateiname der Importdatei';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.importDateTime is '+ Startzeitpunkt des Imports';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.validFrom is 'erster Gueltigkeitstag des Fahrplans';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.validTo is 'letzter Gueltigkeitstag des Fahrplans';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.descriptionhrdf is 'Fahrplanbezeichnung in HRDF';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.description is '+ Bezeichnung des Fahrplans';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.creationdatetime is '+ Erzeugungsdatum mit Zeit';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.hrdfversion is '+ Version der HRDF-Daten';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.exportsystem is '+ System von dem die HRDF-Daten exportiert wurden';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.deleteFlag is '+ Markierung, dass die Daten gelöscht werden sollen';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.inactive is 'Markierung, dass die Daten nicht verwendet werden sollen';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.ttgenerated is 'Array mit den Tagen, für die die Tagesfahrpläne bereits generiert wurden';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.importstatus is 'Status des Imports dieser Daten (ok,running,error)';

/*
\brief	table for file BITFELD
*/
CREATE TABLE HRDF_BITFELD_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  bitfieldno		integer		NOT NULL,
  bitfield			varchar(96)	NOT NULL,
  bitfieldextend	varchar(380) NOT NULL,
  bitfieldarray		date[]		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_BITFELD_TAB ADD CONSTRAINT PK_HRDF_BITFELD_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_bitfeld_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_BITFELD_TAB IS 'Verkehrstagesdefinitionen der Fahrten (BITFELD)';
COMMENT ON COLUMN HRDF_BITFELD_TAB.bitfieldno is 'Eindeutige Nr der Verkehrstagesdefinition';
COMMENT ON COLUMN HRDF_BITFELD_TAB.bitfield is 'Verkehrstagesdefinition als Bitfeld (hrdf-hexdezimalcodiert)';
COMMENT ON COLUMN HRDF_BITFELD_TAB.bitfieldextend is '+ Verkehrstagesdefinition als Bitfeld (bitcodiert bereinigt)';
COMMENT ON COLUMN HRDF_BITFELD_TAB.bitfieldarray is '+ Bitfeld als array of date';
CREATE INDEX IDX01_HRDF_BITFELD_TAB ON HRDF_BITFELD_TAB (fk_eckdatenid, bitfieldno) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_BITFELD_TAB ON HRDF_BITFELD_TAB USING GIN (bitfieldarray) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file BAHNHOF
*/
CREATE TABLE HRDF_BAHNHOF_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  stopno			integer		NOT NULL,
  transportUnion	varchar(3)	NULL,
  stopname			varchar(30) NOT NULL,
  stopnamelong		varchar(50)	NULL,
  stopnameshort		varchar(50) NULL,
  stopnamealias		varchar(50) NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_BAHNHOF_TAB ADD CONSTRAINT PK_HRDF_BAHNHOF_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_bahnhof_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_BAHNHOF_TAB IS 'Namen für Bahnhöfe/Haltestellen (BAHNHOF)';
COMMENT ON COLUMN HRDF_BAHNHOF_TAB.stopno is 'Nummer der Haltestelle';
COMMENT ON COLUMN HRDF_BAHNHOF_TAB.stopname is 'Name der Haltestelle';
COMMENT ON COLUMN HRDF_BAHNHOF_TAB.stopnamelong is 'Name lang der Haltestelle';
COMMENT ON COLUMN HRDF_BAHNHOF_TAB.stopnameshort is 'Abkürzung der Haltestelle';
COMMENT ON COLUMN HRDF_BAHNHOF_TAB.stopnamealias is 'Synonym / Alias der Haltestelle';
CREATE INDEX IDX01_HRDF_BAHNHOF_TAB ON HRDF_BAHNHOF_TAB (fk_eckdatenid) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_BAHNHOF_TAB ON HRDF_BAHNHOF_TAB (fk_eckdatenid, stopno) TABLESPACE :TBSINDEXNAME;


/*
\brief	table for file GLEIS
*/
CREATE TABLE HRDF_GLEIS_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  stopno			integer		NOT NULL,
  tripno			integer		NOT NULL,
  operationalno		varchar(6)	NOT NULL,
  stoppointtext		varchar(8)  NOT NULL,
  stoppointtime		integer		NULL,
  bitfieldno		integer		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_GLEIS_TAB ADD CONSTRAINT PK_HRDF_GLEIS_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_gleis_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_GLEIS_TAB IS 'Verkehrstagesdefinitionen der Fahrten (BITFELD)';
COMMENT ON COLUMN HRDF_GLEIS_TAB.stopno is 'Nummer der Haltestelle';
COMMENT ON COLUMN HRDF_GLEIS_TAB.tripno is 'Fahrtnummer';
COMMENT ON COLUMN HRDF_GLEIS_TAB.operationalno is 'Verwaltungsnummer zur Unterscheidung von Fahrten mit gleicher Nr';
COMMENT ON COLUMN HRDF_GLEIS_TAB.stoppointtext is 'Haltepositionstext';
COMMENT ON COLUMN HRDF_GLEIS_TAB.stoppointtime is 'Zeit zur Erkennung ob Gültig für Ankunft oder Abfahrt';
COMMENT ON COLUMN HRDF_GLEIS_TAB.bitfieldno is 'Eindeutige Nr der Verkehrstagesdefinition';
CREATE INDEX IDX01_HRDF_GLEIS_TAB ON HRDF_GLEIS_TAB (fk_eckdatenid, tripno, operationalno) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_GLEIS_TAB ON HRDF_GLEIS_TAB (fk_eckdatenid, stopno) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file ZUGART
*/
CREATE TABLE HRDF_ZUGART_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  categorycode		varchar(3)	NOT NULL,
  classno			integer		NOT NULL,
  tariffgroup		varchar(1) 	NOT NULL,
  outputcontrol		integer		NOT NULL,
  categorydesc		varchar(8)	NOT NULL,
  extracharge		integer		NOT NULL,
  flags				varchar(1)	NOT NULL,
  categoryimage		integer		NULL,
  categoryno		integer		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_ZUGART_TAB ADD CONSTRAINT PK_HRDF_ZUGART_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_zugart_tab_id_seq	CYCLE;
COMMENT ON TABLE HRDF_ZUGART_TAB IS 'Verkehrsmittel bzw. Gattung';
COMMENT ON COLUMN HRDF_ZUGART_TAB.categorycode IS 'Code der Gattung';
COMMENT ON COLUMN HRDF_ZUGART_TAB.classno IS 'ProduktklassenNr der Gattung (0-13)';
COMMENT ON COLUMN HRDF_ZUGART_TAB.tariffgroup IS 'Tarifgruppe der Gattung (A-H)';
COMMENT ON COLUMN HRDF_ZUGART_TAB.outputcontrol IS 'Ausgabesteuerung (0=Gattung und Nummer, 1=Gattung, 2=Nummer, 3=keine Ausgabe, +4=Betreiber statt Gattung)';
COMMENT ON COLUMN HRDF_ZUGART_TAB.categorydesc IS 'Gattungsbezeichnung,di ausgegeben wird';
COMMENT ON COLUMN HRDF_ZUGART_TAB.extracharge IS 'Zuschlag (0=Zuschlagfrei, 1=Zuschlagpflicht nach Kontext, 2=Zuschlagpflicht)';
COMMENT ON COLUMN HRDF_ZUGART_TAB.flags IS 'Flags (N=Nahverkehr, B=Schiff)';
COMMENT ON COLUMN HRDF_ZUGART_TAB.categoryimage IS 'Nr für Gattungsbildernamen (0-999)';
COMMENT ON COLUMN HRDF_ZUGART_TAB.categoryno IS 'Nr für sprachabhängigen Gattungslangnamen (0-999). Auch Text möglich - gilt dann für alle Sprachen';
CREATE INDEX IDX01_HRDF_ZUGART_TAB ON HRDF_ZUGART_TAB (fk_eckdatenid, categorycode) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_ZUGART_TAB ON HRDF_ZUGART_TAB (fk_eckdatenid) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file ZUGART - Produktklasse
*/
CREATE TABLE HRDF_ZUGARTKlasse_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  classno			integer		NOT NULL,
  languagecode		varchar(2)	NOT NULL,
  classtext		varchar 	NOT NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_ZUGARTKlasse_TAB ADD CONSTRAINT PK_HRDF_ZUGARTKlasse_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_zugartklasse_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_ZUGARTKlasse_TAB IS 'Produktklassen für Gattungen';
COMMENT ON COLUMN HRDF_ZUGARTKlasse_TAB.classno IS 'Nr der Produktklasse (0-13)';
COMMENT ON COLUMN HRDF_ZUGARTKlasse_TAB.languagecode IS '+ Sprache des Produktklasse (Kürzel entsprechend der Dateiendung)';
COMMENT ON COLUMN HRDF_ZUGARTKlasse_TAB.classtext IS 'Text zur Produktklasse';
CREATE INDEX IDX01_HRDF_ZUGARTKlasse_TAB ON HRDF_ZUGARTKlasse_TAB (fk_eckdatenid, classno, languagecode) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file ZUGART - Kategorie
*/
CREATE TABLE HRDF_ZUGARTKategorie_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  categoryno		integer		NOT NULL,
  languagecode		varchar(2)	NOT NULL,
  categorytext		varchar 	NOT NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_ZUGARTKategorie_TAB ADD CONSTRAINT PK_HRDF_ZUGARTKategorie_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_zugartkategorie_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_ZUGARTKategorie_TAB IS 'Bezeichnungen für Gattungen';
COMMENT ON COLUMN HRDF_ZUGARTKategorie_TAB.categoryno IS 'Nr der Gattung/Kategorie';
COMMENT ON COLUMN HRDF_ZUGARTKategorie_TAB.languagecode IS '+ Sprache der Gattungsbezeichnung (Kürzel entsprechend der Dateiendung)';
COMMENT ON COLUMN HRDF_ZUGARTKategorie_TAB.categorytext IS 'Gattungsbeschreibung/namen';
CREATE INDEX IDX01_HRDF_ZUGARTKategorie_TAB ON HRDF_ZUGARTKategorie_TAB (fk_eckdatenid, categoryno, languagecode) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file ZUGART - Option (Suche)
*/
CREATE TABLE HRDF_ZUGARTOption_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  optionno			integer		NOT NULL,
  languagecode		varchar(2)	NOT NULL,
  optiontext		varchar 	NOT NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_ZUGARTOption_TAB ADD CONSTRAINT PK_HRDF_ZUGARTOption_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_zugartoption_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_ZUGARTOption_TAB IS 'Optionen für die Suche';
COMMENT ON COLUMN HRDF_ZUGARTOption_TAB.optionno IS 'Nr der Option (10-14)';
COMMENT ON COLUMN HRDF_ZUGARTOption_TAB.languagecode IS '+ Sprache der Optionsbezeichnung (Kürzel entsprechend der Dateiendung)';
COMMENT ON COLUMN HRDF_ZUGARTOption_TAB.optiontext IS 'Text der Option';
CREATE INDEX IDX01_HRDF_ZUGARTOption_TAB ON HRDF_ZUGARTOption_TAB (fk_eckdatenid, optionno, languagecode) TABLESPACE :TBSINDEXNAME;



/*
\brief	table for file RICHTUNG
*/
CREATE TABLE HRDF_RICHTUNG_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  directioncode		varchar(7)	NOT NULL,
  directiontext		varchar(50) NOT NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_RICHTUNG_TAB ADD CONSTRAINT PK_HRDF_RICHTUNG_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_richtung_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_RICHTUNG_TAB IS 'Verkehrsmittel bzw. Gattung';
COMMENT ON COLUMN HRDF_RICHTUNG_TAB.directioncode IS 'Code der Richtung';
COMMENT ON COLUMN HRDF_RICHTUNG_TAB.directiontext IS 'Ausgabetext der Richtung';
CREATE INDEX IDX01_HRDF_HRDF_RICHTUNG_TAB ON HRDF_RICHTUNG_TAB (fk_eckdatenid, directioncode) TABLESPACE :TBSINDEXNAME;


/*
\brief	table for file ATTRIBUT
*/
CREATE TABLE HRDF_ATTRIBUT_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  attributecode		varchar(2)	NOT NULL,
  languagecode		varchar(2)	NOT NULL,
  stopcontext		integer 	NOT NULL,
  outputprio		integer		NOT NULL,
  outputpriosort	integer		NOT NULL,
  attributetext		varchar(70)	NOT NULL,
  outputforsection	varchar(2)	NOT NULL,
  outputforcomplete varchar(2)	NOT NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_ATTRIBUT_TAB ADD CONSTRAINT PK_HRDF_ATTRIBUT_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_attribut_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_ATTRIBUT_TAB IS 'Spezielle Attribute einer Fahrt/Fahrtabschnitt';
COMMENT ON COLUMN HRDF_ATTRIBUT_TAB.attributecode IS 'Code des Attributes';
COMMENT ON COLUMN HRDF_ATTRIBUT_TAB.languagecode IS '+ Sprache des Attributs (Kürzel entsprechend der Dateiendung)';
COMMENT ON COLUMN HRDF_ATTRIBUT_TAB.stopcontext IS 'Haltestellenzugehörigkeit (0=Fahrtabschnitt, 1=Abfahrtshaltestelle, 2=Ankunftshaltestelle)';
COMMENT ON COLUMN HRDF_ATTRIBUT_TAB.outputprio IS 'Ausgabepriorität, kleine Werte sind höher Prior (0-999)';
COMMENT ON COLUMN HRDF_ATTRIBUT_TAB.outputpriosort IS 'Ausgabepriosortierung, bei gleicher Prio => Ausgabe nach Sortierung';
COMMENT ON COLUMN HRDF_ATTRIBUT_TAB.attributetext IS 'Text des Attributs (Abschlusszeichen # entfällt)';
COMMENT ON COLUMN HRDF_ATTRIBUT_TAB.outputforsection IS 'Attributcode für Ausgabe einer Teilstrecke)';
COMMENT ON COLUMN HRDF_ATTRIBUT_TAB.outputforcomplete IS 'Attributcode für Ausgabe auf der Vollstrecke)';
CREATE INDEX IDX01_HRDF_ATTRIBUT_TAB ON HRDF_ATTRIBUT_TAB (fk_eckdatenid, languagecode) TABLESPACE :TBSINDEXNAME;


/*
\brief	table for file INFOTEXT
*/
CREATE TABLE HRDF_INFOTEXT_TAB
(
  id				SERIAL			NOT NULL,
  fk_eckdatenid		integer			NOT NULL,
  infotextno		integer			NOT NULL,
  languagecode		varchar(2)		NOT NULL,
  infotext			varchar(1000)	NOT NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_INFOTEXT_TAB ADD CONSTRAINT PK_HRDF_INFOTEXT_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_infotext_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_INFOTEXT_TAB IS 'Im Fahrplan verwendete Infotexte';
COMMENT ON COLUMN HRDF_INFOTEXT_TAB.infotextno IS 'Nr. des Infotext';
COMMENT ON COLUMN HRDF_INFOTEXT_TAB.languagecode IS '+ Sprache des Infotext (Kürzel entsprechend der Dateiendung)';
COMMENT ON COLUMN HRDF_INFOTEXT_TAB.infotext IS 'Infotext';
CREATE INDEX IDX01_HRDF_INFOTEXT_TAB ON HRDF_INFOTEXT_TAB (fk_eckdatenid, infotextno, languagecode) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file BFKOORD
*/
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
ALTER SEQUENCE IF EXISTS hrdf_bfkoord_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_BFKOORD_TAB IS 'Geo-Koordinaten einer Haltestelle (BFKOORD)';
COMMENT ON COLUMN HRDF_BFKOORD_TAB.stopno is 'Eindeutige Nr der Haltestelle';
COMMENT ON COLUMN HRDF_BFKOORD_TAB.longitude_geo is 'Längengrad der Haltestelle (x-Koordinate)';
COMMENT ON COLUMN HRDF_BFKOORD_TAB.latitude_geo is 'Breitengrad der Haltestelle (y-Koordinate)';
COMMENT ON COLUMN HRDF_BFKOORD_TAB.altitude_geo is 'Geographische Höhe der Haltestelle (z-Koordinate, Meter über NN)';
CREATE INDEX IDX01_HRDF_BFKOORD_TAB ON HRDF_BFKOORD_TAB (fk_eckdatenid, stopno) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file DURCHBI
*/
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
ALTER SEQUENCE IF EXISTS hrdf_durchbi_tab_id_seq CYCLE;
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


/*
\brief	table for file UMSTEIGB
*/
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
ALTER SEQUENCE IF EXISTS hrdf_umsteigb_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_UMSTEIGB_TAB IS 'Haltestellenbezogene Umsteigezeiten (UMSTEIGB)';
COMMENT ON COLUMN HRDF_UMSTEIGB_TAB.stopno IS 'Eindeutige Nr der Haltestelle';
COMMENT ON COLUMN HRDF_UMSTEIGB_TAB.transfertime1 IS 'Umsteigezeit in Minuten zwischen IC und IC max 60 Min';
COMMENT ON COLUMN HRDF_UMSTEIGB_TAB.transfertime2 IS 'Umsteigezeit in Minuten zwischen allen anderen Gattungskombinationen';
CREATE INDEX IDX01_HRDF_UMSTEIGB_TAB ON HRDF_UMSTEIGB_TAB (fk_eckdatenid, stopno) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file BFPRIOS
*/
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
ALTER SEQUENCE IF EXISTS hrdf_bfprios_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_BFPRIOS_TAB IS 'Bahnhofsumsteigeprioritäten (BFPRIOS)';
COMMENT ON COLUMN HRDF_BFPRIOS_TAB.stopno IS 'Eindeutige Nr der Haltestelle';
COMMENT ON COLUMN HRDF_BFPRIOS_TAB.transferprio IS 'Umsteigepriorität der Haltestelle (0-16 => 0 ist höchste Prio)';
CREATE INDEX IDX01_HRDF_BFPRIOS_TAB ON HRDF_BFPRIOS_TAB (fk_eckdatenid, stopno) TABLESPACE :TBSINDEXNAME;


/*
\brief	table for file METABHF
*/
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
ALTER SEQUENCE IF EXISTS hrdf_metabhf_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_METABHF_TAB IS 'Übergangsbeziehung zwischen Haltestellen (METABHF)';
COMMENT ON COLUMN HRDF_METABHF_TAB.stopnoFrom IS 'Eindeutige Nr der Haltestelle von';
COMMENT ON COLUMN HRDF_METABHF_TAB.stopnoTo IS 'Eindeutige Nr der Haltestelle nach';
COMMENT ON COLUMN HRDF_METABHF_TAB.transfertimeMin IS 'Dauer des Übergangs in Minuten';
COMMENT ON COLUMN HRDF_METABHF_TAB.transfertimeSec IS 'Zusätzliche Dauer in Sekunden';
COMMENT ON COLUMN HRDF_METABHF_TAB.attributecode IS 'Beliebige Attributcodes';
CREATE INDEX IDX01_HRDF_METABHF_TAB ON HRDF_METABHF_TAB (fk_eckdatenid, stopnoFrom) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file METABHF-GRUPPE
*/
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
ALTER SEQUENCE IF EXISTS hrdf_metabhfgruppe_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_METABHFGRUPPE_TAB IS 'Haltestellengruppen (METABHF Gruppen)';
COMMENT ON COLUMN HRDF_METABHFGRUPPE_TAB.stopgroupno IS 'Eindeutige Nr der Haltestellengruppe';
COMMENT ON COLUMN HRDF_METABHFGRUPPE_TAB.stopmember IS 'Liste der zugehörigen Haltestellen';
CREATE INDEX IDX01_HRDF_METABHFGRUPPE_TAB ON HRDF_METABHFGRUPPE_TAB (fk_eckdatenid, stopgroupno) TABLESPACE :TBSINDEXNAME;

/* Tabellen zur Datei FPLAN */

/*
\brief	table for file FPLAN lines beginning with *Z / *KW / *T
*/
CREATE TABLE HRDF_FPLANFahrt_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  triptype			varchar(2)	NOT NULL,
  tripno			integer		NOT NULL,
  operationalno		varchar(6)	NOT NULL,
  tripversion		integer		NULL,
  cyclecount		integer		NULL,
  cycletimemin 		integer		NULL,
  triptimemin		integer		NULL,
  cycletimesec		integer		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_FPLANFahrt_TAB ADD CONSTRAINT PK_HRDF_FPLANFahrt_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrt_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_FPLANFahrt_TAB IS 'Einträge der FPLAN-Datei beginnend mit *Z / *KW / *T';
COMMENT ON COLUMN HRDF_FPLANFahrt_TAB.triptype is 'Art der Fahrt (Z, KW, T)';
COMMENT ON COLUMN HRDF_FPLANFahrt_TAB.tripno is 'Fahrtnummer';
COMMENT ON COLUMN HRDF_FPLANFahrt_TAB.operationalno is 'Verwaltungsnummer zur Unterscheidung von Fahrten mit gleicher Nr';
COMMENT ON COLUMN HRDF_FPLANFahrt_TAB.tripversion is '+ Nummer der Variante des Verkehrsmittel (Info+)';
COMMENT ON COLUMN HRDF_FPLANFahrt_TAB.cyclecount is 'Taktanzahl der noch folgenden Takte; triptype=Z';
COMMENT ON COLUMN HRDF_FPLANFahrt_TAB.cycletimemin is 'Taktzeit in Minuten (Abstand zwischen zwei Fahrten); triptype=Z';
COMMENT ON COLUMN HRDF_FPLANFahrt_TAB.triptimemin is 'Fahrtzeitraum; triptype=T';
COMMENT ON COLUMN HRDF_FPLANFahrt_TAB.cycletimesec is 'Taktzeit in Sekunden(Abstand zwischen zwei Fahrten); triptype=T';
CREATE INDEX IDX01_HRDF_FPLANFahrt_TAB ON HRDF_FPLANFahrt_TAB (fk_eckdatenid, tripno, operationalno) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_FPLANFahrt_TAB ON HRDF_FPLANFahrt_TAB (fk_eckdatenid) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX03_HRDF_FPLANFahrt_TAB ON HRDF_FPLANFahrt_TAB (fk_eckdatenid, tripno, operationalno) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file FPLAN lines beginning with *A VE
*/
CREATE TABLE HRDF_FPLANFahrtVE_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  fk_fplanfahrtid   integer		NOT NULL,
  fromStop			integer		NULL,
  toStop			integer		NULL,
  bitfieldno		integer		NULL,
  deptimeFrom		integer		NULL,
  arrtimeTo			integer		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_FPLANFahrtVE_TAB ADD CONSTRAINT PK_HRDF_FPLANFahrtVE_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrtve_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_FPLANFahrtVE_TAB IS 'Einträge der FPLAN-Datei beginnend mit *A VE';
COMMENT ON COLUMN HRDF_FPLANFahrtVE_TAB.fromStop is 'HaltestellenNr ab der die Verkehrstage gelten';
COMMENT ON COLUMN HRDF_FPLANFahrtVE_TAB.toStop is 'HaltestellenNr bis zu der die Verkehrstage gelten';
COMMENT ON COLUMN HRDF_FPLANFahrtVE_TAB.bitfieldno is 'Eindeutige Nr der Verkehrstagesdefinition';
COMMENT ON COLUMN HRDF_FPLANFahrtVE_TAB.deptimeFrom is 'Abfahrtszeitpunkt der Ab-Haltestelle';
COMMENT ON COLUMN HRDF_FPLANFahrtVE_TAB.arrtimeTo is 'Ankunftszeitpunkt der Bis-Haltestelle';
CREATE INDEX IDX01_HRDF_FPLANFahrtVE_TAB ON HRDF_FPLANFahrtVE_TAB (fk_fplanfahrtid) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_FPLANFahrtVE_TAB ON HRDF_FPLANFahrtVE_TAB (fk_eckdatenid, bitfieldno) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX03_HRDF_FPLANFahrtVE_TAB ON HRDF_FPLANFahrtVE_TAB (fk_eckdatenid) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file FPLAN lines beginning with *G
*/
CREATE TABLE HRDF_FPLANFahrtG_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  fk_fplanfahrtid   integer		NOT NULL,
  categorycode		varchar(3)	NOT NULL,
  fromStop			integer		NULL,
  toStop			integer		NULL,
  deptimeFrom		integer		NULL,
  arrtimeTo			integer		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_FPLANFahrtG_TAB ADD CONSTRAINT PK_HRDF_FPLANFahrtG_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrtg_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_FPLANFahrtG_TAB IS 'Einträge der FPLAN-Datei beginnend mit *G';
COMMENT ON COLUMN HRDF_FPLANFahrtG_TAB.categorycode is 'Code der Gattung';
COMMENT ON COLUMN HRDF_FPLANFahrtG_TAB.fromStop is 'HaltestellenNr ab der die Gattung gültig ist';
COMMENT ON COLUMN HRDF_FPLANFahrtG_TAB.toStop is 'HaltestellenNr bis zu der die Gattung gültig ist';
COMMENT ON COLUMN HRDF_FPLANFahrtG_TAB.deptimeFrom is 'Abfahrtszeitpunkt der Ab-Haltestelle';
COMMENT ON COLUMN HRDF_FPLANFahrtG_TAB.arrtimeTo is 'Ankunftszeitpunkt der Bis-Haltestelle';
CREATE INDEX IDX01_HRDF_FPLANFahrtG_TAB ON HRDF_FPLANFahrtG_TAB (fk_fplanfahrtid) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_FPLANFahrtG_TAB ON HRDF_FPLANFahrtG_TAB (fk_eckdatenid) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file FPLAN lines beginning with *A
*/
CREATE TABLE HRDF_FPLANFahrtA_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  fk_fplanfahrtid   integer		NOT NULL,
  attributecode		varchar(2)	NOT NULL,
  fromStop			integer		NULL,
  toStop			integer		NULL,
  bitfieldno		integer		NULL,
  deptimeFrom		integer		NULL,
  arrtimeTo		integer		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_FPLANFahrtA_TAB ADD CONSTRAINT PK_HRDF_FPLANFahrtA_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrta_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_FPLANFahrtA_TAB IS 'Einträge der FPLAN-Datei beginnend mit *A';
COMMENT ON COLUMN HRDF_FPLANFahrtA_TAB.attributecode is 'Attributscode';
COMMENT ON COLUMN HRDF_FPLANFahrtA_TAB.fromStop is 'HaltestellenNr ab der das Attribut gültig ist';
COMMENT ON COLUMN HRDF_FPLANFahrtA_TAB.toStop is 'HaltestellenNr bis zu der das Attribut gültig ist';
COMMENT ON COLUMN HRDF_FPLANFahrtA_TAB.bitfieldno is 'Eindeutige Nr der Verkehrstagesdefinition';
COMMENT ON COLUMN HRDF_FPLANFahrtA_TAB.deptimeFrom is 'Abfahrtszeitpunkt der Ab-Haltestelle';
COMMENT ON COLUMN HRDF_FPLANFahrtA_TAB.arrtimeTo is 'Ankunftszeitpunkt der Bis-Haltestelle';
CREATE INDEX IDX01_HRDF_FPLANFahrtA_TAB ON HRDF_FPLANFahrtA_TAB (fk_fplanfahrtid) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_FPLANFahrtA_TAB ON HRDF_FPLANFahrtA_TAB (fk_eckdatenid) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file FPLAN lines beginning with *R
*/
CREATE TABLE HRDF_FPLANFahrtR_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  fk_fplanfahrtid   integer		NOT NULL,
  directionShort	varchar(1)	NULL,
  directionCode		varchar(7)	NULL,
  fromStop			integer		NULL,
  toStop			integer		NULL,
  deptimeFrom		integer		NULL,
  arrtimeTo			integer		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_FPLANFahrtR_TAB ADD CONSTRAINT PK_HRDF_FPLANFahrtR_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrtr_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_FPLANFahrtR_TAB IS 'Einträge der FPLAN-Datei beginnend mit *R';
COMMENT ON COLUMN HRDF_FPLANFahrtR_TAB.directionShort is 'Kennung der Richtung (H,R)';
COMMENT ON COLUMN HRDF_FPLANFahrtR_TAB.directionCode is 'Richtungscode';
COMMENT ON COLUMN HRDF_FPLANFahrtR_TAB.fromStop is 'HaltestellenNr ab der die Richtung gültig ist';
COMMENT ON COLUMN HRDF_FPLANFahrtR_TAB.toStop is 'HaltestellenNr bis zu der die Richtung gültig ist';
COMMENT ON COLUMN HRDF_FPLANFahrtR_TAB.deptimeFrom is 'Abfahrtszeitpunkt der Ab-Haltestelle';
COMMENT ON COLUMN HRDF_FPLANFahrtR_TAB.arrtimeTo is 'Ankunftszeitpunkt der Bis-Haltestelle';
CREATE INDEX IDX01_HRDF_FPLANFahrtR_TAB ON HRDF_FPLANFahrtR_TAB (fk_fplanfahrtid) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_FPLANFahrtR_TAB ON HRDF_FPLANFahrtR_TAB (fk_eckdatenid) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file FPLAN lines beginning with *I
*/
CREATE TABLE HRDF_FPLANFahrtI_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  fk_fplanfahrtid   integer		NOT NULL,
  infotextcode		varchar(2)	NOT NULL,
  infotextno		integer		NOT NULL,
  fromStop			integer		NULL,
  toStop			integer		NULL,
  bitfieldno		integer		NULL,
  deptimeFrom		integer		NULL,
  arrtimeTo			integer		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_FPLANFahrtI_TAB ADD CONSTRAINT PK_HRDF_FPLANFahrtI_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrti_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_FPLANFahrtI_TAB IS 'Einträge der FPLAN-Datei beginnend mit *I';
COMMENT ON COLUMN HRDF_FPLANFahrtI_TAB.infotextcode is 'Code des Infotext';
COMMENT ON COLUMN HRDF_FPLANFahrtI_TAB.infotextno is 'Nr. des Infotext';
COMMENT ON COLUMN HRDF_FPLANFahrtI_TAB.fromStop is 'HaltestellenNr ab der der Infotext gültig ist';
COMMENT ON COLUMN HRDF_FPLANFahrtI_TAB.toStop is 'HaltestellenNr bis zu der der Infotext gültig ist';
COMMENT ON COLUMN HRDF_FPLANFahrtI_TAB.bitfieldno is 'Eindeutige Nr der Verkehrstagesdefinition';
COMMENT ON COLUMN HRDF_FPLANFahrtI_TAB.deptimeFrom is 'Abfahrtszeitpunkt der Ab-Haltestelle';
COMMENT ON COLUMN HRDF_FPLANFahrtI_TAB.arrtimeTo is 'Ankunftszeitpunkt der Bis-Haltestelle';
CREATE INDEX IDX01_HRDF_FPLANFahrtI_TAB ON HRDF_FPLANFahrtI_TAB (fk_fplanfahrtid) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_FPLANFahrtI_TAB ON HRDF_FPLANFahrtI_TAB (fk_eckdatenid) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file FPLAN lines beginning with *L
*/
CREATE TABLE HRDF_FPLANFahrtL_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  fk_fplanfahrtid   integer		NOT NULL,
  lineno			varchar(8)	NULL,
  lineindex varchar(8) NULL,
  fromStop			integer		NULL,
  toStop			integer		NULL,
  deptimeFrom		integer		NULL,
  arrtimeTo			integer		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_FPLANFahrtL_TAB ADD CONSTRAINT PK_HRDF_FPLANFahrtL_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrtl_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_FPLANFahrtL_TAB IS 'Einträge der FPLAN-Datei beginnend mit *L';
COMMENT ON COLUMN HRDF_FPLANFahrtL_TAB.lineno is 'Liniennummer';
COMMENT ON COLUMN HRDF_FPLANFAHRTL_TAB.lineindex is 'Index der Linie im LINIE-File';
COMMENT ON COLUMN HRDF_FPLANFahrtL_TAB.fromStop is 'HaltestellenNr ab der die Linie gültig ist';
COMMENT ON COLUMN HRDF_FPLANFahrtL_TAB.toStop is 'HaltestellenNr bis zu der die Linie gültig ist';
COMMENT ON COLUMN HRDF_FPLANFahrtL_TAB.deptimeFrom is 'Abfahrtszeitpunkt der Ab-Haltestelle';
COMMENT ON COLUMN HRDF_FPLANFahrtL_TAB.arrtimeTo is 'Ankunftszeitpunkt der Bis-Haltestelle';
CREATE INDEX IDX01_HRDF_FPLANFahrtL_TAB ON HRDF_FPLANFahrtL_TAB (fk_fplanfahrtid) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_FPLANFahrtL_TAB ON HRDF_FPLANFahrtL_TAB (fk_eckdatenid) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file FPLAN lines beginning with *SH
*/
CREATE TABLE HRDF_FPLANFahrtSH_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  fk_fplanfahrtid   integer		NOT NULL,
  stop				integer		NOT NULL,
  bitfieldno		integer		NULL,
  deptimeFrom		integer		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_FPLANFahrtSH_TAB ADD CONSTRAINT PK_HRDF_FPLANFahrtSH_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrtsh_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_FPLANFahrtSH_TAB IS 'Einträge der FPLAN-Datei beginnend mit *SH (saisonaler Halt)';
COMMENT ON COLUMN HRDF_FPLANFahrtSH_TAB.stop is 'HaltestellenNr für den die saisonale Verkehrstage gelten. Sie werden nur an diesen Tagen angefahren';
COMMENT ON COLUMN HRDF_FPLANFahrtSH_TAB.bitfieldno is 'Eindeutige Nr der Verkehrstagesdefinition';
COMMENT ON COLUMN HRDF_FPLANFahrtSH_TAB.deptimeFrom is 'Abfahrtszeitpunkt der Ab-Haltestelle';
CREATE INDEX IDX01_HRDF_FPLANFahrtSH_TAB ON HRDF_FPLANFahrtSH_TAB (fk_fplanfahrtid) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_FPLANFahrtSH_TAB ON HRDF_FPLANFahrtSH_TAB (fk_eckdatenid) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file FPLAN lines beginning with *GR
*/
CREATE TABLE HRDF_FPLANFahrtGR_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  fk_fplanfahrtid   integer		NOT NULL,
  borderStop		integer		NOT NULL,
  prevStop			integer		NULL,
  nextStop			integer		NULL,
  deptimePrev		integer		NULL,
  arrtimeNext		integer		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_FPLANFahrtGR_TAB ADD CONSTRAINT PK_HRDF_FPLANFahrtGR_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrtgr_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_FPLANFahrtGR_TAB IS 'Einträge der FPLAN-Datei beginnend mit *GR';
COMMENT ON COLUMN HRDF_FPLANFahrtGR_TAB.borderStop is 'Virtuelle Grenzpunktnummer';
COMMENT ON COLUMN HRDF_FPLANFahrtGR_TAB.prevStop is 'HaltestellenNr vor dem Grenzpunkt';
COMMENT ON COLUMN HRDF_FPLANFahrtGR_TAB.nextStop is 'HaltestellenNr nach dem Grenzpunkt';
COMMENT ON COLUMN HRDF_FPLANFahrtGR_TAB.deptimePrev is 'Abfahrtszeitpunkt der Vorgänger-Haltestelle';
COMMENT ON COLUMN HRDF_FPLANFahrtGR_TAB.arrtimeNext is 'Ankunftszeitpunkt der Nachfolger-Haltestelle';
CREATE INDEX IDX01_HRDF_FPLANFahrtGR_TAB ON HRDF_FPLANFahrtGR_TAB (fk_fplanfahrtid) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_FPLANFahrtGR_TAB ON HRDF_FPLANFahrtGR_TAB (fk_eckdatenid) TABLESPACE :TBSINDEXNAME;


/*
\brief	table for file FPLAN lines beginning with *C (CI/CO)
*/
CREATE TABLE HRDF_FPLANFahrtC_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  fk_fplanfahrtid   integer		NOT NULL,
  checkinTime		integer		NULL,
  checkoutTime		integer		NULL,
  fromStop			integer		NULL,
  toStop			integer		NULL,
  deptimeFrom		integer		NULL,
  arrtimeTo			integer		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_FPLANFahrtC_TAB ADD CONSTRAINT PK_HRDF_FPLANFahrtC_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrtc_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_FPLANFahrtC_TAB IS 'Einträge der FPLAN-Datei beginnend mit *C (CI/CO)';
COMMENT ON COLUMN HRDF_FPLANFahrtC_TAB.checkinTime is 'Eincheckzeit in Minuten';
COMMENT ON COLUMN HRDF_FPLANFahrtC_TAB.checkoutTime is 'Auscheckzeit in Minuten';
COMMENT ON COLUMN HRDF_FPLANFahrtC_TAB.fromStop is 'HaltestellenNr ab der die Ein-/Auscheckzeiten gelten';
COMMENT ON COLUMN HRDF_FPLANFahrtC_TAB.toStop is 'HaltestellenNr bis zu die Ein-/Auscheckzeiten gelten';
COMMENT ON COLUMN HRDF_FPLANFahrtC_TAB.deptimeFrom is 'Abfahrtszeitpunkt der Ab-Haltestelle';
COMMENT ON COLUMN HRDF_FPLANFahrtC_TAB.arrtimeTo is 'Ankunftszeitpunkt der Bis-Haltestelle';
CREATE INDEX IDX01_HRDF_FPLANFahrtC_TAB ON HRDF_FPLANFahrtC_TAB (fk_fplanfahrtid) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_FPLANFahrtC_TAB ON HRDF_FPLANFahrtC_TAB (fk_eckdatenid) TABLESPACE :TBSINDEXNAME;


/*
\brief	table for file FPLAN data-lines
*/
CREATE TABLE HRDF_FPLANFahrtLaufweg_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  fk_fplanfahrtid   integer		NOT NULL,
  stopno			integer		NOT NULL,
  stopname			varchar(21)	NULL,
  sequenceno		integer		NOT NULL,
  arrtime			integer		NULL,
  deptime			integer		NULL,
  tripno			integer		NULL,
  operationalno		varchar(6)	NULL,
  ontripsign		varchar(1)	NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_FPLANFahrtLaufweg_TAB ADD CONSTRAINT PK_HRDF_FPLANFahrtLaufweg_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_fplanfahrtlaufweg_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_FPLANFahrtLaufweg_TAB IS 'Laufweg einer Fahrt';
COMMENT ON COLUMN HRDF_FPLANFahrtLaufweg_TAB.stopno IS 'HaltestelleNr';
COMMENT ON COLUMN HRDF_FPLANFahrtLaufweg_TAB.stopname IS 'Haltestellenname';
COMMENT ON COLUMN HRDF_FPLANFahrtLaufweg_TAB.sequenceno IS '+ ReihenfolgenNr';
COMMENT ON COLUMN HRDF_FPLANFahrtLaufweg_TAB.arrtime IS 'Ankunftszeit an der Haltestelle';
COMMENT ON COLUMN HRDF_FPLANFahrtLaufweg_TAB.deptime IS 'Abfahrtszeit an der Haltestelle';
COMMENT ON COLUMN HRDF_FPLANFahrtLaufweg_TAB.tripno IS 'FahrtNr ab der Haltestelle';
COMMENT ON COLUMN HRDF_FPLANFahrtLaufweg_TAB.operationalno IS 'VerwaltungsNr. ab der Haltestelle';
COMMENT ON COLUMN HRDF_FPLANFahrtLaufweg_TAB.ontripsign IS 'Anzeige der Haltestelle auf dem Laufschild';
CREATE INDEX IDX01_HRDF_FPLANFahrtLaufweg_TAB ON HRDF_FPLANFahrtLaufweg_TAB (fk_fplanfahrtid, sequenceno) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_FPLANFahrtLaufweg_TAB ON HRDF_FPLANFahrtLaufweg_TAB (fk_eckdatenid, fk_fplanfahrtid, sequenceno) TABLESPACE :TBSINDEXNAME;


/*
\brief	table for file LINIE
*/
CREATE TABLE HRDF_LINIE_TAB
(
  id 			SERIAL			NOT NULL,
  fk_eckdatenid	integer	NOT NULL,
  line_key varchar(256) NOT NULL,
  number_intern	varchar(256) NULL,
  name_short		varchar(256) NULL,
  name_short_index		varchar(20)	NULL,
  name_long	varchar(256) NULL,
  name_long_index varchar(20) NULL,
  color_font varchar(20) NULL,
  color_back varchar(20) NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_LINIE_TAB ADD CONSTRAINT PK_HRDF_LINIE_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_linie_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_LINIE_TAB IS 'Erweiterte Liniendaten';
COMMENT ON COLUMN HRDF_LINIE_TAB.line_key IS 'Linienschluessel';
COMMENT ON COLUMN HRDF_LINIE_TAB.number_intern IS 'Interne Liniennummer';
COMMENT ON COLUMN HRDF_LINIE_TAB.name_short IS 'Kurzname';
COMMENT ON COLUMN HRDF_LINIE_TAB.name_short_index IS 'Index für Kurzname';
COMMENT ON COLUMN HRDF_LINIE_TAB.name_long IS 'Langname';
COMMENT ON COLUMN HRDF_LINIE_TAB.name_long_index IS 'Index für Langname';
COMMENT ON COLUMN HRDF_LINIE_TAB.color_font IS 'Schriftfarbe';
COMMENT ON COLUMN HRDF_LINIE_TAB.color_back IS 'Hintergrundfarbe';
CREATE INDEX IDX01_HRDF_LINIE_TAB ON HRDF_LINIE_TAB (fk_eckdatenid, line_key) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_LINIE_TAB ON HRDF_LINIE_TAB (fk_eckdatenid, name_short) TABLESPACE :TBSINDEXNAME;


/*
\brief	table for daily timetable
*/
CREATE TABLE HRDF_DailyTimeTable_TAB
(
  id				SERIAL			NOT NULL,
  fk_eckdatenid		integer			NOT NULL,
  tripident			varchar(100)	NOT NULL,
  tripno			integer			NOT NULL,
  operationalno		varchar(6)		NOT NULL,
  tripversion		integer			NOT NULL,
  operatingday		timestamp with time zone NOT NULL,
  stopsequenceno	integer			NOT NULL,
  stopident			varchar(100)	NOT NULL,
  stopname			varchar(500)	NULL,
  stoppointident	varchar(100)	NULL,
  stoppointname		varchar(500)	NULL,
  arrstoppointtext	varchar(8)		NULL,
  depstoppointtext  varchar(8)		NULL,
  arrdatetime		timestamp with time zone NULL,
  depdatetime		timestamp with time zone NULL,
  noentry			bool			NULL,
  noexit			bool			NULL,
  categorycode		varchar(3)		NULL,
  classno			integer			NULL,
  categoryno		integer			NULL,
  lineno			varchar(8)		NULL,
  directionShort	varchar(1)		NULL,
  directiontext		varchar(50)		NULL,
  attributecode		varchar[]	NULL,
  attributetext_de	varchar[]	NULL,
  attributetext_fr	varchar[]	NULL,
  attributetext_en	varchar[]	NULL,
  attributetext_it	varchar[]	NULL,
  infotextcode		varchar[]	NULL,
  infotext_de		varchar[]	NULL,
  infotext_fr		varchar[]	NULL,
  infotext_en		varchar[]	NULL,
  infotext_it		varchar[]	NULL,
  longitude_geo	numeric		NULL,
  latitude_geo		numeric		NULL,
  altitude_geo		integer		NULL,
  transfertime1	integer		NULL,
  transfertime2	integer		NULL,
  transferprio		integer		NULL,
  tripno_continued integer		NULL,
  operationalno_continued	varchar(6)	NULL,
  stopno_continued	integer NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_DailyTimeTable_TAB ADD CONSTRAINT PK_HRDF_DailyTimeTable_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_dailytimetable_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_DailyTimeTable_TAB IS 'Der Tagesfahrplan mit Fahrten ';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.tripident IS 'Eindeutige Kennung der Fahrt';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.tripno is 'Fahrtnummer';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.operationalno is 'Verwaltungsnummer zur Unterscheidung von Fahrten mit gleicher Nr';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.tripversion is 'Nummer der Variante des Verkehrsmittel (Info+)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.operatingday is 'Betriebstag';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.stopsequenceno is 'ReihenfolgenNr des Halts einer Fahrt';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.stopident is 'Eindeutige Kennung des Halts';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.stopname is 'Name des Halts';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.stoppointident is 'Eindeutige Kennung des Haltepunkts am Halt';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.stoppointname is 'Name des Haltepunkts';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.arrstoppointtext is 'Haltepositionstext (Reisendeninformation) Ankunft';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.depstoppointtext is 'Haltepositionstext (Reisendeninformation) Abfahrt';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.arrdatetime is 'Ankunftszeit am Halt/Haltepunkt';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.depdatetime is 'Abfahrtszeit am Halt/Haltepunkt';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.noentry is 'Einsteigeverbot';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.noexit is 'Aussteigeverbot';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.categorycode IS 'Code der Gattung';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.classno IS 'ProduktklassenNr der Gattung (0-13)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.categoryno IS 'Nr für sprachabhängigen Gattungslangnamen (0-999). Auch Text möglich - gilt dann für alle Sprachen';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.lineno is 'Liniennummer';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.directionShort is 'Kennung der Richtung (H,R)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.directiontext IS 'Ausgabetext der Richtung';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.attributecode IS 'Code des Attributes (array)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.attributetext_de IS 'Text des Attributs deutsch (array)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.attributetext_fr IS 'Text des Attributs französisch (array)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.attributetext_en IS 'Text des Attributs englisch (array)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.attributetext_it IS 'Text des Attributs italienisch (array)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.infotextcode IS 'Code/Nr des Infotext (array)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.infotext_de IS 'Code/Text des Infotext deutsch (array)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.infotext_fr IS 'Code/Text des Infotext französisch (array)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.infotext_en IS 'Code/Text des Infotext englisch (array)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.infotext_it IS 'Code/Text des Infotext italienisch (array)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.longitude_geo IS 'Längengrad der Haltestelle (x-Koordinate)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.latitude_geo IS 'Breitengrad der Haltestelle (y-Koordinate)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.altitude_geo IS 'Geographische Höhe der Haltestelle (z-Koordinate, Meter über NN)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.transfertime1 IS 'Umsteigezeit in Minuten zwischen IC und IC max 60 Min';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.transfertime2 IS 'Umsteigezeit in Minuten zwischen allen anderen Gattungskombinationen';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.transferprio IS 'Umsteigepriorität der Haltestelle (0-16 => 0 ist höchste Prio)';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.tripno_continued IS 'FahrtNr für Durchbindung; fährt weiter als';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.operationalno_continued	IS 'Verwaltungsnummer für Durchbindung; fährt weiter als';
COMMENT ON COLUMN HRDF_DailyTimeTable_TAB.stopno_continued	IS 'HaltestellenNr für Durchbindung; kann unterschiedlich zum Halt sein';
CREATE INDEX IDX01_HRDF_DailyTimeTable_TAB ON HRDF_DailyTimeTable_TAB (fk_eckdatenid, operatingday) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_DailyTimeTable_TAB ON HRDF_DailyTimeTable_TAB (fk_eckdatenid, operationalno) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX03_HRDF_DailyTimeTable_TAB ON HRDF_DailyTimeTable_TAB (fk_eckdatenid, lineno varchar_pattern_ops) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX04_HRDF_DailyTimeTable_TAB ON HRDF_DailyTimeTable_TAB (fk_eckdatenid, stopident) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX05_HRDF_DailyTimeTable_TAB ON HRDF_DailyTimeTable_TAB (fk_eckdatenid, directionshort) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX06_HRDF_DailyTimeTable_TAB ON HRDF_DailyTimeTable_TAB (operatingday) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX07_HRDF_DailyTimeTable_TAB ON HRDF_DailyTimeTable_TAB (fk_eckdatenid, operatingday, stopident) TABLESPACE :TBSINDEXNAME;

/*
\brief  table for tripcount per operator
*/
CREATE TABLE HRDF_tripcount_operator_TAB
(
  id SERIAL primary key,
  fk_eckdatenid integer NOT NULL,
  operationalno varchar(32) NOT NULL,
  tripcount integer NULL,
  lineno varchar(8) NULL,
  categorycode varchar(8) NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
COMMENT ON TABLE HRDF_tripcount_operator_TAB IS 'Anzahl Fahrten pro Operator/Linie/Kategorie und EckdatenID';
CREATE INDEX IDX01_HRDF_tripcount_operator_TAB ON HRDF_tripcount_operator_TAB (fk_eckdatenid,operationalno) TABLESPACE :TBSINDEXNAME;
ALTER SEQUENCE IF EXISTS hrdf_tripcount_operator_tab_id_seq CYCLE;

/*
\brief  table for tripcount per line
*/
CREATE TABLE HRDF_tripcount_line_TAB
(
  id SERIAL primary key,
  fk_eckdatenid integer NOT NULL,
  operationalno varchar(32) NOT NULL,
  lineno varchar(8) NOT NULL,
  tripcount integer NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER SEQUENCE IF EXISTS hrdf_tripcount_line_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_tripcount_line_TAB IS 'Anzahl Fahrten pro Linie und EckdatenID';
CREATE INDEX IDX01_HRDF_tripcount_line_TAB ON HRDF_tripcount_line_TAB (fk_eckdatenid,operationalno) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_tripcount_line_TAB ON HRDF_tripcount_line_TAB (fk_eckdatenid,lineno varchar_pattern_ops) TABLESPACE :TBSINDEXNAME;

/*
\brief  table for lines per stop
*/
CREATE TABLE HRDF_linesperstop_TAB
(
  id SERIAL primary key,
  fk_eckdatenid integer NOT NULL,
  stopno integer NOT NULL,
  operationalno varchar(32) NOT NULL,
  lineno varchar(8) NULL,
  categorycode varchar(8) NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER SEQUENCE IF EXISTS hrdf_linesperstop_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_linesperstop_TAB IS 'Linien pro Haltestelle und EckdatenID';
CREATE INDEX IDX01_HRDF_linesperstop_TAB ON HRDF_linesperstop_TAB (fk_eckdatenid,operationalno) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_linesperstop_TAB ON HRDF_linesperstop_TAB (fk_eckdatenid,lineno) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX03_HRDF_linesperstop_TAB ON HRDF_linesperstop_TAB (fk_eckdatenid,stopno) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX04_HRDF_linesperstop_TAB ON HRDF_linesperstop_TAB (fk_eckdatenid,categorycode) TABLESPACE :TBSINDEXNAME;


/*
\brief  table for stop-trip count statistics
*/
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


/* ---------------------------------------------- Tabellen für den HRDF-VDVService -----------------------
*/
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
ALTER SEQUENCE IF EXISTS hrdf_vdvlinienmapping_tab_id_seq CYCLE;
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
ALTER SEQUENCE IF EXISTS hrdf_vdvbetreibermapping_tab_id_seq CYCLE;
COMMENT ON TABLE HRDF_VDVBetreiberMapping_TAB IS 'Mapping-Tabelle für Betreiber';
COMMENT ON COLUMN HRDF_VDVBetreiberMapping_TAB.operationalno IS 'HRDF-Verwaltungsnummer';
COMMENT ON COLUMN HRDF_VDVBetreiberMapping_TAB.UICLaendercode IS 'UIC Laendercode';
COMMENT ON COLUMN HRDF_VDVBetreiberMapping_TAB.GONr IS 'Geschäftsorganisations NR';
COMMENT ON COLUMN HRDF_VDVBetreiberMapping_TAB.GOAbk IS 'Geschäftsorganisations Abkürzung';
COMMENT ON COLUMN HRDF_VDVBetreiberMapping_TAB.creationdatetime IS 'Zeitpunkt der Erstellung des Eintrags';
CREATE INDEX IDX01_HRDF_VDVBetreiberMapping_TAB ON HRDF_VDVBetreiberMapping_TAB (operationalno) TABLESPACE :TBSINDEXNAME;
