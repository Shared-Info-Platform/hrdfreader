/*
	SQL script to create hrdf - tables 
*/

\set TBSDATANAME tbs_ :DBNAME _data
\set TBSINDEXNAME tbs_ :DBNAME _index

/*
\brief	table for file ECKDATEN (with extensions)
*/
CREATE TABLE HRDF_ECKDATEN_TAB
(
  id				SERIAL		NOT NULL,
  validFrom			date		NOT NULL,
  validTo			date		NOT NULL,
  descriptionhrdf	varchar		NULL,
  description		varchar		NULL,
  creationdatetime	timestamp with time zone NULL,
  hrdfversion		varchar(10)	NULL,
  exportsystem		varchar(20)	NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_ECKDATEN_TAB ADD CONSTRAINT PK_HRDF_ECKDATEN_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
COMMENT ON TABLE HRDF_ECKDATEN_TAB IS 'Eckdaten der Fahrplanperiode';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.validFrom is 'erster Gueltigkeitstag des Fahrplans';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.validTo is 'letzter Gueltigkeitstag des Fahrplans';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.descriptionhrdf is 'Fahrplanbezeichnung in HRDF';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.description is '+ Bezeichnung des Fahrplans';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.creationdatetime is '+ Erzeugungsdatum mit Zeit';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.hrdfversion is '+ Version der HRDF-Daten';
COMMENT ON COLUMN HRDF_ECKDATEN_TAB.exportsystem is '+ System von dem die HRDF-Daten exportiert wurden';


/*
\brief	table for file BITFELD
*/
CREATE TABLE HRDF_BITFELD_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  bitfieldno		integer		NOT NULL,
  bitfield			varchar(96)	NOT NULL,
  bitfieldextend	varchar(380) NOT NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_BITFELD_TAB ADD CONSTRAINT PK_HRDF_BITFELD_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
COMMENT ON TABLE HRDF_BITFELD_TAB IS 'Verkehrstagesdefinitionen der Fahrten (BITFELD)';
COMMENT ON COLUMN HRDF_BITFELD_TAB.bitfieldno is 'Eindeutige Nr der Verkehrstagesdefinition';
COMMENT ON COLUMN HRDF_BITFELD_TAB.bitfield is 'Verkehrstagesdefinition als Bitfeld (hrdf-hexdezimalcodiert)';
COMMENT ON COLUMN HRDF_BITFELD_TAB.bitfieldextend is '+ Verkehrstagesdefinition als Bitfeld (bitcodiert bereinigt)';
CREATE INDEX IDX01_HRDF_BITFELD_TAB ON HRDF_BITFELD_TAB (fk_eckdatenid, bitfieldno) TABLESPACE :TBSINDEXNAME;

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
COMMENT ON TABLE HRDF_ZUGART_TAB IS 'Verkehrsmittel bzw. Gattung';
COMMENT ON COLUMN HRDF_ZUGART_TAB.categorycode IS 'Code der Gattung';
COMMENT ON COLUMN HRDF_ZUGART_TAB.classno IS 'ProduktklassenNr der Gattung (0-13)';
COMMENT ON COLUMN HRDF_ZUGART_TAB.tariffgroup IS 'Tarifgruppe der Gattung (A-H)';
COMMENT ON COLUMN HRDF_ZUGART_TAB.outputcontrol IS 'Ausgabesteuerung (0=Gattung und Nummer, 1=Gattung, 2=Nummer, 3=keine Ausgabe, +4=Betreiber statt Gattung)';
COMMENT ON COLUMN HRDF_ZUGART_TAB.categorydesc IS 'Gattungsbezeichnung,di ausgegeben wird';
COMMENT ON COLUMN HRDF_ZUGART_TAB.extracharge IS 'Zuschlag (0=Zuschlagfrei, 1=Zuschlagpflicht nach Kontext, 2=Zuschlagpflicht)';
COMMENT ON COLUMN HRDF_ZUGART_TAB.flags IS 'Flags (N=Nahverkehr, B=Schiff';
COMMENT ON COLUMN HRDF_ZUGART_TAB.categoryimage IS 'Nr für Gattungsbildernamen (0-999)';
COMMENT ON COLUMN HRDF_ZUGART_TAB.categoryno IS 'Nr für sprachabhängigen Gattungslangnamen (0-999). Auch Text möglich - gilt dann für alle Sprachen';
CREATE INDEX IDX01_HRDF_ZUGART_TAB ON HRDF_ZUGART_TAB (fk_eckdatenid, categorycode) TABLESPACE :TBSINDEXNAME;

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
COMMENT ON TABLE HRDF_ATTRIBUT_TAB IS 'Spezielle Attribute einer Fahrt/Fahrtabschnitt';
COMMENT ON COLUMN HRDF_ATTRIBUT_TAB.attributecode IS 'Code des Attributes';
COMMENT ON COLUMN HRDF_ATTRIBUT_TAB.languagecode IS '+ Sprache des Attributs (Kürzel entsprechend der Dateiendung)';
COMMENT ON COLUMN HRDF_ATTRIBUT_TAB.stopcontext IS 'Haltestellenzugehörigkeit (0=Fahrtabschnitt, 1=Abfahrtshaltestelle, 2=Ankunftshaltestelle)';
COMMENT ON COLUMN HRDF_ATTRIBUT_TAB.outputprio IS 'Ausgabepriorität, kleine Werte sind höher Prior (0-999)';
COMMENT ON COLUMN HRDF_ATTRIBUT_TAB.outputpriosort IS 'Ausgabepriosortierung, bei gleicher Prio => Ausgabe nach Sortierung';
COMMENT ON COLUMN HRDF_ATTRIBUT_TAB.attributetext IS 'Text des Attributs (Abschlusszeichen # entfällt)';
COMMENT ON COLUMN HRDF_ATTRIBUT_TAB.outputforsection IS 'Attributcode für Ausgabe einer Teilstrecke)';
COMMENT ON COLUMN HRDF_ATTRIBUT_TAB.outputforcomplete IS 'Attributcode für Ausgabe auf der Vollstrecke)';
CREATE INDEX IDX01_HRDF_ATTRIBUT_TAB ON HRDF_ATTRIBUT_TAB (fk_eckdatenid, attributecode, languagecode) TABLESPACE :TBSINDEXNAME;


/*
\brief	table for file INFOTEXT
*/
CREATE TABLE HRDF_INFOTEXT_TAB
(
  id				SERIAL			NOT NULL,
  fk_eckdatenid		integer			NOT NULL,
  infotextno		integer			NOT NULL,
  infotextlanguage	varchar(2)		NOT NULL,
  infotext			varchar(1000)	NOT NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_INFOTEXT_TAB ADD CONSTRAINT PK_HRDF_INFOTEXT_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
COMMENT ON TABLE HRDF_INFOTEXT_TAB IS 'Im Fahrplan verwendete Infotexte';
COMMENT ON COLUMN HRDF_INFOTEXT_TAB.infotextno IS 'Nr. des Infotext';
COMMENT ON COLUMN HRDF_INFOTEXT_TAB.infotextlanguage IS '+ Sprache des Infotext (Kürzel entsprechend der Dateiendung)';
COMMENT ON COLUMN HRDF_INFOTEXT_TAB.infotext IS 'Infotext';
CREATE INDEX IDX01_HRDF_INFOTEXT_TAB ON HRDF_INFOTEXT_TAB (fk_eckdatenid, infotextno, infotextlanguage) TABLESPACE :TBSINDEXNAME;



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
COMMENT ON TABLE HRDF_FPLANFahrt_TAB IS 'Fahrten der FPLAN-Datei beginnend mit *Z / *KW / *T';
COMMENT ON COLUMN HRDF_FPLANFahrt_TAB.triptype is 'Art der Fahrt (Z, KW, T)';
COMMENT ON COLUMN HRDF_FPLANFahrt_TAB.tripno is 'Fahrtnummer';
COMMENT ON COLUMN HRDF_FPLANFahrt_TAB.operationalno is 'Verwaltungsnummer zur unterscheidung von Fahrten mit gleicher Nr';
COMMENT ON COLUMN HRDF_FPLANFahrt_TAB.tripversion is '+ Nummer der Variante des Verkehrsmittel (Info+)';
COMMENT ON COLUMN HRDF_FPLANFahrt_TAB.cyclecount is 'Taktanzahl der noch folgenden Takte; triptype=Z';
COMMENT ON COLUMN HRDF_FPLANFahrt_TAB.cycletimemin is 'Taktzeit in Minuten (Abstand zwischen zwei Fahrten); triptype=Z';
COMMENT ON COLUMN HRDF_FPLANFahrt_TAB.triptimemin is 'Fahrtzeitraum; triptype=T';
COMMENT ON COLUMN HRDF_FPLANFahrt_TAB.cycletimesec is 'Taktzeit in Sekunden(Abstand zwischen zwei Fahrten); triptype=T';
CREATE INDEX IDX01_HRDF_FPLANFahrt_TAB ON HRDF_FPLANFahrt_TAB (fk_eckdatenid, tripno, operationalno) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file FPLAN lines beginning with *A VE
*/
CREATE TABLE HRDF_FPLANFahrtVE_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  fk_fplanfahrtid   integer		NOT NULL,
  fromStop			integer		NOT NULL,
  toStop			integer		NOT NULL,
  bitfieldno		integer		NULL,
  deptimeFrom		integer		NULL,
  arrtimeFrom		integer		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_FPLANFahrtVE_TAB ADD CONSTRAINT PK_HRDF_FPLANFahrtVE_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
COMMENT ON TABLE HRDF_FPLANFahrtVE_TAB IS 'Fahrten der FPLAN-Datei beginnend mit *A VE';
COMMENT ON COLUMN HRDF_FPLANFahrtVE_TAB.fromStop is 'HaltestellenNr ab der die Verkehrstage gelten';
COMMENT ON COLUMN HRDF_FPLANFahrtVE_TAB.toStop is 'HaltestellenNr bis zu die Verkehrstage gelten';
COMMENT ON COLUMN HRDF_FPLANFahrtVE_TAB.bitfieldno is 'Eindeutige Nr der Verkehrstagesdefinition';
COMMENT ON COLUMN HRDF_FPLANFahrtVE_TAB.deptimeFrom is 'Abfahrtszeitpunkt der Ab-Haltestelle';
COMMENT ON COLUMN HRDF_FPLANFahrtVE_TAB.arrtimeFrom is 'Ankunftszeitpunkt der Bis-Haltestelle';
CREATE INDEX IDX01_HRDF_FPLANFahrtVE_TAB ON HRDF_FPLANFahrtVE_TAB (fk_fplanfahrtid) TABLESPACE :TBSINDEXNAME;
CREATE INDEX IDX02_HRDF_FPLANFahrtVE_TAB ON HRDF_FPLANFahrtVE_TAB (fk_eckdatenid, bitfieldno) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file FPLAN lines beginning with *G
*/
CREATE TABLE HRDF_FPLANFahrtG_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  fk_fplanfahrtid   integer		NOT NULL,
  categorycode		varchar(3)	NOT NULL,
  fromStop			integer		NOT NULL,
  toStop			integer		NOT NULL,
  deptimeFrom		integer		NULL,
  arrtimeFrom		integer		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_FPLANFahrtG_TAB ADD CONSTRAINT PK_HRDF_FPLANFahrtG_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
COMMENT ON TABLE HRDF_FPLANFahrtG_TAB IS 'Fahrten der FPLAN-Datei beginnend mit *A VE';
COMMENT ON COLUMN HRDF_FPLANFahrtG_TAB.categorycode is 'Code der Gattung';
COMMENT ON COLUMN HRDF_FPLANFahrtG_TAB.fromStop is 'HaltestellenNr ab der die Verkehrstage gelten';
COMMENT ON COLUMN HRDF_FPLANFahrtG_TAB.toStop is 'HaltestellenNr bis zu die Verkehrstage gelten';
COMMENT ON COLUMN HRDF_FPLANFahrtG_TAB.deptimeFrom is 'Abfahrtszeitpunkt der Ab-Haltestelle';
COMMENT ON COLUMN HRDF_FPLANFahrtG_TAB.arrtimeFrom is 'Ankunftszeitpunkt der Bis-Haltestelle';
CREATE INDEX IDX01_HRDF_FPLANFahrtG_TAB ON HRDF_FPLANFahrtG_TAB (fk_fplanfahrtid) TABLESPACE :TBSINDEXNAME;

/*
\brief	table for file FPLAN lines beginning with *A
*/
CREATE TABLE HRDF_FPLANFahrtA_TAB
(
  id				SERIAL		NOT NULL,
  fk_eckdatenid		integer		NOT NULL,
  fk_fplanfahrtid   integer		NOT NULL,
  attributecode		varchar(2)	NOT NULL,
  fromStop			integer		NOT NULL,
  toStop			integer		NOT NULL,
  bitfieldno		integer		NULL,
  deptimeFrom		integer		NULL,
  arrtimeFrom		integer		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_FPLANFahrtA_TAB ADD CONSTRAINT PK_HRDF_FPLANFahrtA_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
COMMENT ON TABLE HRDF_FPLANFahrtA_TAB IS 'Fahrten der FPLAN-Datei beginnend mit *A';
COMMENT ON COLUMN HRDF_FPLANFahrtA_TAB.attributecode is 'Attributscode';
COMMENT ON COLUMN HRDF_FPLANFahrtA_TAB.fromStop is 'HaltestellenNr ab der die Verkehrstage gelten';
COMMENT ON COLUMN HRDF_FPLANFahrtA_TAB.toStop is 'HaltestellenNr bis zu die Verkehrstage gelten';
COMMENT ON COLUMN HRDF_FPLANFahrtA_TAB.bitfieldno is 'Eindeutige Nr der Verkehrstagesdefinition';
COMMENT ON COLUMN HRDF_FPLANFahrtA_TAB.deptimeFrom is 'Abfahrtszeitpunkt der Ab-Haltestelle';
COMMENT ON COLUMN HRDF_FPLANFahrtA_TAB.arrtimeFrom is 'Ankunftszeitpunkt der Bis-Haltestelle';
CREATE INDEX IDX01_HRDF_FPLANFahrtA_TAB ON HRDF_FPLANFahrtA_TAB (fk_fplanfahrtid) TABLESPACE :TBSINDEXNAME;

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
  arrtimeFrom		integer		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_FPLANFahrtR_TAB ADD CONSTRAINT PK_HRDF_FPLANFahrtR_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
COMMENT ON TABLE HRDF_FPLANFahrtR_TAB IS 'Fahrten der FPLAN-Datei beginnend mit *A';
COMMENT ON COLUMN HRDF_FPLANFahrtR_TAB.directionShort is 'Kennung der Richtung (H,R)';
COMMENT ON COLUMN HRDF_FPLANFahrtR_TAB.directionCode is 'Richtungscode';
COMMENT ON COLUMN HRDF_FPLANFahrtR_TAB.fromStop is 'HaltestellenNr ab der die Verkehrstage gelten';
COMMENT ON COLUMN HRDF_FPLANFahrtR_TAB.toStop is 'HaltestellenNr bis zu die Verkehrstage gelten';
COMMENT ON COLUMN HRDF_FPLANFahrtR_TAB.deptimeFrom is 'Abfahrtszeitpunkt der Ab-Haltestelle';
COMMENT ON COLUMN HRDF_FPLANFahrtR_TAB.arrtimeFrom is 'Ankunftszeitpunkt der Bis-Haltestelle';
CREATE INDEX IDX01_HRDF_FPLANFahrtR_TAB ON HRDF_FPLANFahrtR_TAB (fk_fplanfahrtid) TABLESPACE :TBSINDEXNAME;

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
  fromStop			integer		NOT NULL,
  toStop			integer		NOT NULL,
  bitfieldno		integer		NULL,
  deptimeFrom		integer		NULL,
  arrtimeFrom		integer		NULL
)
WITH ( OIDS=FALSE )
TABLESPACE :TBSDATANAME;
ALTER TABLE HRDF_FPLANFahrtI_TAB ADD CONSTRAINT PK_HRDF_FPLANFahrtI_TAB PRIMARY KEY (ID) USING INDEX TABLESPACE :TBSINDEXNAME;
COMMENT ON TABLE HRDF_FPLANFahrtI_TAB IS 'Fahrten der FPLAN-Datei beginnend mit *A';
COMMENT ON COLUMN HRDF_FPLANFahrtI_TAB.infotextcode is 'Code des Infotext';
COMMENT ON COLUMN HRDF_FPLANFahrtI_TAB.infotextno is 'Nr. des Infotext';
COMMENT ON COLUMN HRDF_FPLANFahrtI_TAB.fromStop is 'HaltestellenNr ab der die Verkehrstage gelten';
COMMENT ON COLUMN HRDF_FPLANFahrtI_TAB.toStop is 'HaltestellenNr bis zu die Verkehrstage gelten';
COMMENT ON COLUMN HRDF_FPLANFahrtI_TAB.bitfieldno is 'Eindeutige Nr der Verkehrstagesdefinition';
COMMENT ON COLUMN HRDF_FPLANFahrtI_TAB.deptimeFrom is 'Abfahrtszeitpunkt der Ab-Haltestelle';
COMMENT ON COLUMN HRDF_FPLANFahrtI_TAB.arrtimeFrom is 'Ankunftszeitpunkt der Bis-Haltestelle';
CREATE INDEX IDX01_HRDF_FPLANFahrtI_TAB ON HRDF_FPLANFahrtI_TAB (fk_fplanfahrtid) TABLESPACE :TBSINDEXNAME;


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
