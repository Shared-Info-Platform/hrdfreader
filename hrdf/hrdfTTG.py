import psycopg2
from datetime import datetime, date, timedelta, time
from io import StringIO
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
		# Listen, Strukturen für schnellen Zugriff auf Daten während der Generierung
		self.__bitfieldnumbersOfDay = set()
		self.__fahrtZugartLookup = dict()
		self.__bahnhofLookup = dict()
		self.__gleisLookup = dict()
		self.__allTripStopsLookup = dict()
		self.__allVEsLookup = dict()
		self.__stopSequenceLookup = dict()
		self.__fahrtLinienLookup = dict()
		self.__fahrtRichtungLookup = dict()
		self.__fahrtAttributLookup = dict()
		self.__fahrtInfoLookup = dict()
		self.__fahrtDurchbindungLookup = dict()

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
	
	def infohelp(self, text):
		""" Die Funktion korrigiert den Text (Infotext) mit entsprechenden Escape-Sequencen """
		return str(text).replace(";", "\;").replace("\"", "\\\\\"").replace("\n", "\\n")

	def buildLookupLists(self):
		""" Die Funktion erstellt Lookup-Listen für die Optimierung der Generierung """

		# Lookup für Zugarten der Fahrplanfahrten
		logger.info("Lookup für Zugarten aufbauen")
		sql_zugartLookup = "SELECT a.fk_fplanfahrtid, a.categorycode, fromstop, tostop, deptimefrom, arrtimeto, b.classno, b.categoryno"\
						   "  FROM HRDF_FPlanFahrtG_TAB a, "\
						   "       HRDF_ZUGART_TAB b "\
						   " WHERE a.fk_eckdatenid = %s "\
						   "   and a.fk_eckdatenid = b.fk_eckdatenid "\
						   "   and a.categorycode = b.categorycode "\
						   " ORDER BY a.fk_fplanfahrtid, a.id"

		curFahrtZugart = self.__hrdfdb.connection.cursor()
		curFahrtZugart.execute(sql_zugartLookup, (self.__eckdatenid,))
		fahrtZugarten = curFahrtZugart.fetchall()
		for fahrtZugart in fahrtZugarten:
			fahrtId = fahrtZugart[0]
			if ( fahrtId in self.__fahrtZugartLookup):
				self.__fahrtZugartLookup[fahrtId].append(fahrtZugart)
			else:
				zugartList = list()
				zugartList.append(fahrtZugart);
				self.__fahrtZugartLookup[fahrtId] = zugartList

		curFahrtZugart.close()

		# Lookup für Bahnhofsnamen, Übergangszeiten (mit Standardzeit aus erster Zeile stopno 9999999) und GEO-Koordinaten
		logger.info("Lookup für Bahnhofsinformation aufbauen")
		sql_bahnhofLookup = "SELECT a.stopno, a.stopname, a.stopnamelong, a.stopnameshort, a.stopnamealias,"\
						    "       coalesce(c.transfertime1,b.transfertime1) as transfertime1, coalesce(c.transfertime2,b.transfertime2) as transfertime2,"\
						    "       d.transferprio,"\
						    "       e.longitude_geo, e.latitude_geo, e.altitude_geo"\
						    "  FROM HRDF_bahnhof_TAB a"\
							"       INNER JOIN (SELECT transfertime1, transfertime2, fk_eckdatenid FROM HRDF_umsteigb_TAB WHERE stopno = 9999999) b ON b.fk_eckdatenid = a.fk_eckdatenid"\
						    "       LEFT OUTER JOIN HRDF_umsteigb_TAB c ON c.stopno = a.stopno AND c.fk_eckdatenid = a.fk_eckdatenid"\
						    "       LEFT OUTER JOIN HRDF_bfprios_TAB d ON d.stopno = a.stopno AND d.fk_eckdatenid = a.fk_eckdatenid"\
						    "       LEFT OUTER JOIN HRDF_bfkoord_TAB e ON e.stopno = a.stopno AND e.fk_eckdatenid = a.fk_eckdatenid"\
						    " WHERE a.fk_eckdatenid = %s"
		curBahnhof = self.__hrdfdb.connection.cursor()
		curBahnhof.execute(sql_bahnhofLookup, (self.__eckdatenid,))		
		bahnhhoefe = curBahnhof.fetchall()
		for bahnhof in bahnhhoefe:
			self.__bahnhofLookup[bahnhof[0]] = bahnhof
		curBahnhof.close()

		# Lookup für Haltepositionstexte aufbauen (a.id zu beginn ist schneller als es wegzulassen oder am Ende zu stellen)
		# key => <FahrtId>-<StopNo>[-<StopPointTime>]
		logger.info("Lookup für Haltepositionstexte aufbauen")
		sql_selGleisData = "SELECT distinct a.id, a.id::varchar||'-'||stopno::varchar||coalesce('-'||stoppointtime::varchar,'') as key, stoppointtext, bitfieldno "\
						   "  FROM HRDF_FPlanFahrt_TAB a, HRDF_GLEIS_TAB b "\
						   " WHERE a.fk_eckdatenid = %s "\
						   "   AND a.fk_eckdatenid = b.fk_eckdatenid "\
						   "   AND b.tripno = a.tripno "\
						   "   AND b.operationalno = a.operationalno "
		curGleis = self.__hrdfdb.connection.cursor()
		curGleis.execute(sql_selGleisData, (self.__eckdatenid,))
		allGleise = curGleis.fetchall()
		curGleis.close()
		for gleis in allGleise:
			if (gleis[3] is None or (gleis[3] in self.__bitfieldnumbersOfDay) or gleis[3] == 0):
				self.__gleisLookup[gleis[1]] = gleis[2]

		# Lookup für allTripStops erstellen. allTripStops einer Fahrt enthält den kompletten Laufweg der Fahrt.
		logger.info("Lookup für Laufwege der Fahrten aufbauen")
		sql_selStops = "SELECT stopno, stopname, sequenceno, arrtime, deptime, tripno, operationalno, ontripsign, "\
					   "       fk_fplanfahrtid||'-'||stopno as gleislookup, "\
					   "	   fk_fplanfahrtid||'-'||stopno||'-'||arrtime as gleislookupArr, "\
					   "       fk_fplanfahrtid||'-'||stopno||'-'||deptime as gleislookupDep, "\
					   "       fk_fplanfahrtid "\
		               "  FROM HRDF_FPlanFahrtLaufweg_TAB WHERE fk_eckdatenid = %s ORDER BY fk_fplanfahrtid, sequenceno"
		curStop = self.__hrdfdb.connection.cursor()
		curStop.execute(sql_selStops, (self.__eckdatenid,))
		allTripStops = curStop.fetchall()
		curStop.close()
		for tripStop in allTripStops:
			if (tripStop[11] in self.__allTripStopsLookup):
				self.__allTripStopsLookup[tripStop[11]].append(tripStop)
			else:
				tripStopList = list()
				tripStopList.append(tripStop);
				self.__allTripStopsLookup[tripStop[11]] = tripStopList

		# Lookup für allVEs erstellen. allVEs einer Fahrt enthält alle Verkehrstagesdefinitionen einer Fahrt
		logger.info("Lookup für Verkehrstagesinformation der Fahrten aufbauen")
		sql_selVEData = "SELECT bitfieldno, fromstop, tostop, deptimefrom, arrtimeto, fk_fplanfahrtid FROM HRDF_FPlanFahrtVE_TAB WHERE fk_eckdatenid = %s ORDER BY fk_fplanfahrtid, id"
		curVE = self.__hrdfdb.connection.cursor()
		curVE.execute(sql_selVEData, (self.__eckdatenid,))
		allVEs = curVE.fetchall()
		curVE.close()
		for fahrtVE in allVEs:
			if (fahrtVE[5] in self.__allVEsLookup):
				self.__allVEsLookup[fahrtVE[5]].append(fahrtVE)
			else:
				VEList = list()
				VEList.append(fahrtVE)
				self.__allVEsLookup[fahrtVE[5]] = VEList

		# Lookup für Linieninformationen der Fahrten
		logger.info("Lookup für Linieninformationen der Fahrten aufbauen")
		sql_selLData = "SELECT lineno, fromstop, tostop, deptimefrom, arrtimeto, fk_fplanfahrtid FROM HRDF_FPlanFahrtL_TAB WHERE fk_eckdatenid = %s ORDER BY fk_fplanfahrtid, id"
		curL = self.__hrdfdb.connection.cursor()
		curL.execute(sql_selLData, (self.__eckdatenid,))
		allLs = curL.fetchall()
		curL.close()
		for fahrtL in allLs:
			if (fahrtL[5] in self.__fahrtLinienLookup):
				self.__fahrtLinienLookup[fahrtL[5]].append(fahrtL)
			else:
				LList = list()
				LList.append(fahrtL)
				self.__fahrtLinienLookup[fahrtL[5]] = LList

		# Lookup für Richtungstexte der Fahrten
		logger.info("Lookup für Richtungstexte der Fahrten aufbauen")
		sql_selRData = "SELECT a.directionshort, fromstop, tostop, deptimefrom, arrtimeto, b.directiontext, fk_fplanfahrtid "\
					   "  FROM HRDF_FPlanFahrtR_TAB a, "\
					   "       HRDF_Richtung_TAB b "\
					   " WHERE a.fk_eckdatenid = %s "\
					   "   AND a.fk_eckdatenid = b.fk_eckdatenid "\
					   "   AND b.directioncode = a.directioncode "\
					   " ORDER BY a.fk_fplanfahrtid, a.id"
		curR = self.__hrdfdb.connection.cursor()
		curR.execute(sql_selRData, (self.__eckdatenid,))
		allRs = curR.fetchall()
		curR.close()
		for fahrtR in allRs:
			if (fahrtR[6] in self.__fahrtRichtungLookup):
				self.__fahrtRichtungLookup[fahrtR[6]].append(fahrtR)
			else:
				RList = list()
				RList.append(fahrtR)
				self.__fahrtRichtungLookup[fahrtR[6]] = RList

		# Lookup der Attribute einer Fahrt
		logger.info("Lookup für Attribute der Fahrten aufbauen")
		sql_selAData = "SELECT a.attributecode as attributecodeArray, fromstop, tostop, deptimefrom, arrtimeto, bitfieldno, "\
						"       b.attributetext as text_de, "\
						"       c.attributetext as text_fr, "\
						"       d.attributetext as text_en, "\
						"       e.attributetext as text_it, "\
						"       b.stopcontext as stopcontext, "\
						"       b.outputforsection as outputforsection, "\
						"       b.outputforcomplete as outputforcomplete, "\
						"       a.fk_fplanfahrtid "\
						"  FROM HRDF_FPlanFahrtA_TAB a "\
						"       LEFT OUTER JOIN HRDF_Attribut_TAB b ON b.attributecode = a.attributecode and a.fk_eckdatenid = b.fk_eckdatenid and b.languagecode = 'de' "\
						"       LEFT OUTER JOIN HRDF_Attribut_TAB c ON c.attributecode = a.attributecode and a.fk_eckdatenid = c.fk_eckdatenid and c.languagecode = 'fr' "\
						"	    LEFT OUTER JOIN HRDF_Attribut_TAB d ON d.attributecode = a.attributecode and a.fk_eckdatenid = d.fk_eckdatenid and d.languagecode = 'en' "\
						"	    LEFT OUTER JOIN HRDF_Attribut_TAB e ON e.attributecode = a.attributecode and a.fk_eckdatenid = e.fk_eckdatenid and e.languagecode = 'it' "\
						"  WHERE a.fk_eckdatenid = %s "
		curA = self.__hrdfdb.connection.cursor()
		curA.execute(sql_selAData, (self.__eckdatenid,))
		allAs = curA.fetchall()
		curA.close()
		for fahrtA in allAs:
			if (fahrtA[13] in self.__fahrtAttributLookup):
				self.__fahrtAttributLookup[fahrtA[13]].append(fahrtA)
			else:
				AList = list()
				AList.append(fahrtA)
				self.__fahrtAttributLookup[fahrtA[13]] = AList

		# Lookup für die Infotext einer Fahrt
		logger.info("Lookup für Infotexte der Fahrten aufbauen")
		sql_selIData = "SELECT a.infotextcode, fromstop, tostop, deptimefrom, arrtimeto, bitfieldno, "\
						"       b.infotext as text_de, "\
						"       c.infotext as text_fr, "\
						"       d.infotext as text_en, "\
						"       e.infotext as text_it, "\
						"       a.fk_fplanfahrtid "\
						"  FROM HRDF_FPlanFahrtI_TAB a "\
						"       LEFT OUTER JOIN HRDF_Infotext_TAB b ON b.infotextno = a.infotextno and a.fk_eckdatenid = b.fk_eckdatenid and b.languagecode = 'de' "\
						"   	LEFT OUTER JOIN HRDF_Infotext_TAB c ON c.infotextno = a.infotextno and a.fk_eckdatenid = c.fk_eckdatenid and c.languagecode = 'fr' "\
						"	   LEFT OUTER JOIN HRDF_Infotext_TAB d ON d.infotextno = a.infotextno and a.fk_eckdatenid = d.fk_eckdatenid and d.languagecode = 'en' "\
						"	   LEFT OUTER JOIN HRDF_Infotext_TAB e ON e.infotextno = a.infotextno and a.fk_eckdatenid = e.fk_eckdatenid and e.languagecode = 'it' "\
						"  WHERE a.fk_eckdatenid = %s "
		curI = self.__hrdfdb.connection.cursor()
		curI.execute(sql_selIData, (self.__eckdatenid,))
		allIs = curI.fetchall()
		curI.close()
		for fahrtI in allIs:
			if (fahrtI[10] in self.__fahrtInfoLookup):
				self.__fahrtInfoLookup[fahrtI[10]].append(fahrtI)
			else:
				IList = list()
				IList.append(fahrtI)
				self.__fahrtInfoLookup[fahrtI[10]] = IList

		# Lookup für die DurchbindungsInformation zu einer Fahrt
		logger.info("Lookup für Durchbindungsinformation der Fahrten aufbauen")
		sql_selDurchBiData = "SELECT b.laststopno1, b.bitfieldno, b.tripno2, b.operationalno2, coalesce(b.firststopno2, b.laststopno1), b.comment, a.id "\
						"  FROM HRDF_FPlanFahrt_TAB a, "\
						"       HRDF_DURCHBI_TAB b "\
						" WHERE b.tripno1 = a.tripno "\
						"   AND b.operationalno1 = a.operationalno "\
						"   AND b.fk_eckdatenid = a.fk_eckdatenid "\
						"   AND a.fk_eckdatenid = %s "
		curDurchBi = self.__hrdfdb.connection.cursor()
		curDurchBi.execute(sql_selDurchBiData, (self.__eckdatenid,))
		allDurchBi = curDurchBi.fetchall()
		curDurchBi.close()
		for fahrtDuBI in allDurchBi:
			if (fahrtDuBI[6] in self.__fahrtDurchbindungLookup):
				self.__fahrtDurchbindungLookup[fahrtDuBI[6]].append(fahrtDuBI)
			else:
				DuBiList = list()
				DuBiList.append(fahrtDuBI)
				self.__fahrtDurchbindungLookup[fahrtDuBI[6]] = DuBiList

	def generateTT(self):
		""" Die Funktion generiert den gewünschten Tagesfahrplan bzgl. der Daten, die über setup() bestimmt wurden"""
		iErrorCnt = 0

		# Aufbau von LookUp-Tabellen für die entsprechenden Ergänzungen des Tagesfahrplan
		self.buildLookupLists();

		sql_selDayTrips = "SELECT b.id, b.tripno, b.operationalno, b.tripversion, array_agg(a.bitfieldno) as bitfieldnos "\
						  "FROM HRDF_FPlanFahrtVE_TAB a, "\
						  "     HRDF_FPLanFahrt_TAB b "\
						  "WHERE (a.bitfieldno in (SELECT bitfieldno FROM HRDF_Bitfeld_TAB where bitfieldarray @> ARRAY[%s::date] AND fk_eckdatenid = %s) "\
						  "       OR a.bitfieldno is NULL OR a.bitfieldno = 0) "\
						  "  and a.fk_fplanfahrtid = b.id "\
						  "  and b.fk_eckdatenid = a.fk_eckdatenid "\
						  "  and a.fk_eckdatenid = %s "\
						  "GROUP BY b.id, b.tripno, b.operationalno, b.tripversion"

						  # für debugging-zwecke "  and b.id = 69665 "\

		dayCnt = (self.__generateTo - self.__generateFrom).days
		i = 0
		while (i<=dayCnt):
			generationDay = self.__generateFrom + timedelta(days=i)
			logger.info("Generierung des Tages {:%d.%m.%Y}".format(generationDay))

			# Laden der Verkehrstagesdefinitionen für den Generierungstag als set() für schnellen Zugriff/Abfrage auf Existenz
			self.__bitfieldnumbersOfDay.clear()
			sql_selBitfieldNos = "SELECT bitfieldno FROM HRDF_Bitfeld_TAB where bitfieldarray @> ARRAY[%s::date] AND fk_eckdatenid = %s"
			curBits = self.__hrdfdb.connection.cursor()
			curBits.execute(sql_selBitfieldNos, (str(generationDay), self.__eckdatenid))
			bitfieldNos = curBits.fetchall()
			for bitfield in bitfieldNos:
				self.__bitfieldnumbersOfDay.add(bitfield[0])
			curBits.close()

			# Löschen von bestehenden Tagesdaten"
			curDeleteDay = self.__hrdfdb.connection.cursor()
			sql_delDay = "DELETE FROM HRDF_DailyTimeTable_TAB WHERE fk_eckdatenid = %s AND operatingday = %s"
			curDeleteDay.execute(sql_delDay, (self.__eckdatenid, str(generationDay)))
			deletedRows = curDeleteDay.rowcount
			logger.info("\t{} bestehende Einträge für diesen Tag wurden geloescht".format(deletedRows))
			curDeleteDay.close()

			# Laden der Tagesfahrten und Generierung jeder Fahrt
			# mit einer Schleife über den selDayTrip-Cursor, der in 10000er Blöcken abgearbeitet wird
			curDayTrip = self.__hrdfdb.connection.cursor("cursor_selDayTrip")
			curDayTrip.execute(sql_selDayTrips, (str(generationDay), self.__eckdatenid, self.__eckdatenid))
			currentRowCnt = 0						
			numberOfGeneratedTrips = 0;
			dailytimetable_strIO = StringIO()
			while True:				
				trips = curDayTrip.fetchmany(10000)
				if not trips:
					break
				rowCnt = len(trips)
				logger.info("\tgeneriere die nächsten {} Fahrten (bis jetzt {})".format(rowCnt, currentRowCnt))
			
				tripStops = dict()
				for trip in trips:
					tripStops.clear()					
					tripident = "{}-{}-{}".format(trip[1],trip[2],trip[3])
					try:
						self.generateTrip(trip, tripStops)
						#Schreibe Fahrtinformation in Tabellenformat
						for tripStop in tripStops.values():
							arrival = tripStop["stop"][3]
							departure = tripStop["stop"][4]
							noentry = False
							noexit = False

							arrdatetime = ""
							if (arrival is not None):
								if (arrival < 0): noexit = True
								arrival = abs(arrival)
								arrMins = (int(arrival/100)*60)+(arrival%100)
								arrdatetime = str(datetime.combine(generationDay, time(0,0)) + timedelta(minutes=arrMins))

							depdatetime = ""
							if (departure is not None):
								if(departure < 0): noenty = True
								departure = abs(departure)
								depMins = (int(departure/100)*60)+(departure%100)
								depdatetime = str(datetime.combine(generationDay, time(0,0)) + timedelta(minutes=depMins))

							# Attribute
							strAttributecode = ""
							strAttributetextDE = ""
							strAttributetextFR = ""
							strAttributetextEN = ""
							strAttributetextIT = ""
							if (len(tripStop["attributecode"]) > 0):
								strAttributecode = "{'" + "','".join(map(str,tripStop["attributecode"])) + "'}"
							if (len(tripStop["attributetext_de"]) > 0):
								strAttributetextDE = "{'" + "','".join(map(str,tripStop["attributetext_de"])) + "'}"
							if (len(tripStop["attributetext_fr"]) > 0):
								strAttributetextFR = "{'" + "','".join(map(str,tripStop["attributetext_fr"])) + "'}"
							if (len(tripStop["attributetext_en"]) > 0):
								strAttributetextEN = "{'" + "','".join(map(str,tripStop["attributetext_en"])) + "'}"
							if (len(tripStop["attributetext_it"]) > 0):
								strAttributetextIT = "{'" + "','".join(map(str,tripStop["attributetext_it"])) + "'}"

							# Infotexte
							strInfotextcode = ""
							strInfotextDE = ""
							strInfotextFR = ""
							strInfotextEN = ""
							strInfotextIT = ""
							if (len(tripStop["infotextcode"]) > 0):
								strInfotextcode = '{"' + '","'.join(map(self.infohelp,tripStop["infotextcode"])) + '"}'
							if (len(tripStop["infotext_de"]) > 0):
								strInfotextDE = '{"' + '","'.join(map(self.infohelp,tripStop["infotext_de"])) + '"}'
							if (len(tripStop["infotext_fr"]) > 0):
								strInfotextFR = '{"' + '","'.join(map(self.infohelp,tripStop["infotext_fr"])) + '"}'
							if (len(tripStop["infotext_en"]) > 0):
								strInfotextEN = '{"' + '","'.join(map(self.infohelp,tripStop["infotext_en"])) + '"}'
							if (len(tripStop["infotext_it"]) > 0):
								strInfotextIT = '{"' + '","'.join(map(self.infohelp,tripStop["infotext_it"])) + '"}'
							
							# Angaben zur Haltestelle
							strLongitudeGeo = ""
							strLatitudeGeo = ""
							strAltitudeGeo = ""
							strTransferTime1 = ""
							strTransferTime2 = ""
							strTransferPrio = ""
							strTripNoContinued = ""
							strOperationalNoContinued = ""
							strStopNoContinued = ""
							if (tripStop["longitude_geo"] is not None): strLongitudeGeo = str(tripStop["longitude_geo"])
							if (tripStop["latitude_geo"] is not None): strLatitudeGeo = str(tripStop["latitude_geo"])
							if (tripStop["altitude_geo"] is not None): strAltitudeGeo = str(tripStop["altitude_geo"])
							if (tripStop["transfertime1"] is not None): strTransferTime1 = str(tripStop["transfertime1"])
							if (tripStop["transfertime2"] is not None): strTransferTime2 = str(tripStop["transfertime2"])
							if (tripStop["transferprio"] is not None): strTransferPrio = str(tripStop["transferprio"])
							if (tripStop["tripno_continued"] is not None): strTripNoContinued = str(tripStop["tripno_continued"])
							if (tripStop["operationalno_continued"] is not None): strOperationalNoContinued = str(tripStop["operationalno_continued"])
							if (tripStop["stopno_continued"] is not None): strStopNoContinued = str(tripStop["stopno_continued"])

							# Schreiben des Datensatzes
							dailytimetable_strIO.write(self.__eckdatenid)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(tripident)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(str(trip[1]))
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(trip[2])
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(str(trip[3]))
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(str(generationDay))
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(str(tripStop["stop"][2]))
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(str(tripStop["stop"][0]))
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(tripStop["stop"][1])
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(str(tripStop["stop"][0]))
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(tripStop["stop"][1])
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(tripStop["arrstoppointtext"])
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(tripStop["depstoppointtext"])
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(arrdatetime)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(depdatetime)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(str(noentry))
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(str(noexit))
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(tripStop["categorycode"])
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(str(tripStop["classno"]))
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(str(tripStop["categoryno"]))
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(tripStop["lineno"])
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(tripStop["directionshort"])
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(tripStop["directiontext"])
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(strAttributecode)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(strAttributetextDE)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(strAttributetextFR)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(strAttributetextEN)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(strAttributetextIT)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(strInfotextcode)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(strInfotextDE)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(strInfotextFR)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(strInfotextEN)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(strInfotextIT)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(strLongitudeGeo)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(strLatitudeGeo)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(strAltitudeGeo)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(strTransferTime1)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(strTransferTime2)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(strTransferPrio)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(strTripNoContinued)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(strOperationalNoContinued)
							dailytimetable_strIO.write(';')
							dailytimetable_strIO.write(strStopNoContinued)						
							dailytimetable_strIO.write('\n')
							numberOfGeneratedTrips += 1

					except Exception as err:
						iErrorCnt += 1
						logger.error("Die Fahrt {} konnte nicht generiert werden. Error:\n{}".format(tripident,err))

					
				# Alle Fahrten des Sets im IO abgelegt => speichern in DB
				tripStops.clear()				
				currentRowCnt += rowCnt

			logger.info("\tEs werden {} Tagesfahrplaneinträge in die DB eingetragen...".format(numberOfGeneratedTrips))				
			curSaveTrip = self.__hrdfdb.connection.cursor()
			strCopy = "COPY HRDF_DailyTimeTable_TAB (fk_eckdatenid,tripident,tripno,operationalno,tripversion,"\
						"operatingday,stopsequenceno,stopident,stopname,stoppointident,stoppointname,arrstoppointtext,depstoppointtext,arrdatetime,depdatetime,noentry,noexit,"\
						"categorycode,classno,categoryno,lineno,directionshort,directiontext,"\
						"attributecode,attributetext_de,attributetext_fr,attributetext_en,attributetext_it,"\
						"infotextcode,infotext_de,infotext_fr,infotext_en,infotext_it,"\
						"longitude_geo,latitude_geo,altitude_geo,transfertime1,transfertime2,transferprio,tripno_continued,operationalno_continued,stopno_continued)"\
						" FROM STDIN USING DELIMITERS ';' NULL AS ''"
			dailytimetable_strIO.seek(0)
			curSaveTrip.copy_expert(strCopy, dailytimetable_strIO)
			curSaveTrip.close()	
			dailytimetable_strIO.close()
			curDayTrip.close()
			# ein Commit vorher macht den Server-Cursor invalid
			self.__hrdfdb.connection.commit()

			# Tageszähler hochzählen und nächsten gewünschten Tag generieren
			i += 1

		return iErrorCnt


	def generateTrip(self, trip, newTripStops):
		""" Die Funktion generiert die Angaben zur übergebenen Fahrt

		trip - Datenzeile der Tabelle HRDF_FPlanFahrt_TAB mit einem Array der gültigen BitfieldNos (Verkehrstagesschlüssel)
		newTripStops - Dictonary, welches den Laufweg mit Zusatzinformationen enthält (=> sollte leer sein?!)
		"""
		bReturn = False
		#logger.info("generiere Zug {}".format(trip))
		fplanfahrtid = trip[0]
		allTripStops = self.__allTripStopsLookup[fplanfahrtid]
		allVEs = self.__allVEsLookup[fplanfahrtid]

		# Leeren der stopSequenceLookup, da diese nur für die aktuelle Fahrt gilt
		self.__stopSequenceLookup.clear()

		# Erstellen des definitiven Laufwegs für diesen Tag alls dictonary um den Laufweg mit zusätzlichen Informationen ergänzen zu können
		for ve in allVEs:
			if (ve[0] is None or (ve[0] in self.__bitfieldnumbersOfDay) or ve[0] == 0):
				bTakeStop = False
				for tripStop in allTripStops:
					tripStopNo = tripStop[0]
					sequenceNo = tripStop[2]  # hier wird die eindeutige SequenceNo verwendet (tripStopNo kann öfter vorkommen)

					# ist deptimefrom belegt muss auch die deptime des Stops passen
					if (ve[3] is None):
						if (tripStopNo == ve[1]):
							bTakeStop = True
					else:
						if (tripStopNo == ve[1] and tripStop[4] == ve[3]):
							bTakeStop = True
					# ist arrtimeto belegt muss auch die arrtime des Stops passen
					if (ve[4] is None):
						if (tripStopNo == ve[2]):
							if (tripStopNo not in newTripStops):
								newTripStops[sequenceNo] = dict(stop=tripStop) # letzter stop muss mit in die Liste
							bTakeStop = False
					else:
						if (tripStopNo == ve[2] and tripStop[3] == ve[4]):
							if (tripStopNo not in newTripStops):
								newTripStops[sequenceNo] = dict(stop=tripStop) # letzter stop muss mit in die Liste
							bTakeStop = False
					# alle stops übernehmen solange bTakeStop gesetzt ist
					if (bTakeStop):
						if (sequenceNo not in newTripStops):
							newTripStops[sequenceNo] = dict(stop=tripStop)

					# Nur wenn der Stop aufgenommen wurde, wird der Satz initialisiert
					if (sequenceNo in newTripStops):
						# Lookup für StopSequence füllen
						self.__stopSequenceLookup[tripStopNo] = sequenceNo
						# stoppointtexte ermitteln
						arrstoppointtext = ""
						depstoppointtext = ""
						if ( tripStop[8] in self.__gleisLookup):
							arrstoppointtext = self.__gleisLookup[tripStop[8]]
							depstoppointtext = self.__gleisLookup[tripStop[8]]
						else:
							if (tripStop[9] in self.__gleisLookup): arrstoppointtext = self.__gleisLookup[tripStop[9]]
							if (tripStop[10] in self.__gleisLookup): depstoppointtext = self.__gleisLookup[tripStop[10]]

						newTripStops[sequenceNo]["arrstoppointtext"] = arrstoppointtext
						newTripStops[sequenceNo]["depstoppointtext"] = depstoppointtext

						# Initialisieren der zusätzlichen Felder des TripStops
						newTripStops[sequenceNo]["categorycode"] = ""
						newTripStops[sequenceNo]["classno"] = ""
						newTripStops[sequenceNo]["categoryno"] = ""
						newTripStops[sequenceNo]["lineno"] = ""
						# Initialisierung der Richtungsangaben erfolgt in der entsprechenden Funktion
						newTripStops[sequenceNo]["directionshort"] = ""
						newTripStops[sequenceNo]["directiontext"] = ""
						newTripStops[sequenceNo]["attributecode"] = list()
						newTripStops[sequenceNo]["attributetext_de"] = list()
						newTripStops[sequenceNo]["attributetext_fr"] = list()
						newTripStops[sequenceNo]["attributetext_en"] = list()
						newTripStops[sequenceNo]["attributetext_it"] = list()
						newTripStops[sequenceNo]["infotextcode"] = list()
						newTripStops[sequenceNo]["infotext_de"] = list()
						newTripStops[sequenceNo]["infotext_fr"] = list()
						newTripStops[sequenceNo]["infotext_en"] = list()
						newTripStops[sequenceNo]["infotext_it"] = list()
						# Initialisierung der zusätzlichen Haltestellenmerkmale
						newTripStops[sequenceNo]["longitude_geo"] = self.__bahnhofLookup[tripStopNo][8]
						newTripStops[sequenceNo]["latitude_geo"] = self.__bahnhofLookup[tripStopNo][9]
						newTripStops[sequenceNo]["altitude_geo"] = self.__bahnhofLookup[tripStopNo][10]
						newTripStops[sequenceNo]["transfertime1"] = self.__bahnhofLookup[tripStopNo][5]
						newTripStops[sequenceNo]["transfertime2"] = self.__bahnhofLookup[tripStopNo][6]
						newTripStops[sequenceNo]["transferprio"] = self.__bahnhofLookup[tripStopNo][7]
						# Initialisierung der Durchbindungsmerkmale
						newTripStops[sequenceNo]["tripno_continued"] = None
						newTripStops[sequenceNo]["operationalno_continued"] = None
						newTripStops[sequenceNo]["stopno_continued"] = None

				# neue Stopliste ist erweitert um die Angaben des VEs

		# alle VEs sind bearbeitet
		# newTripStops enthält nun den tätsächlichen Laufweg, der jetzt mit zusätzlichen Informationen an den Halten gefüllt wird
		# G-Zeilen Information hinzufügen
		self.add_GInfoToTrip(fplanfahrtid, newTripStops)
		# L-Zeilen Information hinzufügen
		self.add_LInfoToTrip(fplanfahrtid, newTripStops)
		# A-Zeilen Information hinzufügen
		self.add_AInfoToTrip(fplanfahrtid, newTripStops)
		# I-Zeilen Information hinzufügen
		self.add_IInfoToTrip(fplanfahrtid, newTripStops)
		# R-Zeilen Information hinzufügen
		self.add_RInfoToTrip(fplanfahrtid, newTripStops)
		# Durchbindungs Information hinzufügen
		self.add_DurchBIToTrip(fplanfahrtid, newTripStops)

		return bReturn

	def getAffectedStops(self, fromStop, toStop, deptimeFrom, arrtimeTo, newTripStops):
		"""Die Funktion liefert eine Liste mit StopSequenceNos der Halte, die von den Angaben betroffen sind

		Die Halteliste wird von vorne nach hinten durchsucht.
		Kommen Halte mehrfach vor (Rundkurse...) sind diese eindeutig über Ankunft- bzw. Abfahrtszeiten definiert
		Sind keine Ankunft-/Abfahrtszeiten angegeben, dann kommt der Halt nur einmal in der Liste vor

		fromStop - Halt mit der die Liste beginnt
		toStop - Halt mit der die List aufhört
		deptimeFrom - Abfahrtszeit am "fromStop"
		arrtimeTo - Ankunftszeit am "toStop"
		newTripStops - Liste der Fahrthalte
		"""
		stopSequenceList = list()
		if (fromStop is None and toStop is None):
			stopSequenceList = newTripStops.keys()
		else:
			bTakeStop = False
			for sequenceNo in newTripStops:
				# ist deptimefrom belegt muss auch die deptime des Stops passen
				if (deptimeFrom is None):
					if (newTripStops[sequenceNo]["stop"][0] == fromStop):
						bTakeStop = True
				else:
					if (newTripStops[sequenceNo]["stop"][0] == fromStop and newTripStops[sequenceNo]["stop"][4] == deptimeFrom):
						bTakeStop = True
				# ist arrtimeto belegt muss auch die arrtime des Stops passen
				if (arrtimeTo is None):
					if (newTripStops[sequenceNo]["stop"][0] == toStop):
						stopSequenceList.append(sequenceNo)
						bTakeStop = False
				else:
					if (newTripStops[sequenceNo]["stop"][0] == toStop and newTripStops[sequenceNo]["stop"][3] == arrtimeTo):
						stopSequenceList.append(sequenceNo)
						bTakeStop = False
				# Übernahme der SequenceNo solange bTakeStop = true
				if (bTakeStop):
					stopSequenceList.append(sequenceNo)

		return stopSequenceList

	def getStopSequenceNo(self, stopno):
		"""Die Funktion liefert die SequenceNo für die angegebene HaltestellenNr. des angepassten Laufwegs
		Ist die gesuchte HaltestellenNr nicht in der Liste wird eine -1 geliefert.

		stopno - Haltestellenummer
		"""
		stopSequenceNo = -1
		if (stopno in self.__stopSequenceLookup): stopSequenceNo = self.__stopSequenceLookup[stopno]
		return stopSequenceNo

	def add_GInfoToTrip(self, fplanfahrtid, newTripStops):
		"""Die Funktion fügt zum Laufweg die notwendige G-Information hinzu

		fplanfahrtid - Id der Fahrplanfahrt
		newTripStops - angepasster Laufweg für diese Fahrt
		"""

		#listentry => a.fplanfahrtid, a.categorycode, fromstop, tostop, deptimefrom, arrtimeto, b.classno, b.categoryno
		if ( fplanfahrtid in self.__fahrtZugartLookup):
			zugartList = self.__fahrtZugartLookup[fplanfahrtid]
		
			if (len(zugartList) == 1):
				for tripStop in newTripStops.values():
					tripStop["categorycode"] = zugartList[0][1]
					tripStop["classno"] = zugartList[0][6]
					tripStop["categoryno"] = zugartList[0][7]
			else:
				for g in zugartList:
					sequenceNoList = self.getAffectedStops(g[2], g[3], g[4], g[5], newTripStops)
					# Belegung der notwendigen Attribute
					for sequenceNo in sequenceNoList:
						newTripStops[sequenceNo]["categorycode"] = g[1]
						newTripStops[sequenceNo]["classno"] = g[6]
						newTripStops[sequenceNo]["categoryno"] = g[7]

	def add_LInfoToTrip(self, fplanfahrtid, newTripStops):
		"""Die Funktion fügt zum Laufweg die notwendige L-Information hinzu

		fplanfahrtid - Id der Fahrplanfahrt
		newTripStops - angepasster Laufweg für diese Fahrt
		"""
		if ( fplanfahrtid in self.__fahrtLinienLookup):
			allLs = self.__fahrtLinienLookup[fplanfahrtid]

			if (len(allLs) == 1):
				for tripStop in newTripStops.values():
					tripStop["lineno"] = allLs[0][0]
			else:
				for l in allLs:
					sequenceNoList = self.getAffectedStops(l[1], l[2], l[3], l[4], newTripStops)
					# Belegung der notwendigen Attribute
					for sequenceNo in sequenceNoList:
						newTripStops[sequenceNo]["lineno"] = l[0]

	def add_RInfoToTrip(self, fplanfahrtid, newTripStops):
		"""Die Funktion fügt zum Laufweg die notwendige R-Information hinzu

		fplanfahrtid - Id der Fahrplanfahrt
		newTripStops - angepasster Laufweg für diese Fahrt
		"""

		# Initialisieren mit Defaultwerten
		defaultDirectionShort = ""
		defaultDirectionText = ""
		# Richtungstexte werden über den letzen Halt und das Bahnhof-Lookup mit Default-Werten belegt
		lastEntry = list(newTripStops.items())[-1][1]
		lastStopNo = lastEntry["stop"][0]
		if (lastStopNo in self.__bahnhofLookup):
			defaultDirectionText = self.__bahnhofLookup[lastStopNo][1]
		else:
			defaultDirectionText = lastEntry["stop"][1]

		for tripStop in newTripStops.values():
			tripStop["directionshort"] = defaultDirectionShort
			tripStop["directiontext"] = defaultDirectionText

		# Sobald ein Datensatz FahrtR vorhanden ist muss die "kompliziertere" Variante der Findung des richtigen Stops erfolgen
		if ( fplanfahrtid in self.__fahrtRichtungLookup):
			allRs = self.__fahrtRichtungLookup[fplanfahrtid]
			for r in allRs:
				sequenceNoList = self.getAffectedStops(r[1], r[2], r[3], r[4], newTripStops)
				# Belegung der notwendigen Attribute und Defaultwerte beachten
				directionShort = r[0]
				if (r[0] is None): directionShort = defaultDirectionShort
				directionText = r[5]
				if (r[5] is None): directionText = defaultDirectionText

				for sequenceNo in sequenceNoList:
					newTripStops[sequenceNo]["directionshort"] = directionShort
					newTripStops[sequenceNo]["directiontext"] = directionText

	def add_AInfoToTrip(self, fplanfahrtid, newTripStops):
		"""Die Funktion fügt zum Laufweg die notwendige A-Information hinzu

		fplanfahrtid - Id der Fahrplanfahrt
		newTripStops - angepasster Laufweg für diese Fahrt
		"""
		if ( fplanfahrtid in self.__fahrtAttributLookup):
			allAs = self.__fahrtAttributLookup[fplanfahrtid]
			for a in allAs:
				# ist die bitfieldno eine gueltige bitfieldno für heute 
				if (a[5] is None or (a[5] in self.__bitfieldnumbersOfDay) or a[5] == 0):
					sequenceNoList = self.getAffectedStops(a[1], a[2], a[3], a[4], newTripStops)
					# Belegung der notwendigen Attribute
					for sequenceNo in sequenceNoList:
						newTripStops[sequenceNo]["attributecode"].append(a[0])
						newTripStops[sequenceNo]["attributetext_de"].append(a[6])
						newTripStops[sequenceNo]["attributetext_fr"].append(a[7])
						newTripStops[sequenceNo]["attributetext_en"].append(a[8])
						newTripStops[sequenceNo]["attributetext_it"].append(a[9])

	def add_IInfoToTrip(self, fplanfahrtid, newTripStops):
		"""Die Funktion fügt zum Laufweg die notwendige I-Information hinzu

		fplanfahrtid - Id der Fahrplanfahrt
		newTripStops - angepasster Laufweg für diese Fahrt
		"""

		if ( fplanfahrtid in self.__fahrtInfoLookup):
			allIs = self.__fahrtInfoLookup[fplanfahrtid]
			for i in allIs:
				# ist die bitfieldno eine gueltige bitfieldno für heute
				if (i[5] is None or (i[5] in self.__bitfieldnumbersOfDay) or i[5] == 0):
					sequenceNoList = self.getAffectedStops(i[1], i[2], i[3], i[4], newTripStops)
					# Belegung der notwendigen Attribute
					for sequenceNo in sequenceNoList:
						newTripStops[sequenceNo]["infotextcode"].append(i[0])
						newTripStops[sequenceNo]["infotext_de"].append(i[6])
						newTripStops[sequenceNo]["infotext_fr"].append(i[7])
						newTripStops[sequenceNo]["infotext_en"].append(i[8])
						newTripStops[sequenceNo]["infotext_it"].append(i[9])

	def add_DurchBIToTrip(self, fplanfahrtid, newTripStops):
		"""Die Funktion fügt der Fahrt die Durchbindungsinformation hinzu
		Es wird hier nur der letzte Halt erweitert, wenn eine gueltige Durchbindung gefunden wird

		fplanfahrtid - Id der Fahrplanfahrt
		newTripStops - angepasster Laufweg für diese Fahrt
		"""
		if ( fplanfahrtid in self.__fahrtDurchbindungLookup):
			allDurchBi = self.__fahrtDurchbindungLookup[fplanfahrtid]
			for d in allDurchBi:
				# ist die bitfieldno eine gueltige bitfieldno für heute
				if (d[1] is None or (d[1] in self.__bitfieldnumbersOfDay) or d[1] == 0):
					# Belegen des Halts mit den Informationen der Durchbindung
					stopSequenceNo = self.getStopSequenceNo(d[0])
					if (stopSequenceNo > -1):					
						newTripStops[stopSequenceNo]["tripno_continued"] = d[2]
						newTripStops[stopSequenceNo]["operationalno_continued"] = d[3]
						newTripStops[stopSequenceNo]["stopno_continued"] = d[4]
					#else:
					#logger.info("\tDurchbindung: Halt {} im Lauf für fplanfahrtid {} nicht gefunden".format(d[0], fplanfahrtid))
