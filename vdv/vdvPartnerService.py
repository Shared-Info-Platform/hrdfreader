import datetime
import time
import enum
from threading import Lock
from vdv.vdvlog import logger
from vdv.vdvdb import VdvDB
import vdv.protocol.vdvProtocol as VDV
from vdv.vdvPartnerMapper import VdvPartnerMapper

class PartnerServiceType(enum.Enum):
    AUSREF = 0
    AUS = 1
    DFIREF = 2
    DFI = 3
    ANSREF = 4
    ANS = 5

class PartnerServiceAboState(enum.Enum):
    IDLE = 0
    REFRESH_DATA = 1
    SENDING_DATA = 2
    DELETED = 3
    UPDATED = 4
    

class VdvPartnerService():
    """ Die Klasse beschreibt einen einzelnen VDV-Partnerservice """

    def __init__(self, partnerConfigName, vdvConfig):
        self.__partnerConfigName = partnerConfigName
        self.__vdvConfig = vdvConfig
        self.__serviceUrl = self.__vdvConfig[partnerConfigName]['serviceUrl']
        self.__senderName = self.__vdvConfig[partnerConfigName]['senderName']
        self.__serviceName = self.__vdvConfig[partnerConfigName]['serviceName']
        self.__serviceType = PartnerServiceType[self.__vdvConfig[partnerConfigName]['serviceType']]
        self.__refreshAboIntervalMin = int(self.__vdvConfig[partnerConfigName]['refreshAboIntervalMin'])
        self.__refreshMappingDataIntervalMin = int(self.__vdvConfig[partnerConfigName]['refreshAboIntervalMin'])
        self.__nextMappingDataRefresh = datetime.datetime.now()
        self.__startTime = datetime.datetime.utcnow()
        self.__datenVersionID = None
        self.__XSDVersionID = self.__vdvConfig[partnerConfigName]['XSDVersionID']
        self.__maxTripsPerAbo = int(self.__vdvConfig[partnerConfigName]['maxTripsPerAbo'])
        self.__extendHaltID7To9 = VDV.vdvStrToBool(self.__vdvConfig[partnerConfigName]['extendHaltID7To9'])
        # dictionary of serviceAbos
        self.__aboLock = Lock()
        self.__serviceAbos = dict()
        # Aufbau der Datenbankverbindung
        dbname = self.__vdvConfig['DATABASE']['dbname']
        host = self.__vdvConfig['DATABASE']['host']
        port = self.__vdvConfig['DATABASE']['port']
        user = self.__vdvConfig['DATABASE']['user']
        pwd = self.__vdvConfig['DATABASE']['pwd']
        self.__vdvDB = VdvDB(dbname, host, port, user, pwd)
        if self.__vdvDB.connect() == False: logger.error("{} => Fehler beim Verbinden mit der Datenbank: ".format(self.ServiceName))
        self.__vdvMapper = VdvPartnerMapper(self.vdvDB)
        self.refreshMappingData()
        logger.info("{} => {}-PartnerService mit URL {} angelegt ".format(self.ServiceName, self.ServiceType.name, self.ServiceURL))

    @property
    def vdvDB(self): return self.__vdvDB
    @property
    def VdvMapper(self): return self.__vdvMapper         
    @property
    def StartTime(self): return self.__startTime
    @property
    def SenderName(self): return self.__senderName
    @property
    def ServiceName(self): return self.__serviceName
    @property
    def ServiceType(self): return self.__serviceType
    @property
    def ServiceURL(self): return self.__serviceUrl
    @property
    def RefreshAboIntervalMin(self): return self.__refreshAboIntervalMin
    @property
    def RefreshMappingDataIntervalMin(self): return self.__refreshMappingDataIntervalMin
    @property
    def NextMappingDataRefresh(self): return self.__nextMappingDataRefresh
    @property
    def DatenVersionID(self): return self.__datenVersionID
    @property
    def XSDVersionID(self): return self.__XSDVersionID
    @property
    def MaxTripsPerAbo(self): return self.__maxTripsPerAbo
    @property
    def ExtendHaltID7To9(self): return self.__extendHaltID7To9
    @property
    def ServiceAbos(self): return self.__serviceAbos
    @property
    def AboLock(self): return self.__aboLock

    @StartTime.setter
    def StartTime(self, v):
        self.__startTime = v

    def deleteAllAbos(self):
        """ Loeschen aller Abos dieses PartnerService """
        for serviceAbo in self.ServiceAbos:
            serviceAbo.State = PartnerServiceAboState.DELETED
            logger.info("{} => Abo {} zum Löschen vorgemerkt".format(self.ServiceName, serviceAbo.AboID))

    def deleteAbo(self, aboID):
        """ Loeschen des Abos mit der entsprechenden AboID """
        if aboID in self.ServiceAbos:
            self.ServiceAbos[aboID].State = PartnerServiceAboState.DELETED
            logger.info("{} => Abo {} zum Löschen vorgemerkt".format(self.ServiceName, aboID))

    def checkPartnerServiceAbos(self):
        """ Prüft die Service-Abos, ob Daten zur Abholung bereitstehen bzw. ob sich Änderungen ergeben haben """
        # Es muss hier geprüft werden, welche Abos zum Löschen anstehen
        deletableAbos = list()
        for serviceAbo in self.ServiceAbos.values():
            if (serviceAbo.State == PartnerServiceAboState.DELETED): deletableAbos.append(serviceAbo.AboID)

        # AboLock ebenfalls in createDatenAbrufenAntwort
        self.AboLock.acquire()
        for aboID in deletableAbos:
            serviceAbo = self.ServiceAbos.pop(aboID)
            serviceAbo.DirtyData.clear()
            serviceAbo.clearVDVLinienfahrplaene()
            del serviceAbo
            logger.info("{} => Abo {} wurde gelöscht".format(self.ServiceName, aboID))
        self.AboLock.release()

        # Aktualisierung der Abos
        self.refreshAbos()

    def isDataReady(self):
        """ Prüft ob Daten zum Versand anstehen """
        dataIsReady = False
        if (len(self.ServiceAbos) > 0):
            for serviceAbo in self.ServiceAbos.values():
                if (serviceAbo.State == PartnerServiceAboState.IDLE and len(serviceAbo.DirtyData) > 0):
                    dataIsReady = True
                    break;
        return dataIsReady

    def refreshMappingData(self):
        """ Aktualisiert die Mapping-Daten in bestimmten Min-Intervallen """
        if self.__nextMappingDataRefresh <= datetime.datetime.now():
            logger.info("{} => Aktualisieren der Mapping-Daten".format(self.ServiceName))
            self.__vdvMapper.refreshMappingData()
            self.__nextMappingDataRefresh = datetime.datetime.now() + datetime.timedelta(minutes=self.RefreshMappingDataIntervalMin)

    def currentEckdatenId(self):
        """ Liefert die aktuell gültige EckdatenId """
        eckdatenId = -1
        sql_stmt = "SELECT id FROM HRDF.HRDF_ECKDATEN_TAB "\
                   " WHERE importstatus = 'ok' AND (deleteflag IS NULL OR deleteflag = false) AND (inactive IS NULL OR inactive = false) "\
                   " ORDER BY creationdatetime desc limit 1 "
        curEckdateId = self.vdvDB.connection.cursor()
        curEckdateId.execute(sql_stmt)
        eckdatenIds = curEckdateId.fetchall()
        curEckdateId.close()
        if len(eckdatenIds) > 0: eckdatenId = eckdatenIds[0][0]
        return eckdatenId


