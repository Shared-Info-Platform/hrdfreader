/*
	SQL script to create database-object in hrdf-schema
*/

-- tables
\i 'hrdf-tables.sql'

-- views
\i 'hrdf-views.sql'

-- functions
-- data
INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.4', 'version created', '1', 'Database creation');
INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.4-0', 'update_2.4-0.sql', '1', 'Erweiterung Tabelle Eckdaten / Neue Tabelle Update-Historie');
INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.4-1', 'update_2.4-1.sql', '1', 'Neuer Index; Füllen der Historie-Tabelle');
INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.4-2', 'update_2.4-2.sql', '1', 'Neue VDV-Mapping-Tabellen');
INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.4-3', 'update_2.4-3.sql', '1', 'Anpassung LinienMapping für PostAuto');
INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.4-4', 'update_2.4-4.sql', '1', 'Neue View hrdf_bahnhofgleis_view');
INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.4-5', 'update_2.4-5.sql', '2', 'Neue Indizes für BahnhofGleis-View und DailyTimeTable; Sequence cycle; Haltestellenstatistik');