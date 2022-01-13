-- für's Anlegen von Tabellen/Indizes
\set TBSDATANAME tbs_ :DBNAME _data
\set TBSINDEXNAME tbs_ :DBNAME _index

\encoding utf-8

\echo '=> Neuer Index für DailyTimeTable-TAB'
CREATE INDEX IDX06_HRDF_HRDF_DailyTimeTable_TAB_TAB ON HRDF_DailyTimeTable_TAB (operatingday) TABLESPACE :TBSINDEXNAME;

\echo '=> Füllen der Update-History-Tabelle'
INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.1', 'version created', '1', 'Datebase creation');
INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.1-0', 'update_2.1-0.sql', '1', 'Neue Tabellen für HRDF-Importer');
INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.1-1', 'update_2.1-1.sql', '1', 'Neue Views für Datenanalysen');
INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.2-0', 'update_2.2-0.sql', '1', 'Neue Indizes für DB-Optimierung; Tabellenerweiterung');
INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.3-0', 'update_2.3-0.sql', '1', 'Tabellenerweiterung; Anpassung Indizes');
INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.3-1', 'update_2.3-1.sql', '1', 'Anpassungen/Korrektur von Indizes');
INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.3-2', 'update_2.3-2.sql', '1', 'Erweiterung Tabelle Eckdaten');
INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.4-0', 'update_2.4-0.sql', '1', 'Erweiterung Tabelle Eckdaten / Neue Tabelle Update-Historie');
INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.4-1', 'update_2.4-1.sql', '1', 'Neuer Index; Füllen der Historie-Tabelle');