class VdvPartnerServiceAbo():
    """ Die Klasse beschreibt ein einzelnes VDV-PartnerserviceAbo """

    def __init__(self, aboID, verfallZst):
        self.__aboID = aboID
        self.__verfallZst = verfallZst        
        self.__nextAboRefresh = datetime.datetime.now()
        self.__dirtyData = list()
        self.__state = PartnerServiceAboState.IDLE
        self.__stateLock = Lock()

    @property
    def AboID(self): return self.__aboID
    @property
    def VerfallZst(self): return self.__verfallZst
    @property
    def NextAboRefresh(self): return self.__nextAboRefresh
    @property
    def DirtyData(self): return self.__dirtyData
    @property
    def State(self): return self.__state

    @VerfallZst.setter
    def VerfallZst(self, v): self.__verfallZst = v

    @NextAboRefresh.setter
    def NextAboRefresh(self, v): self.__nextAboRefresh = v
    @State.setter
    def State(self, v):
        self.__stateLock.acquire()
        self.__state = v
        self.__stateLock.release()

    def isEqual(self, other):
        """ Vergleich von 2 VDVPartnerServiceAbos """
        return ( isinstance(other, VdvPartnerServiceAbo) and self.AboID == other.AboID and self.VerfallZst == other.VerfallZst)
