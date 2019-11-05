
import sys
from hrdf.hrdfdb import HrdfDB
from hrdf.hrdfreader import HrdfReader
from hrdf.hrdflog import logger

import zipfile


def load_hrdfzipfile(filename, dbname, host):
	"""Lädt die HRDF-Zipdatei und schreibt den Inhalt der Dateien in die Datenbank

	filename -- Pfad/Name der Zipdatei die zu laden ist
	dbnanme -- Name der Datenbank, in die die Daten geschrieben werden
	host -- Host auf dem die Datenbank läuft

	Aufzunehmende HRDF-Dateien:
		ECKDATEN
		BITFELD
		ZUGART
		RICHTUNG
		ATTRIBUT_XX (sprachabhängig)
		INFOTEXT_XX (sprachabhängig)
		DURCHBI
		BFKOORD_GEO
		UMSTEIGB
		BFPRIOS
		FPLAN
	"""
	hrdf_db = HrdfDB(dbname, host, "hrdf", "bmHRDF")
	if hrdf_db.connect():

		# ZipFile öffnen und zu lesende Dateien bestimmen
		hrdfzip = zipfile.ZipFile(filename, 'r')
		hrdffiles = ['ECKDATEN','BITFELD','RICHTUNG','BAHNHOF','GLEIS','ZUGART','ATTRIBUT','INFOTEXT','DURCHBI','BFKOORD_GEO','UMSTEIGB','BFPRIOS','FPLAN']
		
		# Initialisierung des HRDF-Readers und lesen der gewünschten HRDF-Dateien
		reader = HrdfReader(hrdfzip, hrdf_db, hrdffiles)
		reader.readfiles()

	else:
		logger.error("Es konnte keine Verbindung zur Datenbank aufgebaut werden")


if __name__ == '__main__':
	# Auswertung der übergebenen Parameter
	paraCnt = len(sys.argv)

	if (paraCnt < 2):
		print("\nAufruf: hrdfimport.py <importFile> [<dbname>] [<host>]\n")
		print("importFile\tPfad/Name der HRDF-Import-Zipdatei die zu laden ist")
		print("dbname\t\tDatenbankname (default => hrdfdb)")
		print("host\t\tHost auf dem die Datenbank läuft (default => 127.0.0.1)")
	else:
		zipfilename = sys.argv[1]
		
		# Default für die Datenbank
		dbname = "hrdfdb"
		if (paraCnt >= 3):
			dbname = sys.argv[2]

		# Default für den Host
		host = "127.0.0.1"
		if (paraCnt >= 4):
			host = sys.argv[3]
	
		load_hrdfzipfile(zipfilename, dbname, host)
