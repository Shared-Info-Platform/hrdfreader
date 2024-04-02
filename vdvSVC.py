import sys
import logging
import os.path
import configparser
from vdv.vdvService import VdvService
from vdv.vdvlog import logger

def initialize_logging(loglevel, logfile):
	"""Initialisiert den Logger
	loglevel -- Level für die Logausgabe
	logfile -- Name der Logdatei (default => log/hrdfreader-import.log)
	"""	
	logger.setLevel(loglevel)
	if (logfile == ""): logfile = 'log/vdvservice.log'
		
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
	configFile = 'vdvconfig.config'

	paraCnt = len(sys.argv)
	if (paraCnt == 1):
		startService = True

	elif (paraCnt == 2):
		if (sys.argv[1] == "-v"):
			print("\nVDVService: Version {}".format(VdvService.modulVersion))
			print("VDV-Formate: {}".format(VdvService.vdvFormats))
			print("VDV-Versionen: {}".format(VdvService.vdvVersions))
		elif (sys.argv[1] == "-h"):
			print("\nAufruf: vdvSVC.py [<configFile>]\n")
			print("configFile\tPfad/Name der Konfigurationsdatei für den VDVService (default=> vdvconfig.config)")
		else:
			# Es ist eine Konfigurationsdatei angegeben
			configFile = sys.argv[1]
			startService = True

	if (startService):
		# hier kanns dann losgehen.
		if (os.path.exists(configFile)):
			vdvConfig = configparser.ConfigParser()
			vdvConfig.read(configFile)

			serviceConfig = vdvConfig["VDVService"]
			loglevel = serviceConfig["loglevel"]
			logfile = serviceConfig["logfile"]
			initialize_logging(loglevel, logfile)
			logger.info("VDVService: Version {} / VDV-Formate: <{}> / VDV-Versionen: <{}>".format(VdvService.modulVersion, VdvService.vdvFormats, VdvService.vdvVersions))
			
			vdvService = VdvService(vdvConfig)
			if (vdvService.initialise()):
				vdvService.run()
			else:
				logger.error("VDVService konnte nicht initialisiert werden")

		else:
			initialize_logging('INFO', 'log/vdvservice.log')
			logger.info("VDVService: Version {} / VDV-Formate: <{}> / VDV-Versionen: <{}>".format(VdvService.modulVersion, VdvService.vdvFormats, VdvService.vdvVersions))
			logger.error("Konfigurationsdatei {} nicht gefunden".format(configFile))

