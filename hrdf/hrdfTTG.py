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
		self.__zugartLookup = dict()
		self.__bahnhofLookup = dict()

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

	def generateTT(self):
		""" Die Funktion generiert den gewünschten Tagesfahrplan bzgl. der Daten, die über setup() bestimmt wurden"""
		iErrorCnt = 0

		# Aufbau von LookUp-Tabellen für die entsprechenden Ergänzungen des Tagesfahrplan
		# Lookup für Zugarten
		sql_zugartLookup = "SELECT categorycode, classno, categoryno FROM HRDF_ZUGART_TAB WHERE fk_eckdatenid = %s"
		curZugart = self.__hrdfdb.connection.cursor()
		curZugart.execute(sql_zugartLookup, (self.__eckdatenid,))
		zugarten = curZugart.fetchall()
		for zugart in zugarten:
			self.__zugartLookup[zugart[0]] = zugart
		curZugart.close()

		# Lookup für Bahnhofsnamen
		sql_bahnhofLookup = "SELECT stopno, stopname, stopnamelong, stopnameshort, stopnamealias FROM HRDF_Bahnhof_TAB WHERE fk_eckdatenid = %s"
		curBahnhof = self.__hrdfdb.connection.cursor()
		curBahnhof.execute(sql_bahnhofLookup, (self.__eckdatenid,))
		bahnhhoefe = curBahnhof.fetchall()
		for bahnhof in bahnhhoefe:
			self.__bahnhofLookup[bahnhof[0]] = bahnhof
		curBahnhof.close()

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

			# Laden der Verkehrstagesdefinitionen für den Generierungstag als set() für schnellen Zugriff
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
			while True:				
				trips = curDayTrip.fetchmany(10000)
				if not trips:
					break
				rowCnt = len(trips)
				logger.info("generiere die nächsten {} Fahrten (bis jetzt {})".format(rowCnt, currentRowCnt))

				dailytimetable_strIO = StringIO()
				tripStops = dict()
				numberOfGeneratedTrips = 0;
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
							if (tripStop["attributecode"] is not None):
								strAttributecode = "{'" + "','".join(map(str,tripStop["attributecode"])) + "'}"
							if (tripStop["attributetext_de"] is not None):
								strAttributetextDE = "{'" + "','".join(map(str,tripStop["attributetext_de"])) + "'}"
							if (tripStop["attributetext_fr"] is not None):
								strAttributetextFR = "{'" + "','".join(map(str,tripStop["attributetext_fr"])) + "'}"
							if (tripStop["attributetext_en"] is not None):
								strAttributetextEN = "{'" + "','".join(map(str,tripStop["attributetext_en"])) + "'}"
							if (tripStop["attributetext_it"] is not None):
								strAttributetextIT = "{'" + "','".join(map(str,tripStop["attributetext_it"])) + "'}"

							# Infotexte
							strInfotextcode = ""
							strInfotextDE = ""
							strInfotextFR = ""
							strInfotextEN = ""
							strInfotextIT = ""
							if (tripStop["infotextcode"] is not None):
								strInfotextcode = '{"' + '","'.join(map(self.infohelp,tripStop["infotextcode"])) + '"}'
							if (tripStop["infotext_de"] is not None):
								strInfotextDE = '{"' + '","'.join(map(self.infohelp,tripStop["infotext_de"])) + '"}'
							if (tripStop["infotext_fr"] is not None):
								strInfotextFR = '{"' + '","'.join(map(self.infohelp,tripStop["infotext_fr"])) + '"}'
							if (tripStop["infotext_en"] is not None):
								strInfotextEN = '{"' + '","'.join(map(self.infohelp,tripStop["infotext_en"])) + '"}'
							if (tripStop["infotext_it"] is not None):
								strInfotextIT = '{"' + '","'.join(map(self.infohelp,tripStop["infotext_it"])) + '"}'
							

							# Schreiben des Datensatzes
							dataline = (self.__eckdatenid+';'
							+tripident+';'
							+str(trip[1])+';'
							+trip[2]+';'
							+str(trip[3])+';'
							+str(generationDay)+';'
							+str(tripStop["stop"][2])+';'
							+str(tripStop["stop"][0])+';'
							+tripStop["stop"][1]+';'
							+str(tripStop["stop"][0])+';'
							+tripStop["stop"][1]+';'
							+tripStop["arrstoppointtext"]+';'
							+tripStop["depstoppointtext"]+';'
							+arrdatetime+';'
							+depdatetime+';'
							+str(noentry)+';'
							+str(noexit)+';'
							+tripStop["categorycode"]+';'
							+str(tripStop["classno"])+';'
							+str(tripStop["categoryno"])+';'
							+tripStop["lineno"]+';'
							+tripStop["directionshort"]+';'
							+tripStop["directiontext"]+';'
							+strAttributecode+';'
							+strAttributetextDE+';'
							+strAttributetextFR+';'
							+strAttributetextEN+';'
							+strAttributetextIT+';'
							+strInfotextcode+';'
							+strInfotextDE+';'
							+strInfotextFR+';'
							+strInfotextEN+';'
							+strInfotextIT)
							#+'\n'
							#print(dataline)
							dailytimetable_strIO.write(dataline+'\n')
							numberOfGeneratedTrips += 1

					except Exception as err:
						iErrorCnt += 1
						logger.error("Die Fahrt {} konnte nicht generiert werden. Error:\n{}".format(tripident,err))

					
				# Alle Fahrten des Sets im IO abgelegt => speichern in DB
				tripStops.clear()
				if (numberOfGeneratedTrips > 0):
					curSaveTrip = self.__hrdfdb.connection.cursor()
					strCopy = "COPY HRDF_DailyTimeTable_TAB (fk_eckdatenid,tripident,tripno,operationalno,tripversion,"\
								"operatingday,stopsequenceno,stopident,stopname,stoppointident,stoppointname,arrstoppointtext,depstoppointtext,arrdatetime,depdatetime,noentry,noexit,"\
								"categorycode,classno,categoryno,lineno,directionshort,directiontext,"\
								"attributecode,attributetext_de,attributetext_fr,attributetext_en,attributetext_it,"\
								"infotextcode,infotext_de,infotext_fr,infotext_en,infotext_it)"\
								" FROM STDIN USING DELIMITERS ';' NULL AS ''"
					dailytimetable_strIO.seek(0)
					curSaveTrip.copy_expert(strCopy, dailytimetable_strIO)
					# ein Commit an dieser Stelle macht den Server-Cursor invalid
					curSaveTrip.close()
					logger.info("\t{} Tagesfahrplaneinträge wurden in der DB abgelegt".format(numberOfGeneratedTrips))
				dailytimetable_strIO.close()
				currentRowCnt += rowCnt
			
			curDayTrip.close()
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

		sql_selStops = "SELECT stopno, stopname, sequenceno, arrtime, deptime, tripno, operationalno, ontripsign FROM HRDF_FPlanFahrtLaufweg_TAB WHERE fk_fplanfahrtid = %s ORDER BY sequenceno"
		curStop = self.__hrdfdb.connection.cursor()
		curStop.execute(sql_selStops, (fplanfahrtid,))
		allTripStops = curStop.fetchall()
		curStop.close()

		# allTripStops enthält den kompletten Laufweg der Fahrt. Dieser wird über die AVE-Zeilen angepasst.
		sql_selVEData = "SELECT bitfieldno, fromstop, tostop, deptimefrom, arrtimeto FROM HRDF_FPlanFahrtVE_TAB WHERE fk_fplanfahrtid = %s ORDER BY id"
		curVE = self.__hrdfdb.connection.cursor()
		curVE.execute(sql_selVEData, (fplanfahrtid,))
		allVEs = curVE.fetchall()
		curVE.close()

		# lookup für Haltepositionstexte aufbauen
		sql_selGleisData = "SELECT distinct stopno, stoppointtext, stoppointtime, bitfieldno FROM HRDF_FPlanFahrt_TAB a, HRDF_GLEIS_TAB b WHERE a.id = %s AND a.fk_eckdatenid = b.fk_eckdatenid AND b.tripno = a.tripno AND b.operationalno = a.operationalno ORDER BY stopno"
		curGleis = self.__hrdfdb.connection.cursor()
		curGleis.execute(sql_selGleisData, (fplanfahrtid,))
		allGleise = curGleis.fetchall()
		curGleis.close()
		gleisLookup = dict()
		for gleis in allGleise:
			lookupkey = str(gleis[0])
			if (gleis[2] is not None): lookupkey = str(gleis[0])+"-"+str(gleis[2])
			if (gleis[3] is None or (gleis[3] in self.__bitfieldnumbersOfDay) or gleis[3] == 0):
				gleisLookup[lookupkey] = gleis

		# Erstellen des definitiven Laufwegs für diesen Tag alls dictonary um den Laufweg mit zusätzlichen Informationen ergänzen zu können
		for ve in allVEs:
			if (ve[0] is None or (ve[0] in self.__bitfieldnumbersOfDay) or ve[0] == 0):
				bTakeStop = False
				for tripStop in allTripStops:
					tripStopNo = tripStop[0]
					sequenceNo = tripStop[2]  # hier wird die eindeutige SequenceNo verwendet (tripStopNo kann öfter vorkommen)
					# stoppointtexte ermitteln
					arrstoppointtext = ""
					depstoppointtext = ""
					lookupkey = str(tripStopNo)
					if ( lookupkey in gleisLookup):
						arrstoppointtext = gleisLookup[lookupkey][1]
						depstoppointtext = gleisLookup[lookupkey][1]
					else:
						arrlookupkey = str(tripStopNo)+"-"+str(tripStop[3])
						if (arrlookupkey in gleisLookup):
							arrstoppointtext = gleisLookup[arrlookupkey][1]
						deplookupkey = str(tripStopNo)+"-"+str(tripStop[4])
						if (deplookupkey in gleisLookup):
							depstoppointtext = gleisLookup[deplookupkey][1]

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
								newTripStops[sequenceNo]["arrstoppointtext"] = arrstoppointtext
								newTripStops[sequenceNo]["depstoppointtext"] = depstoppointtext
							bTakeStop = False
					else:
						if (tripStopNo == ve[2] and tripStop[3] == ve[4]):
							if (tripStopNo not in newTripStops):
								newTripStops[sequenceNo] = dict(stop=tripStop) # letzter stop muss mit in die Liste
								newTripStops[sequenceNo]["arrstoppointtext"] = arrstoppointtext
								newTripStops[sequenceNo]["depstoppointtext"] = depstoppointtext
							bTakeStop = False
					# alle stops übernehmen solange bTakeStop gesetzt ist
					if (bTakeStop):
						if (sequenceNo not in newTripStops):
							newTripStops[sequenceNo] = dict(stop=tripStop)
							newTripStops[sequenceNo]["arrstoppointtext"] = arrstoppointtext
							newTripStops[sequenceNo]["depstoppointtext"] = depstoppointtext


					if (sequenceNo in newTripStops):
						# Initialisieren der zusätzlichen Felder des TripStops
						newTripStops[sequenceNo]["categorycode"] = ""
						newTripStops[sequenceNo]["classno"] = ""
						newTripStops[sequenceNo]["categoryno"] = ""
						newTripStops[sequenceNo]["lineno"] = ""
						# Initialisierung der Richtungsangaben erfolgt in der entsprechenden Funktion
						newTripStops[sequenceNo]["attributecode"] = None
						newTripStops[sequenceNo]["attributetext_de"] = None
						newTripStops[sequenceNo]["attributetext_fr"] = None
						newTripStops[sequenceNo]["attributetext_en"] = None
						newTripStops[sequenceNo]["attributetext_it"] = None
						newTripStops[sequenceNo]["infotextcode"] = None
						newTripStops[sequenceNo]["infotext_de"] = None
						newTripStops[sequenceNo]["infotext_fr"] = None
						newTripStops[sequenceNo]["infotext_en"] = None
						newTripStops[sequenceNo]["infotext_it"] = None

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

	def add_GInfoToTrip(self, fplanfahrtid, newTripStops):
		"""Die Funktion fügt zum Laufweg die notwendige G-Information hinzu

		fplanfahrtid - Id der Fahrplanfahrt
		newTripStops - angepasster Laufweg für diese Fahrt
		"""
		#sql_selGData = "SELECT categorycode, fromstop, tostop, deptimefrom, arrtimeto FROM HRDF_FPlanFahrtG_TAB WHERE fk_fplanfahrtid = %s ORDER BY id"
		sql_selGData = "SELECT a.categorycode, fromstop, tostop, deptimefrom, arrtimeto, b.classno, b.categoryno "\
					   "  FROM HRDF_FPlanFahrtG_TAB a, "\
					   "       HRDF_ZUGART_TAB b "\
					   " WHERE a.fk_fplanfahrtid = %s "\
					   "   and a.fk_eckdatenid = b.fk_eckdatenid "\
					   "   and a.categorycode = b.categorycode "\
					   " ORDER BY a.id"
		curG = self.__hrdfdb.connection.cursor()
		curG.execute(sql_selGData, (fplanfahrtid,))
		allGs = curG.fetchall()
		curG.close()

		if (len(allGs) == 1):
			for tripStop in newTripStops.values():
				tripStop["categorycode"] = allGs[0][0]
				tripStop["classno"] = allGs[0][5]
				tripStop["categoryno"] = allGs[0][6]
		else:
			for g in allGs:
				sequenceNoList = self.getAffectedStops(g[1], g[2], g[3], g[4], newTripStops)
				# Belegung der notwendigen Attribute
				for sequenceNo in sequenceNoList:
					newTripStops[sequenceNo]["categorycode"] = g[0]
					newTripStops[sequenceNo]["classno"] = g[5]
					newTripStops[sequenceNo]["categoryno"] = g[6]


	def add_LInfoToTrip(self, fplanfahrtid, newTripStops):
		"""Die Funktion fügt zum Laufweg die notwendige L-Information hinzu

		fplanfahrtid - Id der Fahrplanfahrt
		newTripStops - angepasster Laufweg für diese Fahrt
		"""
		sql_selLData = "SELECT lineno, fromstop, tostop, deptimefrom, arrtimeto FROM HRDF_FPlanFahrtL_TAB WHERE fk_fplanfahrtid = %s ORDER BY id"
		curL = self.__hrdfdb.connection.cursor()
		curL.execute(sql_selLData, (fplanfahrtid,))
		allLs = curL.fetchall()
		curL.close()

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
		sql_selRData = "SELECT a.directionshort, fromstop, tostop, deptimefrom, arrtimeto, b.directiontext "\
					   "  FROM HRDF_FPlanFahrtR_TAB a "\
					   "       LEFT OUTER JOIN HRDF_Richtung_TAB b ON b.directioncode = a.directioncode and a.fk_eckdatenid = b.fk_eckdatenid "\
					   " WHERE a.fk_fplanfahrtid = %s "\
					   " ORDER BY a.id"
		curR = self.__hrdfdb.connection.cursor()
		curR.execute(sql_selRData, (fplanfahrtid,))
		allRs = curR.fetchall()
		curR.close()

		# Initialisieren mit Defaultwerten
		defaultDirectionShort = ""
		defaultDirectionText = ""
		# Richtungstext bevorzugt über Lookup-Tabelle finden
		lastEntry = list(newTripStops.items())[-1][1]
		lastStopNo = lastEntry["stop"][0]
		if (lastStopNo in self.__bahnhofLookup):
			defaultDirectionText = self.__bahnhofLookup[lastStopNo][1]
		else:
			defaultDirectionText = lastEntry["stop"][1]

		for tripStop in newTripStops.values():
			tripStop["directionshort"] = defaultDirectionShort
			tripStop["directiontext"] = defaultDirectionText

		# Auch wenn nur ein Datensatz vorhanden ist muss die "kompliziertere" Variante der Findung des richtigen Stops erfolgen
		for r in allRs:
			sequenceNoList = self.getAffectedStops(r[1], r[2], r[3], r[4], newTripStops)
			# Belegung der notwendigen Attribute und Defaultwerte beachten
			directionShort = r[0]
			if (r[0] is None):
				directionShort = defaultDirectionShort
			directionText = r[5]
			if (r[5] is None):
				directionText = defaultDirectionText

			for sequenceNo in sequenceNoList:
				newTripStops[sequenceNo]["directionshort"] = directionShort
				newTripStops[sequenceNo]["directiontext"] = directionText


	def add_AInfoToTrip(self, fplanfahrtid, newTripStops):
		"""Die Funktion fügt zum Laufweg die notwendige A-Information hinzu

		fplanfahrtid - Id der Fahrplanfahrt
		newTripStops - angepasster Laufweg für diese Fahrt
		"""
		sql_selAData = "SELECT array_agg(a.attributecode ORDER BY b.outputprio, b.outputpriosort) as attributecodeArray, fromstop, tostop, deptimefrom, arrtimeto, bitfieldno, "\
						"       array_agg(b.attributetext ORDER BY b.outputprio, b.outputpriosort) as text_de, "\
						"       array_agg(c.attributetext ORDER BY c.outputprio, c.outputpriosort) as text_fr, "\
						"       array_agg(d.attributetext ORDER BY d.outputprio, d.outputpriosort) as text_en, "\
						"       array_agg(e.attributetext ORDER BY e.outputprio, e.outputpriosort) as text_it, "\
						"       array_agg(b.stopcontext ORDER BY b.outputprio, b.outputpriosort) as stopcontext, "\
						"       array_agg(b.outputforsection ORDER BY b.outputprio, b.outputpriosort) as outputforsection, "\
						"       array_agg(b.outputforcomplete ORDER BY b.outputprio, b.outputpriosort) as outputforcomplete "\
						"  FROM HRDF_FPlanFahrtA_TAB a "\
						"       LEFT OUTER JOIN HRDF_Attribut_TAB b ON b.attributecode = a.attributecode and a.fk_eckdatenid = b.fk_eckdatenid and b.languagecode = 'de' "\
						"  LEFT OUTER JOIN HRDF_Attribut_TAB c ON c.attributecode = a.attributecode and a.fk_eckdatenid = c.fk_eckdatenid and c.languagecode = 'fr' "\
						"	  LEFT OUTER JOIN HRDF_Attribut_TAB d ON d.attributecode = a.attributecode and a.fk_eckdatenid = d.fk_eckdatenid and d.languagecode = 'en' "\
						"	  LEFT OUTER JOIN HRDF_Attribut_TAB e ON e.attributecode = a.attributecode and a.fk_eckdatenid = e.fk_eckdatenid and e.languagecode = 'it' "\
						"  WHERE a.fk_fplanfahrtid = %s "\
						"  GROUP by fromstop, tostop, deptimefrom, arrtimeto, b.languagecode, bitfieldno, fk_fplanfahrtid "
		curA = self.__hrdfdb.connection.cursor()
		curA.execute(sql_selAData, (fplanfahrtid,))
		allAs = curA.fetchall()
		curA.close()

		if (len(allAs) > 0):			
			for a in allAs:
				# ist die bitfieldno eine gueltige bitfieldno für heute 
				if (a[5] is None or (a[5] in self.__bitfieldnumbersOfDay) or a[5] == 0):
					sequenceNoList = self.getAffectedStops(a[1], a[2], a[3], a[4], newTripStops)
					# Belegung der notwendigen Attribute
					for sequenceNo in sequenceNoList:
						newTripStops[sequenceNo]["attributecode"] = a[0]
						newTripStops[sequenceNo]["attributetext_de"] = a[6]
						newTripStops[sequenceNo]["attributetext_fr"] = a[7]
						newTripStops[sequenceNo]["attributetext_en"] = a[8]
						newTripStops[sequenceNo]["attributetext_it"] = a[9]


	def add_IInfoToTrip(self, fplanfahrtid, newTripStops):
		"""Die Funktion fügt zum Laufweg die notwendige I-Information hinzu

		fplanfahrtid - Id der Fahrplanfahrt
		newTripStops - angepasster Laufweg für diese Fahrt
		"""
		sql_selIData = "SELECT array_agg(a.infotextcode) as infotextArray, fromstop, tostop, deptimefrom, arrtimeto, bitfieldno, "\
						"       array_agg(b.infotext) as text_de, "\
						"       array_agg(c.infotext) as text_fr, "\
						"       array_agg(d.infotext) as text_en, "\
						"       array_agg(e.infotext) as text_it "\
						"  FROM HRDF_FPlanFahrtI_TAB a "\
						"       LEFT OUTER JOIN HRDF_Infotext_TAB b ON b.infotextno = a.infotextno and a.fk_eckdatenid = b.fk_eckdatenid and b.languagecode = 'de' "\
						"   	LEFT OUTER JOIN HRDF_Infotext_TAB c ON c.infotextno = a.infotextno and a.fk_eckdatenid = c.fk_eckdatenid and c.languagecode = 'fr' "\
						"	   LEFT OUTER JOIN HRDF_Infotext_TAB d ON d.infotextno = a.infotextno and a.fk_eckdatenid = d.fk_eckdatenid and d.languagecode = 'en' "\
						"	   LEFT OUTER JOIN HRDF_Infotext_TAB e ON e.infotextno = a.infotextno and a.fk_eckdatenid = e.fk_eckdatenid and e.languagecode = 'it' "\
						"  WHERE a.fk_fplanfahrtid = %s "\
						"  GROUP by fromstop, tostop, deptimefrom, arrtimeto, bitfieldno"
		curI = self.__hrdfdb.connection.cursor()
		curI.execute(sql_selIData, (fplanfahrtid,))
		allIs = curI.fetchall()
		curI.close()

		if (len(allIs) > 0):
			for i in allIs:
				# ist die bitfieldno eine gueltige bitfieldno für heute
				if (i[5] is None or (i[5] in self.__bitfieldnumbersOfDay) or i[5] == 0):
					sequenceNoList = self.getAffectedStops(i[1], i[2], i[3], i[4], newTripStops)
					# Belegung der notwendigen Attribute
					for sequenceNo in sequenceNoList:
						newTripStops[sequenceNo]["infotextcode"] = i[0]
						newTripStops[sequenceNo]["infotext_de"] = i[6]
						newTripStops[sequenceNo]["infotext_fr"] = i[7]
						newTripStops[sequenceNo]["infotext_en"] = i[8]
						newTripStops[sequenceNo]["infotext_it"] = i[9]

