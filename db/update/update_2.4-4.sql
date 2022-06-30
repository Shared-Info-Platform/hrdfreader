-- für's Anlegen von Tabellen/Indizes
\set TBSDATANAME tbs_ :DBNAME _data
\set TBSINDEXNAME tbs_ :DBNAME _index

\encoding utf-8

\echo '=> Neue View für Anzeige von Gleisen pro Haltestelle'
CREATE OR REPLACE VIEW hrdf.hrdf_bahnhofgleis_view
AS SELECT
   a.id,
   a.fk_eckdatenid,
   a.stopno,
   a.stopname,
   b.stoppoints,
   coalesce(array_length(b.stoppoints,1),0) as stoppointcnt
   FROM hrdf_bahnhof_tab a
        LEFT OUTER JOIN (SELECT fk_eckdatenid, stopno, array_agg(distinct stoppointtext order by stoppointtext) stoppoints FROM hrdf_gleis_tab GROUP BY fk_eckdatenid, stopno) b ON a.stopno = b.stopno AND a.fk_eckdatenid = b.fk_eckdatenid;

INSERT INTO HRDF.HRDF_UpdateHistory_TAB (databaseversion, scriptname, scriptversion, description) VALUES ('2.4-4', 'update_2.4-4.sql', '1', 'Neue View hrdf_bahnhofgleis_view');