/*
	SQL script to create the hrdf import database
	
	Call script with following parameter from psql:	
	-v TBSDATA='<path to data tablespace>' -v TBSINDEX='<path to index tablespace>' -v DB='<name of db>'
*/

-- setting db dependend tablespace names
\set TBSDATANAME tbs_ :DB _data
\set TBSINDEXNAME tbs_ :DB _index

-- create db-superuser with own schema
CREATE USER hrdf WITH PASSWORD 'bmHRDF' CREATEDB CREATEUSER;
CREATE SCHEMA IF NOT EXISTS hrdf AUTHORIZATION hrdf;

-- create tablespaces
CREATE TABLESPACE :TBSDATANAME OWNER hrdf LOCATION :TBSDATA;
CREATE TABLESPACE :TBSINDEXNAME OWNER hrdf LOCATION :TBSINDEX;

-- grant privileges on tablespace to superuser
GRANT ALL ON TABLESPACE :TBSDATANAME TO hrdf;
GRANT ALL ON TABLESPACE :TBSINDEXNAME TO hrdf;

-- create database
DROP DATABASE :DB;
CREATE DATABASE :DB WITH OWNER = hrdf ENCODING 'UTF8' TEMPLATE = template1 TABLESPACE :TBSDATANAME;

-- grant privileges on database
GRANT TEMPORARY ON DATABASE :DB TO public;
GRANT ALL ON DATABASE :DB TO hrdf;