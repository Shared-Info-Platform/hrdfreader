
import sys
import logging
import os.path
import configparser
from hrdf.hrdfReaderService import HrdfReaderService
from hrdf.hrdfreader import HrdfReader
from hrdf.hrdflog import logger

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
	startService = False
	configFile = 'hrdfconfig.config'

	paraCnt = len(sys.argv)
	if (paraCnt == 1):
		startService = True

	elif (paraCnt == 2):
		if (sys.argv[1] == "-v"):
			print("\nHRDF-Reader: Import-Modul Version {}".format(HrdfReader.modulVersion))
			print("HRDF-Formate: {}".format(HrdfReader.hrdfFormats))
		elif (sys.arg[1] == "-h"):
			print("\nAufruf: hrdfimportSVC.py [<configFile>]\n")
			print("configFile\tPfad/Name der Konfigurationsdatei für den HRDF-Import-Service (default=> hrdfconfig.config")
		else:
			# Es ist eine Konfigurationsdatei angegeben
			configFile = sys.argv[1]
			startService = True

	if (startService):
		# hier kanns dann losgehen.
		if (os.path.exists(configFile)):
			hrdfConfig = configparser.ConfigParser()
			hrdfConfig.read(configFile)

			importConfig = hrdfConfig["HRDFImport"]
			loglevel = importConfig["loglevel"]
			logfile = importConfig["logfile"]
			initialize_logging(loglevel, logfile)
			logger.info("HRDF-Reader: Import-Modul Version {} / HRDF-Formate: <{}>".format(HrdfReader.modulVersion, HrdfReader.hrdfFormats))
			
			hrdf_readerService = HrdfReaderService(hrdfConfig)
			if (hrdf_readerService.initialise()):
				hrdf_readerService.run()
			else:
				logger.error("HRDF-Reader-Service konnte nicht initialisiert werden")

		else:
			initialize_logging('INFO', 'log/hrdfreader-import.log')
			logger.info("HRDF-Reader: Import-Modul Version {} / HRDF-Formate: <{}>".format(HrdfReader.modulVersion, HrdfReader.hrdfFormats))		
			logger.error("Konfigurationsdatei {} nicht gefunden".format(configFile))
