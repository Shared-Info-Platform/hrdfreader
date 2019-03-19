
import sys
from hrdf.hrdfdb import HrdfDB
from hrdf.hrdfreader import HrdfReader
import zipfile


def load_hrdfzipfile(filename, dbname):
	"""Lädt die HRDF-Zipdatei und schreibt den Inhalt der Dateien in die Datenbank

	filename -- Pfad/Name der Zipdatei die zu laden ist
	dbnanme -- Name der Datenbank, in die die Daten geschrieben werden

	Aufzunehmende HRDF-Dateien:
		ECKDATEN
		BITFELD
		ZUGART
		RICHTUNG
		ATTRIBUT_XX (sprachabhängig)
		INFOTEXT_XX (sprachabhängig)
		FPLAN
	"""
	hrdf_db = HrdfDB(dbname, "127.0.0.1", "hrdf", "bmHRDF")
	if hrdf_db.connect():

		# ZipFile öffnen und zu lesende Dateien bestimmen
		hrdfzip = zipfile.ZipFile(filename, 'r')
		hrdffiles = ['ECKDATEN', 'BITFELD', 'RICHTUNG', 'ZUGART', 'BAHNHOF', 'ATTRIBUT', 'INFOTEXT', 'FPLAN']
		
		# Initialisierung des HRDF-Readers und lesen der gewünschten HRDF-Dateien
		reader = HrdfReader(hrdfzip, hrdf_db, hrdffiles)
		reader.readfiles()

	else:
		print("Es konnte keine Verbindung zur Datenbank aufgebaut werden")


if __name__ == '__main__':
	zipfilename = sys.argv[1]
	dbname = sys.argv[2]	
	load_hrdfzipfile(zipfilename, dbname)
