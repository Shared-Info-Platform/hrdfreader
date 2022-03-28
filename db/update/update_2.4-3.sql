-- für's Anlegen von Tabellen/Indizes
\set TBSDATANAME tbs_ :DBNAME _data
\set TBSINDEXNAME tbs_ :DBNAME _index

\encoding utf-8

\echo '=> Korrektur des Linien-Mapping für PostAuto'
UPDATE HRDF.HRDF_VDVLinienMapping_TAB SET linienId = cast(cast(linienId as integer) as varchar) WHERE operationalno = '000801';

INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.4-3', 'update_2.4-3.sql', '1', 'Anpassung LinienMapping für PostAuto');