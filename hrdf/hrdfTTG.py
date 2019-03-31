import psycopg2
from datetime import datetime, date, timedelta
from hrdf.hrdflog import logger

class HrdfTTG:
	"""
	Die Klasse generiert einen Tagesfahrplan für einen gewünschten Zeitraum

	"""

	def __init__(self, db):
		"""
		db - HRDF-DB
		"""
		self.__hrdfdb = db
		self.__importFileName = "unknown"
		self.__eckdatenid = -1
		self.__generateFrom = datetime.now().date()
		self.__generateTo = datetime.now().date()

	def setup(self, eckdatenId, generateFrom, generateTo):
		""" Die Funktion richtet den Tagesfahrplan-Generator für die anstehende
		Generierung ein

		eckdatenId - Id aus der Tabelle HRDF_ECKDATEN_TAB
		generateFrom -- Beginn des Zeitbereichs, für den der Tagesfahrlan generiert wird 
		generateTo -- Ende des Zeitbereichs, für den der Tagesfahrplan generiert wird
		"""
		bReturn = False
		self.__importFileName = "unknown"
		self.__eckdatenid = -1
		self.__generateFrom = datetime.now().date()
		self.__generateTo = datetime.now().date()

		# Ermitteln/Verifizieren des gewünschten Fahrplans
		cur = self.__hrdfdb.connection.cursor()
		sql_string = "SELECT id, importFileName, validFrom, validTo, description FROM HRDF_ECKDATEN_TAB WHERE id = %s"
		cur.execute(sql_string, (eckdatenId,))
		row = cur.fetchone()
		if ( row is None):
			logger.error("Der gewünschte Fahrplan <{}> wurde nicht gefunden".format(eckdatenId))
		elif ( generateFrom >= row[2] and generateTo <= row[3] ):
			bReturn = True
			self.__importFileName = row[1]
			self.__generateFrom = generateFrom
			self.__generateTo = generateTo
			self.__eckdatenid = eckdatenId
		else:
			logger.error("Der zu generierende Zeitbereich liegt außerhalb der Fahrplangrenzen")
			

		cur.close()
		return bReturn
	
	def generateTT(self):
		""" Die Funktion generiert den gewünschten Tagesfahrplan bzgl. der Daten, die über setup() bestimmt wurden"""
		bReturn = False

		sql_selDayTrips = "SELECT b.id, b.tripno, b.operationalno, b.tripversion, array_agg(a.bitfieldno) as bitfieldnos "\
						  "FROM HRDF_FPlanFahrtVE_TAB a, "\
						  "     HRDF_FPLanFahrt_TAB b "\
						  "WHERE a.bitfieldno in (SELECT bitfieldno FROM HRDF_Bitfeld_TAB where bitfieldarray @> ARRAY[%s::date] AND fk_eckdatenid = %s) "\
						  "  and a.fk_fplanfahrtid = b.id "\
						  "  and b.fk_eckdatenid = a.fk_eckdatenid "\
						  "  and a.fk_eckdatenid = %s "\
						  "GROUP BY b.id, b.tripno, b.operationalno, b.tripversion"

		dayCnt = (self.__generateFrom - self.__generateTo).days
		i = 0
		while (i<=dayCnt):
			generationDay = self.__generateFrom + timedelta(days=i)
			logger.info("Generierung des Tages {:%d.%m.%Y}".format(generationDay))

			cur = self.__hrdfdb.connection.cursor("cursor_selDayTrip")
			cur.execute(sql_selDayTrips, (str(generationDay), self.__eckdatenid, self.__eckdatenid))
			# Schleife über den selDayTrip-Cursor, der in 10000er Blöcken abgearbeitet wird
			currentRowCnt = 0
			while True:				
				trips = cur.fetchmany(10000)
				if not trips:
					break
				rowCnt = len(trips)
				logger.info("generiere die nächsten {} Fahrten (bis jetzt {})".format(rowCnt, currentRowCnt))
				for trip in trips:
					self.generateTrip(trip)
				currentRowCnt += rowCnt

			cur.close()

			i += 1

		return bReturn

	def generateTrip(self, trip):
		""" Die Funktion generiert die Angaben zur übergebenen Fahrt

		trip - Datenzeile der Tabelle HRDF_FPlanFahrt_TAB mit einem Array der gültigen BitfieldNos (Verkehrstagesschlüssel)
		"""
		bReturn = False
		#logger.info("generiere Zug {}".format(trip))

		sql_selStops = "SELECT * FROM HRDF_FPlanFahrtLaufweg_TAB WHERE fk_fplanfahrtid = %s ORDER BY sequenceno"
		cur = self.__hrdfdb.connection.cursor()
		cur.execute(sql_selStops, (str(trip[0]),))
		allTripStops = cur.fetchall()
		cur.close()

		return bReturn
