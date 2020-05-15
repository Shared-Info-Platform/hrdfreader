import psycopg2
from datetime import datetime, date, timedelta, time
from io import StringIO
from hrdf.hrdflog import logger
from hrdf.hrdfdb import HrdfDB
from hrdf.hrdfTTGCache import HrdfTTGCache
from hrdf.hrdfTTGWorker import HrdfTTGWorker
import time
from threading import Thread, _start_new_thread, _allocate_lock
from queue import Queue

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
		self.__TTGCache = HrdfTTGCache(db)
		self.__workQueue = Queue()
		self.__commQueue = Queue()
		self.__responseQueue = Queue()
		self.__responseData = dict()

		self.__numOfCurrentDBThreads = 0
		self.__DBThreadStarted = False
		self.__lock = _allocate_lock()

		self.__numberOfWorker = 5
		self.__chunkSize = 5000

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
		iErrorCnt = 0
		logger.info("Anzahl der Worker: {}".format(self.__numberOfWorker))
		logger.info("Arbeitspaketgröße: {}".format(self.__chunkSize))

		# Aufbau/Erzeugen des TTG-Cache mit den Lookup-Tabellen
		self.__TTGCache.createCacheData(self.__eckdatenid, self.__generateFrom, self.__generateTo);

		sql_selDayTrips = "SELECT b.id, b.tripno, b.operationalno, b.tripversion, array_agg(a.bitfieldno) as bitfieldnos, b.cyclecount, b.cycletimemin "\
						  "FROM HRDF_FPlanFahrtVE_TAB a, "\
						  "     HRDF_FPLanFahrt_TAB b "\
						  "WHERE (a.bitfieldno in (SELECT bitfieldno FROM HRDF_Bitfeld_TAB where bitfieldarray @> ARRAY[%s::date] AND fk_eckdatenid = %s) "\
						  "       OR a.bitfieldno is NULL OR a.bitfieldno = 0) "\
						  "  and a.fk_fplanfahrtid = b.id "\
						  "  and b.fk_eckdatenid = a.fk_eckdatenid "\
						  "  and a.fk_eckdatenid = %s "\
						  "GROUP BY b.id, b.tripno, b.operationalno, b.tripversion"

		# Worker anlegen und starten
		workerPool = []
		for x in range(self.__numberOfWorker):
			worker = HrdfTTGWorker(self.__hrdfdb, x, "worker-"+str(x), self.__workQueue, self.__commQueue, self.__responseQueue, self.__TTGCache)
			workerPool.append(worker)

		dayCnt = (self.__generateTo - self.__generateFrom).days
		i = 0
		while (i<=dayCnt):
			generationDay = self.__generateFrom + timedelta(days=i)
			logger.info("{:%d.%m.%Y} => Start der Generierung".format(generationDay))

			# Laden der Tagesfahrten und Generierung jeder Fahrt
			# mit einer Schleife über den selDayTrip-Cursor, der in self.__chunkSize - Blöcken abgearbeitet wird
			curDayTrip = self.__hrdfdb.connection.cursor("cursor_selDayTrip")
			curDayTrip.execute(sql_selDayTrips, (str(generationDay), self.__eckdatenid, self.__eckdatenid))
			currentRowCnt = 0
			paketCnt = 0
			while True:				
				trips = curDayTrip.fetchmany(self.__chunkSize)
				if not trips: break
				paketCnt+=1				
				# Schiebe die zu generierenden Trips in die Workqueue, damit sie dort von den Workern abgeholt werden können
				dataItem = dict(eckdatenid=self.__eckdatenid, day=generationDay, trips=trips)
				self.__workQueue.put(dataItem)
				currentRowCnt += len(trips)

			# Aufbau einer tagesbezogenen Response-Datenstruktur zur Verarbeitung der Ergebnisse der Worker
			logger.info("{:%d.%m.%Y} => {} Fahrten wurden in {} Arbeitspakete aufgeteilt".format(generationDay, currentRowCnt, paketCnt))
			self.__responseData[generationDay] = dict(paketCnt=paketCnt, complete=False, dataItems=set())

			curDayTrip.close()

			# Nachdem der erste Tag aufgeteilt ist, können die Worker gestartet werden
			if (i==0):
				for worker in workerPool:
					worker.start()

			# Tageszähler hochzählen und nächsten gewünschten Tag generieren
			i += 1

		# Auf Responsedaten warten und dann verarbeiten
		moreResponseData = True
		while moreResponseData:
			responseData = self.__responseQueue.get()
			self.__responseData[responseData["day"]]["dataItems"].add(responseData["data"])

			allComplete = True
			for day, resData in self.__responseData.items():
				if (resData["paketCnt"] == len(resData["dataItems"])):
					if (resData["complete"] == False):
						logger.info("{:%d.%m.%Y} => Tagesfahrplan wird gesichert".format(day))
						_start_new_thread(self.saveNewDailyTimetable, (self.__eckdatenid, day, resData["dataItems"],))
						#self.saveNewDailyTimetable(self.__eckdatenid, day, resData["dataItems"])
						resData["complete"] = True				
				else:
					allComplete = False
					break;

			if (allComplete): moreResponseData = False

		# Mindestens ein DB-Thread sollte gestartet worden sein
		while not self.__DBThreadStarted: time.sleep(5)
		# Alle DB-Threads müssen sich beendet haben
		while self.__numOfCurrentDBThreads > 0: time.sleep(5)

		# Warten bis alle dataItem abgearbeitet sind
		self.__workQueue.join()
		# Kontrolliertes schließen der Threads
		self.__commQueue.put(True)

		# Warten auf Beenden der Worker
		for worker in workerPool:
			worker.join()

		return iErrorCnt

	def saveNewDailyTimetable(self, eckdatenid, generationDay, ttChunkSet):
		"""
		Die Funktion speichert die übergebenen TimeTable-Chunks in der Datenbank.
		Um konsistent zu bleiben wird der bestehende Tagesfahrplan zuerst gelöscht
		Die Funktion wird als Thread aufgerufen

		eckdatenid - id der Fahrplandaten
		generationDay - Generierungsdatum
		ttChunkSet - Set mit mehreren Chunks (csv-Stings) des Tagesfahrplans
		"""	
		self.__lock.acquire()
		self.__numOfCurrentDBThreads += 1
		self.__DBThreadStarted = True
		self.__lock.release()

		# Lokale DB-Verbindung erstellen
		hrdfDBSingle = HrdfDB(self.__hrdfdb.dbname, self.__hrdfdb.host, self.__hrdfdb.user, self.__hrdfdb.password)

		# Löschen von bestehenden Tagesdaten"
		if (hrdfDBSingle.connect()):
			curDeleteDay = hrdfDBSingle.connection.cursor()
			sql_delDay = "DELETE FROM HRDF_DailyTimeTable_TAB WHERE fk_eckdatenid = %s AND operatingday = %s"
			curDeleteDay.execute(sql_delDay, (eckdatenid, str(generationDay)))
			deletedRows = curDeleteDay.rowcount
			logger.info("{:%d.%m.%Y} => {} bestehende Einträge wurden geloescht".format(generationDay, deletedRows))
			curDeleteDay.close()

			if (len(ttChunkSet)>0):
				curSaveTrip = hrdfDBSingle.connection.cursor()
				strCopy = "COPY HRDF_DailyTimeTable_TAB (fk_eckdatenid,tripident,tripno,operationalno,tripversion,"\
							"operatingday,stopsequenceno,stopident,stopname,stoppointident,stoppointname,arrstoppointtext,depstoppointtext,arrdatetime,depdatetime,noentry,noexit,"\
							"categorycode,classno,categoryno,lineno,directionshort,directiontext,"\
							"attributecode,attributetext_de,attributetext_fr,attributetext_en,attributetext_it,"\
							"infotextcode,infotext_de,infotext_fr,infotext_en,infotext_it,"\
							"longitude_geo,latitude_geo,altitude_geo,transfertime1,transfertime2,transferprio,tripno_continued,operationalno_continued,stopno_continued)"\
							" FROM STDIN USING DELIMITERS ';' NULL AS ''"
				for chunk in ttChunkSet:
					dailytimetable_strIO = StringIO()
					dailytimetable_strIO.write(chunk)
					dailytimetable_strIO.seek(0)
					curSaveTrip.copy_expert(strCopy, dailytimetable_strIO)
					dailytimetable_strIO.close()

				curSaveTrip.close()
				hrdfDBSingle.connection.commit()
				logger.info("{:%d.%m.%Y} => Neuer Tagesfahrplan wurde gesichert".format(generationDay, deletedRows))
		else:
			logger.error("{:%d.%m.%Y} => DB-Thread konnte keine Verbindung zur Datenbank aufbauen".format(generationDay))

		# DB-Thread-Zähler wieder zurücksetzen
		self.__lock.acquire()
		self.__numOfCurrentDBThreads -= 1
		self.__lock.release()
