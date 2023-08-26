import psycopg2
from datetime import datetime, date, timedelta, time
from hrdf.hrdflog import logger

class HrdfTTGCache:
	""" Klasse stellt einen Daten-Cache für Fahrplandaten zur Verfügung """

	def __init__(self, db):
		"""
		db - HRDF-DB
		"""
		self.__hrdfdb = db
		# Listen, Strukturen für schnellen Zugriff auf Daten während der Generierung
		self.__bitfieldnumbersOfDay = dict()
		self.__fahrtZugartLookup = dict()
		self.__bahnhofLookup = dict()
		self.__gleisLookup = dict()
		self.__gleisLookupDay = dict()
		self.__allTripStopsLookup = dict()
		self.__allVEsLookup = dict()
		self.__fahrtLinienLookup = dict()
		self.__fahrtLinienErweitertLookup = dict()
		self.__fahrtRichtungLookup = dict()
		self.__fahrtAttributLookup = dict()
		self.__fahrtInfoLookup = dict()
		self.__fahrtDurchbindungLookup = dict()

	def lookupBitfieldnumbersOfDay(self, day):
		""" Lookup auf set mit Bitfeld-Nummern für den angegebenen Tag """
		if (day in self.__bitfieldnumbersOfDay):
			return self.__bitfieldnumbersOfDay[day]
		else:
			return None

	def lookupFahrtZugart(self, fplanfahrtid):
		""" Lookup auf die Zugartliste für die Fahrt """
		if (fplanfahrtid in self.__fahrtZugartLookup):
			return self.__fahrtZugartLookup[fplanfahrtid]
		else:
			return None

	def lookupBahnhof(self, stopno):
		""" Lookup auf die Bahnhofs-Informationen für die Fahrt """
		if (stopno in self.__bahnhofLookup):
			return self.__bahnhofLookup[stopno]			
		else:
			return None

	def lookupGleisText(self, gleisKey, generationDay):
		""" Lookup der GleisText-Daten für die Fahrt an diesem Tag """
		gleistext = ""
		if (gleisKey in self.__gleisLookup):
			gleistext = self.__gleisLookup[gleisKey]
		else:
			if (generationDay in self.__gleisLookupDay):
				if (gleisKey in self.__gleisLookupDay[generationDay]):
					gleistext = self.__gleisLookupDay[generationDay][gleisKey]
		return gleistext

	def lookupAllTripStops(self, fplanfahrtid):
		""" Lookup aller Stops einer Fahrt """
		if (fplanfahrtid in self.__allTripStopsLookup):
			return self.__allTripStopsLookup[fplanfahrtid]
		else:
			return None

	def lookupAllVEs(self, fplanfahrtid):
		""" Lookup aller VEs einer Fahrt """
		if (fplanfahrtid in self.__allVEsLookup):
			return self.__allVEsLookup[fplanfahrtid]
		else:
			return None
	
	def lookupFahrtLinien(self, fplanfahrtid):
		""" Lookup aller Linieninformation zu einer Fahrt """
		if ( fplanfahrtid in self.__fahrtLinienLookup):
			return self.__fahrtLinienLookup[fplanfahrtid]
		else:
			return None

	def lookupFahrtRichtung(self, fplanfahrtid):
		""" Lookup aller Richtungsinformation zu einer Fahrt """
		if (fplanfahrtid in self.__fahrtRichtungLookup):
			return self.__fahrtRichtungLookup[fplanfahrtid]
		else:
			return None

	def lookupFahrtAttribut(self, fplanfahrtid):
		""" Lookup aller Attribute zu einer Fahrt """
		if (fplanfahrtid in self.__fahrtAttributLookup):
			return self.__fahrtAttributLookup[fplanfahrtid]
		else:
			return None
	
	def lookupFahrtInfo(self, fplanfahrtid):
		""" Lookup aller Infotexte zu einer Fahrt """
		if (fplanfahrtid in self.__fahrtInfoLookup):
			return self.__fahrtInfoLookup[fplanfahrtid]
		else:
			return None

	def lookupFahrtDuBi(self, fplanfahrtid):
		""" Lookup aller Durchbindungsdaten zu einer Fahrt """
		if (fplanfahrtid in self.__fahrtDurchbindungLookup):
			return self.__fahrtDurchbindungLookup[fplanfahrtid]
		else:
			return None

	def createCacheData(self, eckdatenid, generateFrom, generateTo):
		""" Die Funktion erstellt die Daten des Fahrplan-Cache """

		# Lookup der Verkehrstagesdefinitionen
		# für jeden erforderlichen Tag werden die Verkehrstagesdefinitionen geladen
		logger.info("Lookup der Verkehrstagesdefinitionen aufbauen")
		self.__bitfieldnumbersOfDay.clear()
		dayCnt = (generateTo - generateFrom).days
		i = 0
		while (i<=dayCnt):
			# Laden der Verkehrstagesdefinitionen für den Generierungstag als set() für schnellen Zugriff/Abfrage auf Existenz
			generationDay = generateFrom + timedelta(days=i)
			sql_selBitfieldNos = "SELECT bitfieldno FROM HRDF_Bitfeld_TAB where bitfieldarray @> ARRAY[%s::date] AND fk_eckdatenid = %s"
			curBits = self.__hrdfdb.connection.cursor()
			curBits.execute(sql_selBitfieldNos, (str(generationDay), eckdatenid))
			bitfieldNos = curBits.fetchall()
			bitfieldnumbers = set()
			for bitfield in bitfieldNos:
				bitfieldnumbers.add(bitfield[0])
			curBits.close()
			self.__bitfieldnumbersOfDay[generationDay] = bitfieldnumbers
			# Tageszähler hochzählen und nächsten gewünschten Tag generieren
			i += 1
			
		# Lookup für Zugarten der Fahrplanfahrten
		logger.info("Lookup für Zugarten aufbauen")
		self.__fahrtZugartLookup.clear()
		sql_zugartLookup = "SELECT a.fk_fplanfahrtid, a.categorycode, fromstop, tostop, deptimefrom, arrtimeto, b.classno, b.categoryno"\
						   "  FROM HRDF_FPlanFahrtG_TAB a, "\
						   "       HRDF_ZUGART_TAB b "\
						   " WHERE a.fk_eckdatenid = %s "\
						   "   and a.fk_eckdatenid = b.fk_eckdatenid "\
						   "   and a.categorycode = b.categorycode "\
						   " ORDER BY a.fk_fplanfahrtid, a.id"

		curFahrtZugart = self.__hrdfdb.connection.cursor()
		curFahrtZugart.execute(sql_zugartLookup, (eckdatenid,))
		fahrtZugarten = curFahrtZugart.fetchall()
		logger.debug("Es werden {} Zugarten analysiert".format(len(fahrtZugarten)))
		curFahrtZugart.close()
		for fahrtZugart in fahrtZugarten:
			fahrtId = fahrtZugart[0]
			if ( fahrtId in self.__fahrtZugartLookup):
				self.__fahrtZugartLookup[fahrtId].append(fahrtZugart)
			else:
				zugartList = list()
				zugartList.append(fahrtZugart);
				self.__fahrtZugartLookup[fahrtId] = zugartList
		fahrtZugarten.clear()

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
		curBahnhof.execute(sql_bahnhofLookup, (eckdatenid,))		
		bahnhoefe = curBahnhof.fetchall()
		logger.debug("Es werden {} Bahnhöfe analysiert".format(len(bahnhoefe)))
		curBahnhof.close()
		for bahnhof in bahnhoefe:
			self.__bahnhofLookup[bahnhof[0]] = bahnhof
		bahnhoefe.clear()

		# Lookup für Haltepositionstexte aufbauen (a.id zu beginn ist schneller als es wegzulassen oder am Ende zu stellen)
		# key => <FahrtId>-<StopNo>[-<StopPointTime>]
		logger.info("Lookup für Haltepositionstexte aufbauen")
		# Um das SQL-Script zu optimieren (185M rows), prüfen wir, ob einer der zu generierenden Tage im Bitfieldarray enthalten ist
		logger.debug("Erzeugen eines Datums-Arrays der relevanten Tage für optimiertes SELECT-Statement")
		generationDatesArray = []
		i = 0
		while (i<=dayCnt):
			generationDay = generateFrom + timedelta(days=i)
			generationDatesArray.append(generationDay)
			i += 1
		logger.debug("generationDatesArray contains: "+str(generationDatesArray))
		sql_selGleisData = "SELECT distinct a.id, a.id::varchar||'-'||stopno::varchar||coalesce('-'||stoppointtime::varchar,'') as key, stoppointtext, b.bitfieldno "\
						   "  FROM HRDF_FPlanFahrt_TAB a, HRDF_GLEIS_TAB b, HRDF_BITFELD_TAB c "\
						   " WHERE a.fk_eckdatenid = %s "\
						   "   AND a.fk_eckdatenid = b.fk_eckdatenid "\
						   "   AND a.fk_eckdatenid = c.fk_eckdatenid "\
						   "   AND b.tripno = a.tripno "\
						   "   AND b.operationalno = a.operationalno "\
						   "   AND b.bitfieldno = c.bitfieldno "\
						   "   AND c.bitfieldarray && %s::date[] "
		curGleis = self.__hrdfdb.connection.cursor()
		curGleis.execute(sql_selGleisData, (eckdatenid, generationDatesArray,))
		allGleise = curGleis.fetchall()
		curGleis.close()
		logger.debug("Es werden {} Haltepositionstexte analysiert".format(len(allGleise)))
		for gleis in allGleise:
			if (gleis[3] is None or gleis[3] == 0):
				self.__gleisLookup[gleis[1]] = gleis[2]
			else:
				# Gleisangabe ist nur für einen bestimmten Tag => gehört dieser zur Generierungszeitspanne?
				# Wenn ja dann baue eine Gleis-Tages-LookupTabelle auf
				i = 0
				while (i<=dayCnt):
					generationDay = generateFrom + timedelta(days=i)
					if ( generationDay in self.__bitfieldnumbersOfDay):
						if (gleis[3] in self.__bitfieldnumbersOfDay[generationDay]):
							if ( generationDay in self.__gleisLookupDay):
								self.__gleisLookupDay[generationDay][gleis[1]] = gleis[2]
							else:
								gleisLookup = dict()
								gleisLookup[gleis[1]] = gleis[2]
								self.__gleisLookupDay[generationDay] = gleisLookup
					# Tageszähler hochzählen und nächsten gewünschten Tag generieren
					i += 1
		allGleise.clear()

		# Lookup für allTripStops erstellen. allTripStops einer Fahrt enthält den kompletten Laufweg der Fahrt.
		logger.info("Lookup für Laufwege der Fahrten aufbauen")
		sql_selStops = "SELECT stopno, stopname, sequenceno, arrtime, deptime, tripno, operationalno, ontripsign, "\
					   "       fk_fplanfahrtid||'-'||stopno as gleislookup, "\
					   "	   fk_fplanfahrtid||'-'||stopno||'-'||arrtime as gleislookupArr, "\
					   "       fk_fplanfahrtid||'-'||stopno||'-'||deptime as gleislookupDep, "\
					   "       fk_fplanfahrtid "\
		               "  FROM HRDF_FPlanFahrtLaufweg_TAB WHERE fk_eckdatenid = %s ORDER BY fk_fplanfahrtid, sequenceno"
		curStop = self.__hrdfdb.connection.cursor()
		curStop.execute(sql_selStops, (eckdatenid,))
		allTripStops = curStop.fetchall()
		logger.debug("Es werden {} Fahrtlaufwege analysiert".format(len(allTripStops)))
		curStop.close()
		for tripStop in allTripStops:
			if (tripStop[11] in self.__allTripStopsLookup):
				self.__allTripStopsLookup[tripStop[11]].append(tripStop)
			else:
				tripStopList = list()
				tripStopList.append(tripStop);
				self.__allTripStopsLookup[tripStop[11]] = tripStopList
		allTripStops.clear()

		# Lookup für allVEs erstellen. allVEs einer Fahrt enthält alle Verkehrstagesdefinitionen einer Fahrt
		logger.info("Lookup für Verkehrstagesinformation der Fahrten aufbauen")
		sql_selVEData = "SELECT bitfieldno, fromstop, tostop, deptimefrom, arrtimeto, fk_fplanfahrtid FROM HRDF_FPlanFahrtVE_TAB WHERE fk_eckdatenid = %s ORDER BY fk_fplanfahrtid, id"
		curVE = self.__hrdfdb.connection.cursor()
		curVE.execute(sql_selVEData, (eckdatenid,))
		allVEs = curVE.fetchall()
		logger.debug("Es werden {} Verkehrstagesinformationen analysiert".format(len(allVEs)))
		curVE.close()
		for fahrtVE in allVEs:
			if (fahrtVE[5] in self.__allVEsLookup):
				self.__allVEsLookup[fahrtVE[5]].append(fahrtVE)
			else:
				VEList = list()
				VEList.append(fahrtVE)
				self.__allVEsLookup[fahrtVE[5]] = VEList
		allVEs.clear()

		# Lookup für Linieninformationen der Fahrten
		logger.info("Lookup für Linieninformationen der Fahrten aufbauen")
		sql_selLData = "SELECT lineno, fromstop, tostop, deptimefrom, arrtimeto, fk_fplanfahrtid, ltrim(lineindex, '#') FROM HRDF_FPlanFahrtL_TAB WHERE fk_eckdatenid = %s ORDER BY fk_fplanfahrtid, id"
		curL = self.__hrdfdb.connection.cursor()
		curL.execute(sql_selLData, (eckdatenid,))
		allLs = curL.fetchall()
		logger.debug("Es werden {} Linieninformationen analysiert".format(len(allLs)))
		curL.close()
		for fahrtL in allLs:
			if (fahrtL[5] in self.__fahrtLinienLookup):
				self.__fahrtLinienLookup[fahrtL[5]].append(fahrtL)
			else:
				LList = list()
				LList.append(fahrtL)
				self.__fahrtLinienLookup[fahrtL[5]] = LList
		allLs.clear()

		# Lookup für erweiterte Linieninformationen der Fahrten
		logger.info("Lookup für Linieninformationen der Fahrten mit erweiterten Linieninformationen anreichern")
		sql_selELData = "SELECT line_index, line_key, number_intern, name_short, name_short_index, name_long, name_long_index, color_font, color_back FROM HRDF_Linie_TAB WHERE fk_eckdatenid = %s ORDER BY id"
		curEL = self.__hrdfdb.connection.cursor()
		curEL.execute(sql_selELData, (eckdatenid,))
		allELs = curEL.fetchall()
		logger.debug("Es werden {} erweiterte Linieninformationen analysiert".format(len(allELs)))
		curEL.close()
		for fahrtEL in allELs:
			fahrtELindex = fahrtEL[0]
			if (fahrtELindex in self.__fahrtLinienErweitertLookup):
				self.__fahrtLinienErweitertLookup[fahrtELindex].append(fahrtEL)
			else:
				ELList = list()
				ELList.append(fahrtEL)
				self.__fahrtLinienErweitertLookup[fahrtELindex] = ELList
		for fahrtL in self.__fahrtLinienLookup:
			if (fahrtL[6] is not None):
				fahrtLindex = fahrtL[6]
				if (fahrtLindex in self.__fahrtLinienErweitertLookup):
					self.__fahrtLinienLookup[fahrtLindex] = self.__fahrtLinienErweitertLookup[fahrtLindex][3]
		allLs.clear()

		# Lookup für Richtungstexte der Fahrten
		logger.info("Lookup für Richtungstexte der Fahrten aufbauen")
		sql_selRData = "SELECT a.directionshort, fromstop, tostop, deptimefrom, arrtimeto, b.directiontext, fk_fplanfahrtid "\
					   "  FROM HRDF_FPlanFahrtR_TAB a "\
					   "       LEFT OUTER JOIN HRDF_Richtung_TAB b ON b.fk_eckdatenid = a.fk_eckdatenid AND a.directioncode = b.directioncode"\
					   " WHERE a.fk_eckdatenid = %s "\
					   " ORDER BY a.fk_fplanfahrtid, a.id"
		curR = self.__hrdfdb.connection.cursor()
		curR.execute(sql_selRData, (eckdatenid,))
		allRs = curR.fetchall()
		logger.debug("Es werden {} Richtungstexte analysiert".format(len(allRs)))
		curR.close()
		for fahrtR in allRs:
			if (fahrtR[6] in self.__fahrtRichtungLookup):
				self.__fahrtRichtungLookup[fahrtR[6]].append(fahrtR)
			else:
				RList = list()
				RList.append(fahrtR)
				self.__fahrtRichtungLookup[fahrtR[6]] = RList
		allRs.clear()

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
		curA.execute(sql_selAData, (eckdatenid,))
		allAs = curA.fetchall()
		logger.debug("Es werden {} Fahrtattribute analysiert".format(len(allAs)))
		curA.close()
		for fahrtA in allAs:
			if (fahrtA[13] in self.__fahrtAttributLookup):
				self.__fahrtAttributLookup[fahrtA[13]].append(fahrtA)
			else:
				AList = list()
				AList.append(fahrtA)
				self.__fahrtAttributLookup[fahrtA[13]] = AList
		allAs.clear()

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
		curI.execute(sql_selIData, (eckdatenid,))
		allIs = curI.fetchall()
		logger.debug("Es werden {} Fahrtinfotexte analysiert".format(len(allIs)))
		curI.close()
		for fahrtI in allIs:
			if (fahrtI[10] in self.__fahrtInfoLookup):
				self.__fahrtInfoLookup[fahrtI[10]].append(fahrtI)
			else:
				IList = list()
				IList.append(fahrtI)
				self.__fahrtInfoLookup[fahrtI[10]] = IList
		allIs.clear()

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
		curDurchBi.execute(sql_selDurchBiData, (eckdatenid,))
		allDurchBi = curDurchBi.fetchall()
		logger.debug("Es werden {} Durchbindungsinformation der Fahrten analysiert".format(len(allDurchBi)))
		curDurchBi.close()
		for fahrtDuBI in allDurchBi:
			if (fahrtDuBI[6] in self.__fahrtDurchbindungLookup):
				self.__fahrtDurchbindungLookup[fahrtDuBI[6]].append(fahrtDuBI)
			else:
				DuBiList = list()
				DuBiList.append(fahrtDuBI)
				self.__fahrtDurchbindungLookup[fahrtDuBI[6]] = DuBiList
		allDurchBi.clear()		