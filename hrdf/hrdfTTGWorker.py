import psycopg2
from datetime import datetime, date, timedelta, time
from io import StringIO
from hrdf.hrdfdb import HrdfDB
from hrdf.hrdfTTGCache import HrdfTTGCache
from hrdf.hrdflog import logger
from threading import Thread
from queue import Queue, Empty, Full

class HrdfTTGWorker(Thread):
	"""
	Worker-Thread der einen Teil eines Tagesfahrplans generiert
	Der Worker-Thread hat ein eigenes DB-Objekt und baut seine eigene Verbindung zur Datenbank auf
	
	"""
	
	def __init__(self, db, threadID, threadName, workqueue, commqueue, responsequeue, ttgcache):
		Thread.__init__(self)
		self.__threadID = threadID
		self.__name = threadName
		self.__workQueue = workqueue
		self.__commQueue = commqueue
		self.__responseQueue = responsequeue

		self.__hrdfdb = HrdfDB(db.dbname, db.host, db.user, db.password)
		self.__ttgcache = HrdfTTGCache(self.__hrdfdb)
		self.__ttgcache = ttgcache
		self.__stopSequenceLookup = dict()
		self.__bitfieldnumbers = set()

	def run(self):
		""" Worker-Methode des Threads. Diese wird durch start() aufgerufen """
		if (self.__hrdfdb.connect()):
			hasToExit = False
			while not hasToExit:
				try:
					dataItem = self.__workQueue.get(True, 0.100)
					self.processTrips(dataItem["eckdatenid"], dataItem["day"], dataItem["trips"])
					self.__workQueue.task_done()
				except Empty:
					pass
					#logger.info("Thread {}-{} no work".format(self.__threadID, self.__name))

				try:
					hasToExit = self.__commQueue.get(True, 0.010)
					self.__commQueue.put(hasToExit);
				except Empty:
					pass
		else:
			logger.error("{} konnte keine Verbindung zur Datenbank aufbauen".format(self.__name))

	def infohelp(self, text):
		""" Die Funktion korrigiert den Text (Infotext) mit entsprechenden Escape-Sequencen """
		return str(text).replace(";", "\;").replace("\"", "\\\\\"").replace("\n", "\\n")

	def processTrips(self, eckdatenid, generationDay, trips):
		""" Die Funktion generiert den Tagesfahrplan für die übergebenen Trips am gewünschten Tag"""
		if (len(trips) > 1):
			#logger.error("{}: bearbeitet {} Fahrten".format(self.__name, len(trips)))
			tripStops = dict()		
			dailytimetable_strIO = StringIO()							
			numberOfGeneratedTrips = 0
			iErrorCnt = 0
			for trip in trips:
				tripStops.clear()					
				tripident = "{}-{}-{}".format(trip[1],trip[2],trip[3])
				try:
					self.generateTrip(trip, tripStops, generationDay)
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
						dailytimetable_strIO.write(eckdatenid)
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

			# Alle Fahrten des Sets im IO abgelegt => Zurückgabe an den Main-Thread
			logger.info("\t{}: {:%d.%m.%Y} => {} Tagesfahrplaneinträge erstellt ...".format(self.__name, generationDay, numberOfGeneratedTrips))				
			# Ergebnis liefern
			dailytimetable_strIO.seek(0)
			self.__responseQueue.put(dict(day=generationDay, data=dailytimetable_strIO.getvalue()))
			dailytimetable_strIO.close()
			tripStops.clear()

	def generateTrip(self, trip, newTripStops, generationDay):
		""" Die Funktion generiert die Angaben zur übergebenen Fahrt

		trip - Datenzeile der Tabelle HRDF_FPlanFahrt_TAB mit einem Array der gültigen BitfieldNos (Verkehrstagesschlüssel)
		newTripStops - Dictonary, welches den Laufweg mit Zusatzinformationen enthält (=> sollte leer sein?!)
		generationDay - Tag für den diese Trips generiert werden sollen
		"""
		bReturn = True
		#logger.info("generiere Zug {}".format(trip))
		fplanfahrtid = trip[0]

		allTripStops = self.__ttgcache.lookupAllTripStops(fplanfahrtid)
		allVEs = self.__ttgcache.lookupAllVEs(fplanfahrtid)
		if ((allVEs is not None) and (allTripStops is not None)):

			# Leeren der stopSequenceLookup, da diese nur für die aktuelle Fahrt gilt
			self.__stopSequenceLookup.clear()
			self.__bitfieldnumbers = self.__ttgcache.lookupBitfieldnumbersOfDay(generationDay)

			# Erstellen des definitiven Laufwegs für diesen Tag alls dictonary um den Laufweg mit zusätzlichen Informationen ergänzen zu können
			for ve in allVEs:
				if (ve[0] is None or (ve[0] in self.__bitfieldnumbers) or ve[0] == 0):
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
							arrstoppointtext = self.__ttgcache.lookupGleisText(tripStop[8], generationDay)
							if ( arrstoppointtext is not ""):
								depstoppointtext = arrstoppointtext
							else:
								arrstoppointtext = self.__ttgcache.lookupGleisText(tripStop[9], generationDay)
								depstoppointtext = self.__ttgcache.lookupGleisText(tripStop[10], generationDay)
								
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
							bahnhofLookup = self.__ttgcache.lookupBahnhof(tripStopNo)
							if (bahnhofLookup is not None):
								newTripStops[sequenceNo]["longitude_geo"] = bahnhofLookup[8]
								newTripStops[sequenceNo]["latitude_geo"] = bahnhofLookup[9]
								newTripStops[sequenceNo]["altitude_geo"] = bahnhofLookup[10]
								newTripStops[sequenceNo]["transfertime1"] = bahnhofLookup[5]
								newTripStops[sequenceNo]["transfertime2"] = bahnhofLookup[6]
								newTripStops[sequenceNo]["transferprio"] = bahnhofLookup[7]
							else:
								newTripStops[sequenceNo]["longitude_geo"] = None
								newTripStops[sequenceNo]["latitude_geo"] = None
								newTripStops[sequenceNo]["altitude_geo"] = None
								newTripStops[sequenceNo]["transfertime1"] = None
								newTripStops[sequenceNo]["transfertime2"] = None
								newTripStops[sequenceNo]["transferprio"] = None

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
		zugartList = self.__ttgcache.lookupFahrtZugart(fplanfahrtid)
		if (zugartList is not None):		
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
		allLs = self.__ttgcache.lookupFahrtLinien(fplanfahrtid)
		if ( allLs is not None):		
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
		bahnhofLookup = self.__ttgcache.lookupBahnhof(lastStopNo)
		if (bahnhofLookup is not None):
			defaultDirectionText = bahnhofLookup[1]
		else:
			defaultDirectionText = lastEntry["stop"][1]

		for tripStop in newTripStops.values():
			tripStop["directionshort"] = defaultDirectionShort
			tripStop["directiontext"] = defaultDirectionText

		# Sobald ein Datensatz FahrtR vorhanden ist muss die "kompliziertere" Variante der Findung des richtigen Stops erfolgen
		allRs = self.__ttgcache.lookupFahrtRichtung(fplanfahrtid)
		if (allRs is not None):
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
		allAs = self.__ttgcache.lookupFahrtAttribut(fplanfahrtid)
		if (allAs is not None):
			for a in allAs:
				# ist die bitfieldno eine gueltige bitfieldno für heute 
				if (a[5] is None or (a[5] in self.__bitfieldnumbers) or a[5] == 0):
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
		allIs = self.__ttgcache.lookupFahrtInfo(fplanfahrtid)
		if (allIs is not None):
			for i in allIs:
				# ist die bitfieldno eine gueltige bitfieldno für heute
				if (i[5] is None or (i[5] in self.__bitfieldnumbers) or i[5] == 0):
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
		allDurchBi = self.__ttgcache.lookupFahrtDuBi(fplanfahrtid)
		if (allDurchBi is not None):
			for d in allDurchBi:
				# ist die bitfieldno eine gueltige bitfieldno für heute
				if (d[1] is None or (d[1] in self.__bitfieldnumbers) or d[1] == 0):
					# Belegen des Halts mit den Informationen der Durchbindung
					stopSequenceNo = self.getStopSequenceNo(d[0])
					if (stopSequenceNo > -1):					
						newTripStops[stopSequenceNo]["tripno_continued"] = d[2]
						newTripStops[stopSequenceNo]["operationalno_continued"] = d[3]
						newTripStops[stopSequenceNo]["stopno_continued"] = d[4]
					#else:
					#logger.info("\tDurchbindung: Halt {} im Lauf für fplanfahrtid {} nicht gefunden".format(d[0], fplanfahrtid))




