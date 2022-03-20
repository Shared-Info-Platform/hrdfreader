import psycopg2
import time
from datetime import datetime, date, timedelta, time
from io import StringIO
from vdv.vdvlog import logger
from vdv.vdvdb import VdvDB
from vdv.vdvServer import VdvServer

import time
from threading import Thread, _start_new_thread, _allocate_lock
from queue import Queue


class VdvService():
	"""
	Die Klasse stellt den generellen VDVService zur Verfügung
	Auf Grund der Konfiguration startet der VDVService einen oder mehrere AUSREF-ServiceHandler
	Jeder ServiceHandler verwaltet seine eigenen Abos
	"""
	modulVersion = "2.1.1"
	vdvVersions = ["VDV454-2.6:2017d"]
	vdvFormats = ["AUSREF"]

	def __init__(self, vdvConfig):
		self.__vdvConfig = vdvConfig
		self.__vdvServers = dict()
		self.__workerIntervalSec = int(vdvConfig["VDVService"]["workerIntervalSec"])
		# self.__vdvdb wird in initialise initialisiert

	def initialise(self):
		""" Initialisierung-Task für den VDVService """
		initOk = True
		# Datenbankverbindungen sind vornehmlich in den PartnerServices aktiv

		# Aufbauen der VDVServer und deren (Partner)VDVServiceHandler
		for x in range(int(self.__vdvConfig['VDVService']['vdvServerCnt'])):
			serverNo = x+1
			serverConfigName = "VDVServer_"+str(serverNo)
			self.__vdvServers[serverConfigName] = VdvServer(serverConfigName, self.__vdvConfig)

		return initOk

	def run(self):
		""" Startet den VDVService """
		logger.info("VDVService is running")
		runService = True
		while runService:
			try:

				time.sleep(self.__workerIntervalSec)				
				# In allen vdvServern schauen was zu tun ist
				for vdvServer in self.__vdvServers.values():
					vdvServer.checkPartnerServices()

			except KeyboardInterrupt:
				self.__vdvHTTPServer.shutdown()
				runService = False
		logger.info("Service wurde beendet")