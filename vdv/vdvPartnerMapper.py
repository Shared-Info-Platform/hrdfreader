import datetime
import time
import enum
from vdv.vdvlog import logger
from vdv.vdvdb import VdvDB


class VdvPartnerMapper(object):
    """ Die Klasse stellt VDV-Mapping Funktionalität zur Verfügung """
    def __init__(self, vdvDB):
        self.__vdvDB = vdvDB
        self.__betreiberLookUp = dict()
        self.__linienLookUp = dict()
        self.__produktLookUp = dict()

    def loadMappingData(self):
        """ Funktion lädt die notwendigen Mappingdaten """        
        self.__produktLookUp.clear()
        sql_produktLookUp = "SELECT distinct fk_eckdatenid, categoryno, languagecode, categorytext FROM hrdf.hrdf_zugartkategorie_tab ORDER BY languagecode, categoryno"
        curProdukt = self.__vdvDB.connection.cursor()
        curProdukt.execute(sql_produktLookUp)
        produkte = curProdukt.fetchall()
        logger.debug("Lookup von {} Produkten wird aufgebaut".format(len(produkte)))
        curProdukt.close()
        for produkt in produkte:
            produktHash = hash((produkt[0], produkt[1], produkt[2]))
            self.__produktLookUp[produktHash] = produkt[3]
        produkte.clear()

    def mapBetreiber(self, operationalno):
        """ Mapped die HRDF-operationalno in eine VDV-BetreiberID """
        if operationalno in self.__betreiberLookUp:
            betreiberID = self.__betreiberLookUp[operationalno]
        else:
            try:
                betreiberID = "85:"+str(int(operationalno))
            except:
                betreiberID = "85:"+operationalno
        return betreiberID
        
    def mapLinie(self, operationalno, lineno):
        """ Mapped die HRDF-Linienno in eine VDV-LinienID """
        betreiberID = self.mapBetreiber(operationalno)
        linienID = lineno
        if lineno in self.__linienLookUp:
            linienID = self.__linienLookUp[lineno]
        return betreiberID+":"+linienID

    def mapProdukt(self, categoryno, languagecode, eckdatenid):
        """ Mapped die HRDF-Zugart-Kategorienummer in eine VDV-ProduktID """
        produktID = str(categoryno)
        produktHash = hash((eckdatenid, categoryno, languagecode))
        if produktHash in self.__produktLookUp:
            produktID = self.__produktLookUp[produktHash]
        return produktID
