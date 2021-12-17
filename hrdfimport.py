
import sys
import logging
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
		BFKOORD_WGS
		UMSTEIGB
		BFPRIOS
		METABHF
		FPLAN
	"""
	hrdf_db = HrdfDB(dbname, host, "hrdf", "bmHRDF")
	if hrdf_db.connect():

		# ZipFile öffnen und zu lesende Dateien bestimmen
		hrdfzip = zipfile.ZipFile(filename, 'r')
		hrdffiles = ['ECKDATEN','BITFELD','RICHTUNG','BAHNHOF','GLEIS','ZUGART','ATTRIBUT','INFOTEXT','DURCHBI','BFKOORD_GEO','BFKOORD_WGS','UMSTEIGB','BFPRIOS','METABHF','FPLAN']
		
		# Initialisierung des HRDF-Readers und lesen der gewünschten HRDF-Dateien
		reader = HrdfReader(hrdfzip, hrdf_db, hrdffiles)
		reader.readfiles()

	else:
		logger.error("Es konnte keine Verbindung zur Datenbank aufgebaut werden")


def initialize_logging(loglevel):
	"""Initialisiert den Logger
	loglevel -- Level für die Logausgabe 
	"""	
	logger.setLevel(loglevel)
	# Handler für das Schreiben der Logausgaben in Datei
	logFH = logging.FileHandler('log/hrdfreader-import.log')
	logFH.setLevel(loglevel)
	# Handler für das Schreiben direkt auf die Console
	logCH = logging.StreamHandler()
	logCH.setLevel(loglevel)
	# Formattierung der Ausgabe
	if (logger.level == logging.DEBUG):
		logFormatter = logging.Formatter('%(asctime)s - %(name)s %(funcName)s-%(lineno)d - %(levelname)s - %(message)s')
	else:
		logFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	logFH.setFormatter(logFormatter)
	logCH.setFormatter(logFormatter)
	# Aktivierung der Log-Handler
	logger.addHandler(logFH)
	logger.addHandler(logCH)

if __name__ == '__main__':
	# Auswertung der übergebenen Parameter
	paraCnt = len(sys.argv)

	if (paraCnt < 2):
		print("\nAufruf: hrdfimport.py <importFile> [<loglevel>] [<dbname>] [<host>]\n")
		print("importFile\tPfad/Name der HRDF-Import-Zipdatei die zu laden ist")		
		print("loglevel\t\tLevel für die Logausgabe (default => INFO)")
		print("dbname\t\tDatenbankname (default => hrdfdb)")
		print("host\t\tHost auf dem die Datenbank läuft (default => 127.0.0.1)")
	else:

		if (sys.argv[1] == "-v"):
			print("\nHRDF-Reader: Import-Modul Version 1")
			print("HRDF-Format: 5.20.39")
		else:
			zipfilename = sys.argv[1]
			# Logging initialisieren
			loglevel = "INFO"
			if (paraCnt >=3):
				loglevel = sys.argv[2]
			initialize_logging(loglevel)
		
			# Default für die Datenbank
			dbname = "hrdfdb"
			if (paraCnt >= 4):
				dbname = sys.argv[3]

			# Default für den Host
			host = "127.0.0.1"
			if (paraCnt >= 5):
				host = sys.argv[4]

			load_hrdfzipfile(zipfilename, dbname, host)
