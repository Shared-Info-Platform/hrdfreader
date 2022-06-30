/*
	SQL script to create hrdf - tables 
*/

\set TBSDATANAME tbs_ :DBNAME _data
\set TBSINDEXNAME tbs_ :DBNAME _index

/*
\brief  departures view
*/
CREATE OR REPLACE VIEW hrdf.hrdf_dailytimetable_departures_view
AS SELECT hrdf_dailytimetable_tab.id,
    hrdf_dailytimetable_tab.tripno,
    hrdf_dailytimetable_tab.fk_eckdatenid,
    hrdf_dailytimetable_tab.tripident,
    hrdf_dailytimetable_tab.operationalno,
    hrdf_dailytimetable_tab.operatingday,
    hrdf_dailytimetable_tab.stopident,
    hrdf_dailytimetable_tab.lineno,
    hrdf_dailytimetable_tab.directiontext,
    hrdf_dailytimetable_tab.directionshort,
    hrdf_dailytimetable_tab.depstoppointtext,
    hrdf_dailytimetable_tab.depdatetime,
    hrdf_dailytimetable_tab.noentry,
    hrdf_dailytimetable_tab.noexit,
    hrdf_dailytimetable_tab.categorycode,
    hrdf_dailytimetable_tab.classno,
    hrdf_dailytimetable_tab.categoryno,
    hrdf_dailytimetable_tab.attributecode,
    hrdf_dailytimetable_tab.attributetext_de,
    hrdf_dailytimetable_tab.attributetext_fr,
    hrdf_dailytimetable_tab.attributetext_en,
    hrdf_dailytimetable_tab.attributetext_it,
    hrdf_dailytimetable_tab.infotextcode,
    hrdf_dailytimetable_tab.infotext_de,
    hrdf_dailytimetable_tab.infotext_fr,
    hrdf_dailytimetable_tab.infotext_en,
    hrdf_dailytimetable_tab.infotext_it
   FROM hrdf_dailytimetable_tab
  WHERE hrdf_dailytimetable_tab.depdatetime IS NOT NULL
  ORDER BY hrdf_dailytimetable_tab.depdatetime;

/*
\brief  view for stop information
*/
CREATE OR REPLACE VIEW hrdf.hrdf_stopinformation_view
AS SELECT
    bhf.id,
    bhf.fk_eckdatenid,
    bhf.stopno,
    bhf.transportunion,
    bhf.stopname,
    bhf.stopnamelong,
    bhf.stopnameshort,
    bhf.stopnamealias,
    koord.longitude_geo,
    koord.latitude_geo,
    koord.altitude_geo,
    prio.transferprio,
    umst.transfertime1,
    umst.transfertime2
   FROM hrdf_bahnhof_tab bhf
     LEFT JOIN hrdf_bfkoord_tab koord ON bhf.fk_eckdatenid = koord.fk_eckdatenid AND bhf.stopno = koord.stopno
     LEFT JOIN hrdf_bfprios_tab prio ON bhf.fk_eckdatenid = prio.fk_eckdatenid AND bhf.stopno = prio.stopno
     LEFT JOIN hrdf_umsteigb_tab umst ON bhf.fk_eckdatenid = umst.fk_eckdatenid AND bhf.stopno = umst.stopno;

/*
\brief  view for stop point information
*/
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

     
