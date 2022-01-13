
-- für's Anlegen von Tabellen/Indizes
\set TBSDATANAME tbs_ :DBNAME _data
\set TBSINDEXNAME tbs_ :DBNAME _index

\encoding utf-8

\echo '=> Erweiterung der Tabelle HRDF_ECKDATEN_TAB um Spalten "inactive" und "ttgenerated"'
ALTER TABLE HRDF.hrdf_eckdaten_tab ADD COLUMN inactive bool NULL;
ALTER TABLE HRDF.hrdf_eckdaten_tab ADD COLUMN ttgenerated date[] NULL;
COMMENT ON COLUMN HRDF.hrdf_eckdaten_tab.inactive IS 'Markierung, dass die Daten nicht verwendet werden sollen';
COMMENT ON COLUMN HRDF.hrdf_eckdaten_tab.ttgenerated IS 'Array mit den Tagen, für die die Tagesfahrpläne bereits generiert wurden';
