#!/bin/bash
#
# Script to create a hrdf-import-database
#


if [[ "$1" == "?" || "$1" == "" || "$2" == "" || "$3" == "" ]] ;
then
   echo "****************************************************************************************"   
   echo "  Usage: create-hrdf.sh [host] [databasename] [data-path]"
   echo "****************************************************************************************"
   echo "  host         = ip-address of host where postgres is running and db should be installed"
   echo "  databasename = name of database to create"
   echo "  data-path    = path to directory where data should be stored. Postgres must have"
   echo "                 read/write access to that directory"
   echo "****************************************************************************************"
else

	echo "creating data-path directories..."
	mkdir -p $3
	mkdir -p $3/data
	mkdir -p $3/index
	
	echo "creating the database and the user..."
	psql -h $1 -d template1 -U postgres -f create-database-hrdf.sql -v DB=$2 -v TBSDATA=\'$3/data\' -v TBSINDEX=\'$3/index\' > create-database-hrdf_$2.log
	
	echo "creating the database-objects for user hrdf..."
	psql -h $1 -d $2 -U hrdf -f hrdf-schema.sql

fi
