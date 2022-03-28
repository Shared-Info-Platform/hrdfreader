#!/bin/bash
#
# Script to update a hrdf-import-database
#


if [[ "$1" == "?" || "$1" == "" || "$2" == "" || "$3" == "" || "$4" == "" ]] ;
then
   echo "****************************************************************************************"   
   echo "  Usage: update-hrdf.sh [host] [databasename] [user] [password]"
   echo "****************************************************************************************"
   echo "  host         = ip-address of host where postgres is running"
   echo "  databasename = name of database to update"
   echo "  port         = port"
   echo "  user         = user"
   echo "  pwd          = password"
   echo "****************************************************************************************"
else

	export PGPASSWORD=$5

	echo "updating to version 2.1 ..."
	#psql -h $1 -d $2 -p $3 -U $4 -f update_2.1-0.sql
	#psql -h $1 -d $2 -p $3 -U $4 -f update_2.1-1.sql

	echo "updating to version 2.2 ..."
	#psql -h $1 -d $2 -p $3 -U $4 -f update_2.2-0.sql
	
	echo "updating to version 2.3 ..."
	#psql -h $1 -d $2 -p $3 -U $4 -f update_2.3-0.sql
	#psql -h $1 -d $2 -p $3 -U $4 -f update_2.3-1.sql
	#psql -h $1 -d $2 -p $3 -U $4 -f update_2.3-2.sql

	echo "updating to version 2.4 ..."
	#psql -h $1 -d $2 -p $3 -U $4 -f update_2.4-0.sql
	#psql -h $1 -d $2 -p $3 -U $4 -f update_2.4-1.sql
	#psql -h $1 -d $2 -p $3 -U $4 -f update_2.4-2.sql
	psql -h $1 -d $2 -p $3 -U $4 -f update_2.4-3.sql

fi
