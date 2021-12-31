
import sys
import os
import logging
import configparser
from hrdf.hrdfdb import HrdfDB
from hrdf.hrdfreader import HrdfReader
from hrdf.hrdflog import logger

import zipfile


def load_hrdfzipfile(filename, dbname, host, user, pwd):
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
		BFKOORD_WGS
		UMSTEIGB
		BFPRIOS
		METABHF
		FPLAN
	"""
	hrdf_db = HrdfDB(dbname, host, user, pwd)
	if hrdf_db.connect():

		# ZipFile öffnen und zu lesende Dateien bestimmen
		hrdfzip = zipfile.ZipFile(filename, 'r')
		hrdffiles = ['ECKDATEN','BITFELD','RICHTUNG','BAHNHOF','GLEIS','ZUGART','ATTRIBUT','INFOTEXT','DURCHBI','BFKOORD_WGS','UMSTEIGB','BFPRIOS','METABHF','FPLAN']
		
		# Initialisierung des HRDF-Readers und lesen der gewünschten HRDF-Dateien
		reader = HrdfReader(hrdfzip, hrdf_db, hrdffiles)
		reader.readfiles()
		hrdfzip.close()

	else:
		logger.error("Es konnte keine Verbindung zur Datenbank aufgebaut werden")


def initialize_logging(loglevel, logfile):
	"""Initialisiert den Logger
	loglevel -- Level für die Logausgabe	
	logfile -- Name der Logdatei (default => log/hrdfreader-import.log)
	"""	
	logger.setLevel(loglevel)
	if (logfile == ""): logfile = 'log/hrdfreader-import.log'

	# Handler für das Schreiben der Logausgaben in Datei
	logFH = logging.FileHandler(logfile)
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
	configFile = 'hrdfconfig.config'

	if (paraCnt < 2):
		print("\nAufruf: hrdfimport.py <importFile>\n")
	else:

		if (sys.argv[1] == "-v"):
			print("\nHRDF-Reader: Import-Modul Version {}".format(HrdfReader.modulVersion))
			print("HRDF-Formate: {}".format(HrdfReader.hrdfFormats))
		else:
			if (os.path.exists(configFile)):
				zipfilename = sys.argv[1]

				hrdfConfig = configparser.ConfigParser()
				hrdfConfig.read(configFile)

				# Logging initialisieren
				loglevel = hrdfConfig['HRDFImport']["loglevel"]
				logfile = hrdfConfig['HRDFImport']["logfile"]
				initialize_logging(loglevel, logfile)
				logger.info("HRDF-Reader: Import-Modul Version {} / HRDF-Formate: <{}>".format(HrdfReader.modulVersion, HrdfReader.hrdfFormats))
		
				# Angaben zur Datenbank
				dbname = hrdfConfig['DATABASE']['dbname']
				host = hrdfConfig['DATABASE']['host']
				user = hrdfConfig['DATABASE']['user']
				pwd = hrdfConfig['DATABASE']['pwd']

				load_hrdfzipfile(zipfilename, dbname, host, user, pwd)
			else:
				print("HRDF-Konfigurationsdatei {} existiert nicht".format(configFile))
