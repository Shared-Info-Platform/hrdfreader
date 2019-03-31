
import sys
from datetime import datetime, date, timedelta
from hrdf.hrdfdb import HrdfDB
from hrdf.hrdfTTG import HrdfTTG
from hrdf.hrdflog import logger


def generate_timetable_from_hrdf(eckdatenId, generateFrom, generateTo, dbname):
	"""Generiert einen Tagesfahrplan aus den HRDF-Daten für die
	Betriebstage im angegebenen Zeitbereich

	eckdatenId -- ID aus der Tabelle HRDF_ECKDATEN_TAB
	generateFrom -- Beginn des Zeitbereichs, für den der Tagesfahrlan generiert wird (String-Format '%d.%m.%Y')
	generateTo -- Ende des Zeitbereichs, für den der Tagesfahrplan generiert wird (String-Format '%d.%m.%Y')
	dbname -- Datenbankname
	"""
	hrdf_db = HrdfDB(dbname, "127.0.0.1", "hrdf", "bmHRDF")
	if hrdf_db.connect():
	
		# Initialisierung des HRDF-TTGenerators
		ttGenerator = HrdfTTG(hrdf_db)
		dtGenerateFrom = datetime.strptime(generateFrom, '%d.%m.%Y').date()
		dtGenerateTo = datetime.strptime(generateTo, '%d.%m.%Y').date()
		logger.info("Generierung des Tagesfahrplan für den Zeitraum von {:%d.%m.%Y} bis {:%d.%m.%Y}:".format(dtGenerateFrom, dtGenerateTo))
		if ( ttGenerator.setup(eckdatenId, dtGenerateFrom, dtGenerateTo) ):
			if (ttGenerator.generateTT()):
				logger.info("Der Tagesfahrplan für den Zeitraum von {:%d.%m.%Y} bis {:%d.%m.%Y} wurde erfolgreich generiert".format(dtGenerateFrom, dtGenerateTo))
			else:
				logger.warning("Der Tagesfahrplan für den Zeitraum von {:%d.%m.%Y} bis {:%d.%m.%Y} konnte nicht vollständig generiert werden".format(dtGenerateFrom, dtGenerateTo))
		else:
			logger.error("Der Tagesfahrplan-Generator konnte nicht initialisiert werden")
			
	else:
		logger.error("Es konnte keine Verbindung zur Datenbank aufgebaut werden")


if __name__ == '__main__':
	# Auswertung der übergebenen Parameter
	eckdatenId = sys.argv[1]
	generateFrom = sys.argv[2]
	generateTo = sys.argv[3]
	dbname = sys.argv[4]	

	generate_timetable_from_hrdf(eckdatenId, generateFrom, generateTo, dbname)
