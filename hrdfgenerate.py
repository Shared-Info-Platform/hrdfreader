
import sys
import logging
from datetime import datetime, date, timedelta
from hrdf.hrdfdb import HrdfDB
from hrdf.hrdfTTG import HrdfTTG
from hrdf.hrdflog import logger


def generate_timetable_from_hrdf(eckdatenId, generateFrom, generateTo, dbname, host):
	"""Generiert einen Tagesfahrplan aus den HRDF-Daten für die
	Betriebstage im angegebenen Zeitbereich

	eckdatenId -- ID aus der Tabelle HRDF_ECKDATEN_TAB
	generateFrom -- Beginn des Zeitbereichs, für den der Tagesfahrlan generiert wird (String-Format '%d.%m.%Y')
	generateTo -- Ende des Zeitbereichs, für den der Tagesfahrplan generiert wird (String-Format '%d.%m.%Y')
	dbname -- Datenbankname
	host -- Host auf dem die Datenbank läuft
	"""
	hrdf_db = HrdfDB(dbname, host, "hrdf", "bmHRDF")
	if hrdf_db.connect():
	
		# Initialisierung des HRDF-TTGenerators
		ttGenerator = HrdfTTG(hrdf_db)
		dtGenerateFrom = datetime.strptime(generateFrom, '%d.%m.%Y').date()
		dtGenerateTo = datetime.strptime(generateTo, '%d.%m.%Y').date()
		logger.info("Generierung des Tagesfahrplan für den Zeitraum von {:%d.%m.%Y} bis {:%d.%m.%Y}:".format(dtGenerateFrom, dtGenerateTo))
		if ( ttGenerator.setup(eckdatenId, dtGenerateFrom, dtGenerateTo) ):
			iErrorCnt = ttGenerator.generateTT()
			if ( iErrorCnt == 0):
				logger.info("Der Tagesfahrplan für den Zeitraum von {:%d.%m.%Y} bis {:%d.%m.%Y} wurde erfolgreich generiert".format(dtGenerateFrom, dtGenerateTo))
			else:
				logger.warning("Der Tagesfahrplan für den Zeitraum von {:%d.%m.%Y} bis {:%d.%m.%Y} konnte nicht vollständig generiert werden. {} fehlerhafte Fahrten".format(dtGenerateFrom, dtGenerateTo, iErrorCnt))
		else:
			logger.error("Der Tagesfahrplan-Generator konnte nicht initialisiert werden")
			
	else:
		logger.error("Es konnte keine Verbindung zur Datenbank aufgebaut werden")

def initialize_logging(loglevel):
	"""Initialisiert den Logger

	loglevel -- Level für die Logausgabe 
	"""	
	logger.setLevel(loglevel)
	# Handler für das Schreiben der Logausgaben in Datei
	logFH = logging.FileHandler('log/hrdfreader-generate.log')
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

	if (paraCnt < 2):
		print("\nAufruf: hrdfgenerate.py <eckdatenId> [<generateFrom> <generateTo>] [<loglevel>] [<dbname>] [<host>]\n")
		print("eckdatenId\tId des zu betrachtenden HRDF-Import")
		print("generateFrom\tBeginn des Zeitbereichs, für den der Tagesfahrlan generiert wird (String-Format '%d.%m.%Y') (default => heute)")
		print("generateTo\tEnde des Zeitbereichs, für den der Tagesfahrplan generiert wird (String-Format '%d.%m.%Y') (default => heute)")				
		print("loglevel\t\tLevel für die Logausgabe (default => INFO)")
		print("dbname\t\tDatenbankname (default => hrdfdb)")
		print("host\t\tHost auf dem die Datenbank läuft (default => 127.0.0.1)")
	else:
		if (sys.argv[1] == "-v"):
			print("\nHRDF-Reader: Tagesfahrplan-Modul Version 1")
			print("HRDF-Format: 5.20.39")
		else:
			eckdatenId = sys.argv[1]

			# Default für den Generierungszeitraum (=> heute)
			generateFrom = "{:%d.%m.%Y}".format(datetime.now().date())
			generateTo = generateFrom
			if (paraCnt >= 4):
				generateFrom = sys.argv[2]
				generateTo = sys.argv[3]

			# Logging initialisieren
			loglevel = "INFO"
			if (paraCnt >=5):
				loglevel = sys.argv[4].upper()
			initialize_logging(loglevel)
			# Default für die Datenbank
			dbname = "hrdfdb"
			if (paraCnt >= 6):
				dbname = sys.argv[5]

			# Default für den Host
			host = "127.0.0.1"
			if (paraCnt >= 7):
				host = sys.argv[6]

			generate_timetable_from_hrdf(eckdatenId, generateFrom, generateTo, dbname, host)
