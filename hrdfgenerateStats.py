
import sys
import logging
import os
import configparser
from datetime import datetime, date, timedelta
from hrdf.hrdfdb import HrdfDB
from hrdf.hrdfTTG import HrdfTTG
from hrdf.hrdflog import logger


def generate_timetable_statistics(eckdatenId, generateFrom, generateTo, dbname, host, port, user, pwd):
	"""Generiert Statistiken aus bestehenden Tagesfahrplandaten für die	Betriebstage im angegebenen Zeitbereich

	eckdatenId -- ID aus der Tabelle HRDF_ECKDATEN_TAB
	generateFrom -- Beginn des Zeitbereichs, für den der Tagesfahrlan analysiert wird (String-Format '%d.%m.%Y')
	generateTo -- Ende des Zeitbereichs, für den der Tagesfahrplan analysiert wird (String-Format '%d.%m.%Y')
	dbname -- Datenbankname
	host -- Host auf dem die Datenbank läuft
	port -- Port für den Zugriff auf die Datenbank
	user -- Datenbankbenutzer
	pwd -- Passwort des DB-Benutzer
	"""
	hrdf_db = HrdfDB(dbname, host, port, user, pwd)
	if hrdf_db.connect():
	
		# Initialisierung des HRDF-TTGenerators
		ttGenerator = HrdfTTG(hrdf_db)
		dtGenerateFrom = datetime.strptime(generateFrom, '%d.%m.%Y').date()
		dtGenerateTo = datetime.strptime(generateTo, '%d.%m.%Y').date()
		logger.info("Generierung des Tagesfahrplan-Statistikdaten für den Zeitraum von {:%d.%m.%Y} bis {:%d.%m.%Y} ({}):".format(dtGenerateFrom, dtGenerateTo, eckdatenId))
		if ( ttGenerator.setup(eckdatenId, dtGenerateFrom, dtGenerateTo) ):
			# Haltestellen-Statistik
			ttGenerator.createStopTripStats(eckdatenId, dtGenerateFrom, dtGenerateTo)
		else:
			logger.error("Der Tagesfahrplan-Generator konnte nicht initialisiert werden")
			
	else:
		logger.error("Es konnte keine Verbindung zur Datenbank aufgebaut werden")

def initialize_logging(loglevel, logfile):
	"""Initialisiert den Logger

	loglevel -- Level für die Logausgabe
	logfile -- Name der Logdatei (default => log/hrdfreader-generate.log)
	"""	
	logger.setLevel(loglevel)
	if (logfile == ""): logfile = 'log/hrdfreader-generate.log'
	
	# Handler für das Schreiben der Logausgaben in Datei
	logFH = logging.FileHandler(logfile)
	logFH.setLevel(loglevel)
	# Handler für das Schreiben direkt auf die Console
	logCH = logging.StreamHandler()
	logCH.setLevel(loglevel)
	# Formattierung der Ausgabe
	if (logger.level == logging.DEBUG):
		logFormatter = logging.Formatter('%(asctime)s - %(name)s (%(thread)d) %(funcName)s-%(lineno)d - %(levelname)s - %(message)s')
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
		print("\nAufruf: hrdfgenerateStats.py <eckdatenId> <generateFrom> <generateTo>\n")
		print("eckdatenId\tId des zu betrachtenden HRDF-Import")
		print("generateFrom\tBeginn des Zeitbereichs, für den der Tagesfahrlan analysiert wird (String-Format '%d.%m.%Y') (default => heute)")
		print("generateTo\tEnde des Zeitbereichs, für den der Tagesfahrplan analysiert wird (String-Format '%d.%m.%Y') (default => heute)")
	else:
		if (sys.argv[1] == "-v"):
			print("\nHRDF-Reader: Tagesfahrplan-Modul Version {}".format(HrdfTTG.modulVersion))
			print("HRDF-Formate: {}".format(HrdfTTG.hrdfFormats))
		else:
			if (os.path.exists(configFile)):
				eckdatenId = sys.argv[1]

				hrdfConfig = configparser.ConfigParser()
				hrdfConfig.read(configFile)

				# Default für den Generierungszeitraum (=> heute)
				generateFrom = "{:%d.%m.%Y}".format(datetime.now().date())
				generateTo = generateFrom
				if (paraCnt >= 4):
					generateFrom = sys.argv[2]
					generateTo = sys.argv[3]

				# Logging initialisieren
				loglevel = hrdfConfig['HRDFGeneration']["loglevel"]
				logfile = hrdfConfig['HRDFGeneration']["logfile"]
				initialize_logging(loglevel, logfile)
				logger.info("HRDF-Reader: Tagesfahrplan-Modul Version {} / HRDF-Formate: <{}>".format(HrdfTTG.modulVersion, HrdfTTG.hrdfFormats))

				# Angaben zur Datenbank
				dbname = hrdfConfig['DATABASE']['dbname']
				host = hrdfConfig['DATABASE']['host']
				port = hrdfConfig['DATABASE']['port']
				user = hrdfConfig['DATABASE']['user']
				pwd = hrdfConfig['DATABASE']['pwd']

				generate_timetable_statistics(eckdatenId, generateFrom, generateTo, dbname, host, port, user, pwd)
			else:
				print("HRDF-Konfigurationsdatei {} existiert nicht".format(configFile))
