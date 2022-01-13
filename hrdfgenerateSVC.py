
import sys
import os
import logging
import configparser
from datetime import datetime, date, timedelta
from hrdf.hrdfdb import HrdfDB
from hrdf.hrdfTTG import HrdfTTG
from hrdf.hrdfTTGService import HrdfTTGService
from hrdf.hrdflog import logger

def initialize_logging(loglevel, logfile):
	"""Initialisiert den Logger

	loglevel -- Level für die Logausgabe
	logfile -- Name der Logdatei (default => log/hrdfreader-generate.log
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
	startService = False
	configFile = 'hrdfconfig.config'

	paraCnt = len(sys.argv)

	if (paraCnt == 1):
		startService = True

	elif (paraCnt == 2):
		if (sys.argv[1] == '-v'):
			print("\nHRDF-Reader: TTG-Modul Version {}".format(HrdfTTG.modulVersion))
			print("HRDF-Formate: {}".format(HrdfTTG.hrdfFormats))
		elif (sys.argv[1] == '-h'):
			print("\nAufruf: hrdfgenerateSVC.py [<configFile>]\n")
			print("configFile\tPfad/Name der Konfigurationsdatei für den HRDF-TTG-Service (default=> hrdfconfig.config)")
		else:
			# Es ist eine Konfigurationsdatei angegeben
			configFile = sys.argv[1]
			startService = True

	if (startService):
		# hier kanns dann losgehen.
		if (os.path.exists(configFile)):
			hrdfConfig = configparser.ConfigParser()
			hrdfConfig.read(configFile)

			generateConfig = hrdfConfig["HRDFGeneration"]
			loglevel = generateConfig["loglevel"]
			logfile = generateConfig["logfile"]
			initialize_logging(loglevel, logfile)
			logger.info("HRDF-Reader: TTG-Modul Version {} / HRDF-Formate: <{}>".format(HrdfTTG.modulVersion, HrdfTTG.hrdfFormats))
			
			hrdf_ttgService = HrdfTTGService(hrdfConfig)
			if (hrdf_ttgService.initialise()):
				hrdf_ttgService.run()
			else:
				logger.error("HRDF-TTG-Service konnte nicht initialisiert werden")

		else:
			initialize_logging('INFO', 'log/hrdfreader-generate.log')
			logger.info("HRDF-Reader: TTG-Modul Version {} / HRDF-Formate: <{}>".format(HrdfTTG.modulVersion, HrdfTTG.hrdfFormats))		
			logger.error("Konfigurationsdatei {} nicht gefunden".format(configFile))
