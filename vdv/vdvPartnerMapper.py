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
        self.__operationalnoLookUp = dict()
        self.__linienLookUp = dict()
        self.__linenoLookUp = dict()
        self.__produktTextLookUp = dict()
        self.__produktIDLookUp = dict()
        # Verkehrsmittelkategorien Zusammenfassung nach KategorieNr (HRDF_ZugartKategorie_tab)
        self.__catZug = tuple(('EC','EN','IC','IR','IRE','RE','R','S','SN','PE','ATZ','EXT','ICE','TGV','RJ','RJX','TE2','TER','RB','IRE','MAT','NJ'))
        self.__catTram = tuple(('T','TN'))
        self.__catMetro = tuple(('M',))
        self.__catZahnradbahn = tuple(('CC',))
        self.__catBus = tuple(('B','BN','BP','CAR','CAX','EXB','RUB','KB','TX'))
        self.__catStandSeilbahn = tuple(('FUN',))
        self.__catKabinenbahn = tuple(('PB','GB'))
        self.__catSesselbahn = tuple(('SL',))
        self.__catAufzug = tuple(('ASC',))
        self.__catSchiff = tuple(('BAT','FAE'))
        # Verkehrsmittelkategorien für spezielles Verhalten
        self.__catForSpecialLinienText = self.__catZug + self.__catSchiff

    def refreshMappingData(self):
        """ Funktion lädt/aktualisiert die notwendigen Mappingdaten """        
        # ProduktText und ProduktID-Mapping
        self.__produktTextLookUp.clear()
        self.__produktIDLookUp.clear()
        sql_produktLookUp = "SELECT distinct a.fk_eckdatenid, b.categorycode, a.languagecode, a.categorytext "\
                            "  FROM hrdf.hrdf_zugartkategorie_tab a, hrdf.hrdf_zugart_tab b "\
                            " WHERE a.fk_eckdatenid = b.fk_eckdatenid "\
                            "   AND a.categoryno = b.categoryno "\
                            " ORDER BY a.fk_eckdatenid, b.categorycode, a.languagecode"
        curProdukt = self.__vdvDB.connection.cursor()
        curProdukt.execute(sql_produktLookUp)
        produkte = curProdukt.fetchall()
        logger.debug("Lookup von {} Produkten wird aufgebaut".format(len(produkte)))
        curProdukt.close()
        for produkt in produkte:            
            produktHash = hash((produkt[0], produkt[1], produkt[2]))
            self.__produktTextLookUp[produktHash] = produkt[3]
            if (produkt[1] in self.__catZug): self.__produktIDLookUp[produktHash] = 'Zug'
            elif (produkt[1] in self.__catTram): self.__produktIDLookUp[produktHash] = 'Tram'
            elif (produkt[1] in self.__catMetro): self.__produktIDLookUp[produktHash] = 'Metro'
            elif (produkt[1] in self.__catZahnradbahn): self.__produktIDLookUp[produktHash] = 'Zahnradbahn'
            elif (produkt[1] in self.__catBus): self.__produktIDLookUp[produktHash] = 'Bus'
            elif (produkt[1] in self.__catStandSeilbahn): self.__produktIDLookUp[produktHash] = 'Standseilbahn'
            elif (produkt[1] in self.__catKabinenbahn): self.__produktIDLookUp[produktHash] = 'Kabinenbahn'
            elif (produkt[1] in self.__catSesselbahn): self.__produktIDLookUp[produktHash] = 'Sesselbahn'
            elif (produkt[1] in self.__catAufzug): self.__produktIDLookUp[produktHash] = 'Aufzug'
            elif (produkt[1] in self.__catSchiff): self.__produktIDLookUp[produktHash] = 'Schiff'
            else: self.__produktIDLookUp[produktHash] = 'Unbekannt'
        produkte.clear()

        # Betreiber-Mapping
        self.__betreiberLookUp.clear()
        self.__operationalnoLookUp.clear()
        sql_betreiberLookUp = "SELECT operationalno, uiclaendercode, gonr, goabk FROM hrdf.hrdf_vdvbetreibermapping_tab ORDER BY operationalno"
        curBetreiber = self.__vdvDB.connection.cursor()
        curBetreiber.execute(sql_betreiberLookUp)
        betreiber = curBetreiber.fetchall()
        logger.debug("Lookup von {} Betreibern wird aufgebaut".format(len(betreiber)))
        curBetreiber.close()
        for b in betreiber:
            betreiberID = b[1]+":"+b[2]
            self.__betreiberLookUp[b[0]] = betreiberID
            self.__operationalnoLookUp[betreiberID] = b[0]
        betreiber.clear()

        # Linien-Mapping
        self.__linienLookUp.clear()
        sql_linienLookUp = "SELECT operationalno, lineno, linienid, linientext FROM hrdf.hrdf_vdvlinienmapping_tab ORDER BY operationalno, lineno"
        curLinien = self.__vdvDB.connection.cursor()
        curLinien.execute(sql_linienLookUp)
        linien = curLinien.fetchall()
        logger.debug("Lookup von {} Linien wird aufgebaut".format(len(linien)))
        curLinien.close()
        for linie in linien:
            linienHash = hash((linie[0], linie[1]))
            betreiberID = self.__betreiberLookUp[linie[0]]
            linienID = betreiberID+":"+linie[2]
            self.__linienLookUp[linienHash] = (linie[2], linie[3])
            self.__linenoLookUp[linienID] = (linie[0], linie[1])
        linien.clear()

    def mapBetreiberID(self, operationalno):
        """ Mapped die HRDF-operationalno in eine VDV-BetreiberID """
        if operationalno in self.__betreiberLookUp:
            betreiberID = self.__betreiberLookUp[operationalno]
        else:
            try:
                betreiberID = "85:"+str(int(operationalno))
            except:
                betreiberID = "85:"+operationalno
        return betreiberID

    def mapOperationalno(self, betreiberID):
        """ Mapped die VDV-BetreiberID zur HRDF-operationalno """
        # Die VDV-BetreiberID (RV-Vorgabe ist <UIC-Ländercode>:<Go-Nummer>
        if betreiberID in self.__operationalnoLookUp: return self.__operationalnoLookUp[betreiberID]
        return betreiberID

    def mapOperationalLineno(self, linienID):
        """ Mapped die VDV-LinienID (mit BetreiberID) zur HRDF-lineno und HRDF-operationalno"""
        # DIe VDV-LinienID (RV-Vorgabe ist <UIC-Ländercode>:<Go-Nummer>:<Technischer Linienschlüssel>
        operationalLineno = tuple(("-1","-1"))
        if linienID in self.__linenoLookUp: operationalLineno = self.__linenoLookUp[linienID]
        return operationalLineno
                
    def mapLinieID(self, operationalno, lineno):
        """ Mapped die HRDF-Linienno in eine VDV-LinienID """
        betreiberID = self.mapBetreiberID(operationalno)
        linienID = lineno
        linienHash = hash((operationalno, lineno))
        if linienHash in self.__linienLookUp: linienID = self.__linienLookUp[linienHash][0]
        return betreiberID+":"+linienID

    def mapLinieText(self, operationalno, lineno, firstCategorycode, firstLineNo):
        """ Mapped die HRDF-Linienno in einen VDV-LinienText
            Spezialität für Verkehrsmittelkategorie Zug/Schiff (siehe __init__())
        """
        if firstCategorycode in self.__catForSpecialLinienText:
            if firstLineNo is None: linienText = firstCategorycode
            else: linienText = firstCategorycode+firstLineNo
        else:
            linienText = lineno
            linienHash = hash((operationalno, lineno))
            if linienHash in self.__linienLookUp: linienText = self.__linienLookUp[linienHash][1]
        return linienText

    def mapProduktID(self, categorycode, languagecode, eckdatenid):
        """ Mapped den HRDF-Zugart-Kategoriecode in eine VDV-ProduktID """
        produktID = str(categorycode)
        produktHash = hash((eckdatenid, categorycode, languagecode))
        if produktHash in self.__produktIDLookUp: produktID = self.__produktIDLookUp[produktHash]
        # ProduktID muss einer Verkehrsmittelkategorie entsprechen siehe Doku (Harmonisierung...)
        # daher wir hier nicht auf self.__produktTextLookUp zugegriffen
        return produktID

    def mapHaltID(self, stoppointident, extendHaltID7To9):
        """ Mapped den HRDF-StoppointIdent in die VDV-HaltID """
        # HRDF übliche 7-stellige Format durch Anhängen von "00" in das im 454 (NAV) übliche 9-stellige Format (konfigurierbar)
        if (extendHaltID7To9 and len(stoppointident) == 7): return stoppointident+"00"
        return stoppointident