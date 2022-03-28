import datetime
import time
import enum
from vdv.vdvlog import logger
import xml.etree.ElementTree as ET
import vdv.protocol.vdvProtocol as VDV
from vdv.vdvPartnerService import VdvPartnerService, VdvPartnerServiceAbo, PartnerServiceAboState
from vdv.vdvPartnerMapper import VdvPartnerMapper
from vdv.protocol.AboVerwalten import AboAntwort
from vdv.protocol.Bestaetigung import Bestaetigung, BestaetigungMitAboID, Fehlernummer
from vdv.protocol.DatenAbrufen import DatenAbrufenAntwort
from vdv.protocol.AUSNachricht import AUSNachricht, Linienfahrplan, SollFahrt, SollHalt

class VdvPSAUSREF(VdvPartnerService):
    """ Die Klasse beschreibt einen einzelnen VDV-Partnerservice des AUSREF """

    def __init__(self, partnerConfigName, vdvConfig):
        super().__init__(partnerConfigName, vdvConfig)

    def createOrUpdateAbos(self, serviceAboList):
        """
        Erstellen oder Aktualisieren von Abos die dem Dienst entsprechen

            aboAnfrage - xml ElementTree der VDV-Aboanfrage
        """
        if (len(serviceAboList) == 0):
            aboAntwort = AboAntwort(Bestaetigung())
            aboAntwort.XSDVersionID = self.XSDVersionID
            aboAntwort.Bestaetigung.Ergebnis = 'notok'
            aboAntwort.Bestaetigung.Fehlernummer = Fehlernummer.ERR_NOREP
            aboAntwort.Bestaetigung.Fehlertext = 'Die Anfrage enthaelt keine Abos'
        else:
            aboAntwort = AboAntwort(None)
            aboAntwort.XSDVersionID = self.XSDVersionID
            for aboAUSREF in serviceAboList:
                aboID = aboAUSREF.get('AboID')
                bestaetigungMitAboID = BestaetigungMitAboID(aboID)
                if (aboAUSREF.tag == 'AboAUSRef'):
                    # Es handelt sich tatsächlich um ein AUSRef-Abo => Übernahme der Daten in VdvPartnerServiceAbo erstellen
                    abo = VdvPSAboAUSREF(aboID, aboAUSREF.get('VerfallZst'))
                    abo.GueltigVon = VDV.vdvStrToDateTimeUTC(aboAUSREF.find('Zeitfenster').find('GueltigVon').text)
                    abo.GueltigBis = VDV.vdvStrToDateTimeUTC(aboAUSREF.find('Zeitfenster').find('GueltigBis').text)
                    for linie in aboAUSREF.findall('LinienFilter'):
                        if linie.find('RichtungsID') is None:
                            richtungsID = None
                        else:
                            richtungsID = linie.find('RichtungsID').text
                        abo.addLinienFilter(linie.find('LinienID').text, richtungsID, self.VdvMapper)

                    for betreiber in aboAUSREF.findall('BetreiberFilter'):
                        abo.addBetreiberFilter(betreiber.find('BetreiberID').text, self.VdvMapper)

                    # Überprüfen, ob dieses Abo bereits besteht.
                    if aboID not in self.ServiceAbos:
                        self.__createAbo(abo)
                    else:
                        self.__updateAbo(abo)
                    
                    bestaetigungMitAboID.Bestaetigung.Ergebnis = 'ok'
                    bestaetigungMitAboID.Bestaetigung.Fehlernummer = Fehlernummer.OK.value
                else:
                    # Abo passt nicht zum Dienst 
                    bestaetigungMitAboID.Bestaetigung.Ergebnis = 'notok'
                    bestaetigungMitAboID.Bestaetigung.Fehlernummer = Fehlernummer.ERR_NOREP_SERVICE.value
                    bestaetigungMitAboID.Bestaetigung.Fehlertext = 'Abo passt nicht zum VDV-Dienst'

                # Bestätigung an die AboAntwort hängen
                aboAntwort.addBestaetigungMitAboID(bestaetigungMitAboID)
        
        return aboAntwort

    def __createAbo(self, abo):
        """ Anlegen eines neuen Abos """
        self.ServiceAbos[abo.AboID] = abo
        abo.NextAboRefresh = datetime.datetime.now()

    def __updateAbo(self, abo):
        """ Aktualisieren eines bestehenden Abos """
        existingAbo = self.ServiceAbos[abo.AboID]
        if existingAbo.isEqual(abo) == False:
            existingAbo.VerfallZst = abo.VerfallZst
            existingAbo.GueltigVon = abo.GueltigVon
            existingAbo.GueltigBis = abo.GueltigBis
            existingAbo.LinienFilter = abo.LinienFilter
            existingAbo.LinienFilterHRDF = abo.LinienFilterHRDF
            existingAbo.BetreiberFilter = abo.BetreiberFilter
            existingAbo.BetreiberFilterHRDF = abo.BetreiberFilterHRDF
            existingAbo.DirtyData.clear()
            existingAbo.clearVDVLinienfahrplaene()
            abo.NextAboRefresh = datetime.datetime.now()

    def __buildLinienfahrplaeneSQL(self, serviceAbo, eckdatenId):
        """ Erzeugt das SQL-Statment für die Linienfahrpläne des angegebenen ServiceAbos """
        sql_stmt = "SELECT CASE WHEN array_position(infotextcode, 'RN') IS NULL THEN coalesce(lineno, cast(tripno as varchar)) ELSE infotext_de[array_position(infotextcode, 'RN')] END as lineno, "\
                   "       coalesce(directionshort, 'H'), operationalno, count(distinct tripident) "\
			       "  FROM HRDF.HRDF_DailyTimetable_TAB "\
				   " WHERE stopsequenceno = 0 AND depdatetime between %s and %s and fk_eckdatenid = %s"\

        betreiberSQL = serviceAbo.buildBetreiberSQL()
        if ( betreiberSQL is not None): sql_stmt += " AND ("+betreiberSQL+")"

        linienSQL = serviceAbo.buildLinienSQL()
        if ( linienSQL is not None): sql_stmt += " AND ("+linienSQL+")"

        sql_stmt += " GROUP BY lineno, coalesce(directionshort, 'H'), operationalno, (array_position(infotextcode, 'RN') IS NULL), coalesce(lineno, cast(tripno as varchar)), infotext_de[array_position(infotextcode, 'RN')] "\
					" ORDER BY lineno, coalesce(directionshort, 'H'), operationalno "
        curLinienfahrplan = self.vdvDB.connection.cursor()
        curLinienfahrplan.execute(sql_stmt, (VDV.vdvUTCToLocal(serviceAbo.GueltigVon), VDV.vdvUTCToLocal(serviceAbo.GueltigBis), eckdatenId))
        linienFahrplaene = curLinienfahrplan.fetchall()
        curLinienfahrplan.close()
        return linienFahrplaene

    def __buildFahrlplaeneSQL(self, serviceAbo, lineno, directionshort, operationalno, eckdatenId):
        """ Erzeugt das SQL-Statement für die einzelnen Fahrpläne eines Linienfahrplans des angegebenen serviceAbos """
        sql_stmt = "SELECT tripident, operatingday, "\
                   "       stoppointident, stoppointname, arrstoppointtext, depstoppointtext, arrdatetime, depdatetime, noentry, noexit, directiontext, stopname as fromdirectiontext, categorycode, classno, categoryno, "\
                   "       fk_eckdatenid, infotextcode, infotext_de, lineno "\
                   "  FROM HRDF.HRDF_DailyTimetable_TAB "\
                   " WHERE CASE WHEN array_position(infotextcode, 'RN') IS NULL THEN coalesce(lineno, cast(tripno as varchar)) ELSE infotext_de[array_position(infotextcode, 'RN')] END = %s "\
                   "   AND coalesce(directionshort, 'H') = %s and operationalno = %s and depdatetime between %s and %s  and fk_eckdatenid = %s"\
                   " ORDER BY lineno, coalesce(directionshort, 'H'), operationalno, tripident, stopsequenceno"
        curFahrplan = self.vdvDB.connection.cursor()
        curFahrplan.execute(sql_stmt, (lineno, directionshort, operationalno, VDV.vdvUTCToLocal(serviceAbo.GueltigVon), VDV.vdvUTCToLocal(serviceAbo.GueltigBis), eckdatenId))
        fahrplaene = curFahrplan.fetchall()
        curFahrplan.close()
        return fahrplaene

    def refreshAbos(self):
        """ Die Funktion aktualisiert die Daten der Service-Abos """
        if (self.vdvDB.connect()):
            eckdatenId = self.currentEckdatenId()            
            for serviceAbo in self.ServiceAbos.values():
                if (serviceAbo.State == PartnerServiceAboState.IDLE and serviceAbo.NextAboRefresh < datetime.datetime.now()):
                    serviceAbo.State = PartnerServiceAboState.REFRESH_DATA
                    # Gruppierung aller Linienfahrpläne, mit anschließendem Statement über alle beinhalteten Fahrten mit Haltestellen
                    linienFahrplaene = self.__buildLinienfahrplaeneSQL(serviceAbo, eckdatenId)
                    logger.info("{} => Abo {}: Starte Prüfung/Übernahme der {} Linienfahrplaene".format(self.ServiceName, serviceAbo.AboID, len(linienFahrplaene)))
                    # columns => lineno, coalesce(directionshort, 'H'), operationalno, count(distinct tripident)
                    for sqlLinienFahrplan in linienFahrplaene:
                        lineno = sqlLinienFahrplan[0]
                        directionshort = sqlLinienFahrplan[1]
                        operationalno = sqlLinienFahrplan[2]
                        betreiberID = self.VdvMapper.mapBetreiberID(operationalno)
                        linienID = self.VdvMapper.mapLinieID(operationalno, lineno)
                        richtungsID = directionshort 
                        linienfahrplan = Linienfahrplan(linienID, richtungsID)
                        linienfahrplan.BetreiberID = betreiberID                        
                        fahrplaene = self.__buildFahrlplaeneSQL(serviceAbo, lineno, directionshort, operationalno, eckdatenId)
                        tripident = ""
                        operatingday = datetime.datetime.utcnow()
                        # columns => tripident, operatingday, stoppointident, stoppointname, arrstoppointtext, depstoppointtext, arrdatetime, depdatetime, noentry, noexit, directiontext, stopname as fromdirectiontext, categorycode, classno, categoryno,fk_eckdatenid, infotextcode, infotext_de, lineno 
                        for sqlFahrplan in fahrplaene:
                            if (tripident != sqlFahrplan[0] or operatingday != sqlFahrplan[1]):
                                # Neue Fahrt erstellen
                                tripident = sqlFahrplan[0]
                                operatingday = sqlFahrplan[1]
                                fahrtBezeichner = betreiberID+":"+tripident
                                sollFahrt = SollFahrt(fahrtBezeichner, operatingday)
                                sollFahrt.RichtungsText = sqlFahrplan[10]
                                # FromDirectiontext kann nur beim ersten Halt ausgewertet werden!!!
                                sollFahrt.VonRichtungsText = sqlFahrplan[11]
                                firstCategoryCode = sqlFahrplan[12]
                                firstCategoryNo = sqlFahrplan[14]
                                firstLineNo = sqlFahrplan[18] # nicht gewandelte linieno der Fahrt (kann auch NULL sein) für korrekten LinienText
                                linienfahrplan.VerkehrsmittelText = str(firstCategoryCode)
                                linienfahrplan.ProduktID = self.VdvMapper.mapProduktID(firstCategoryNo, 'de', sqlFahrplan[15])
                                linienfahrplan.LinienText = self.VdvMapper.mapLinieText(operationalno, lineno, firstCategoryNo, firstCategoryCode, firstLineNo)
                                linienfahrplan.addSollFahrt(sollFahrt)
                            # Halte erstellen
                            sollHalt = SollHalt(sqlFahrplan[2])
                            sollHalt.HaltestellenName = sqlFahrplan[3]
                            sollHalt.AnkunftssteigText = sqlFahrplan[4]
                            sollHalt.AbfahrtssteigText = sqlFahrplan[5]
                            sollHalt.Ankunftszeit = sqlFahrplan[6]
                            sollHalt.Abfahrtszeit = sqlFahrplan[7]
                            sollHalt.Einsteigeverbot = sqlFahrplan[8]
                            sollHalt.Aussteigeverbot = sqlFahrplan[9]
                            if (sqlFahrplan[10] != sollFahrt.RichtungsText): sollHalt.RichtungsText = sqlFahrplan[10]
                            if (sqlFahrplan[12] != firstCategoryCode): sollFahrt.VerkehrsmittelText = str(sqlFahrplan[12])
                            if (sqlFahrplan[14] != firstCategoryNo): sollFahrt.ProduktID = self.VdvMapper.mapProduktID(firstCategoryNo, 'de', sqlFahrplan[15])
                            sollFahrt.addSollHalt(sollHalt)

                        # Vor dem Einfügen des Linienfahrplans ins Abo muss geprüft werden ob dieser evtl. schon existiert und ob diese identisch sind
                        # Aufnehmen des Linienfahrplans in die DirtyListe
                        if serviceAbo.existsVDVLinienfahrplan(linienfahrplan):
                            # Prüfe auf Gleichheit
                            if linienfahrplan.isEqual(serviceAbo.vdvLinienfahrplan(hash(linienfahrplan))):
                                pass
                            else:
                                serviceAbo.DirtyData.append(hash(linienfahrplan))
                                serviceAbo.addVDVLinienfahrplan(linienfahrplan)
                        else:
                            serviceAbo.DirtyData.append(hash(linienfahrplan))
                            serviceAbo.addVDVLinienfahrplan(linienfahrplan)

                    # Refresh des Abos abgeschlossen
                    serviceAbo.NextAboRefresh = datetime.datetime.now() + datetime.timedelta(minutes=self.RefreshAboIntervalMin)
                    logger.info("{} => Abo {}: Prüfung/Übernahme der Linienfahrplaene abgeschlossen. Naechste Prüfung => {}".format(self.ServiceName, serviceAbo.AboID, serviceAbo.NextAboRefresh))
                    serviceAbo.State = PartnerServiceAboState.IDLE

    def createDatenAbrufenAntwort(self, datensatzAlle):
        """ Erzeugt eine DatenAbrufenAntwort dienstspezifisch """
        datenAbrufenAntwort = DatenAbrufenAntwort(Bestaetigung())
        try:
            if (len(self.ServiceAbos) > 0):
                for serviceAbo in self.ServiceAbos.values():
                    # Sind Linienfahrpläne zu übertragen => Status des Abos ist IDLE und es sind geänderte/neue Daten vorhanden
                    if serviceAbo.State == PartnerServiceAboState.IDLE:
                        if datensatzAlle:
                            # Es werden alle Linienfahrpläne abgefragt => alle als DirtyData markieren
                            serviceAbo.DirtyData.clear()
                            for linienfahrplan in serviceAbo.VDVLinienfahrplaene: serviceAbo.addDirtyData(hash(linienfahrplan))

                        if len(serviceAbo.DirtyData) > 0:
                            # Linienfahrpläne werden in der AUSNachricht verpackt und versendet
                            # Es werden maximal "maxTripsPerAbo" Fahrten verschickt. Wird TripsCnt während des Linienfahrplans überschritten, wird dieser aber vollständig übertragen
                            # => Es können mehr als "maxTripsPerAbo" in einer DatenAbrufenAntwort auftreten.
                            tripsPerAbo = 0
                            serviceAbo.State = PartnerServiceAboState.SENDING_DATA
                            ausNachricht = AUSNachricht(serviceAbo.AboID)
                            linienFahrplanToRemove = list()
                            for linienfahrplanHash in serviceAbo.DirtyData:
                                linienFahrplan = serviceAbo.vdvLinienfahrplan(linienfahrplanHash)
                                if linienFahrplan is not None:
                                    tripsPerAbo += len(linienFahrplan.SollFahrt)
                                    ausNachricht.addLinienFahrplan(linienFahrplan)
                                else:
                                    logger.info("{} => Abo {}: LinienfahrplanHash {} konnte nicht gefunden werden".format(self.ServiceName, serviceAbo.AboID, linienfahrplanHash))
                                # Merken der LinienFahrpläne die aus der Dirty-Liste gelöscht werden können (In der Schleife löschen führt zu unvorhersehbaren Verhalten)
                                linienFahrplanToRemove.append(linienfahrplanHash)                                
                                if tripsPerAbo > self.MaxTripsPerAbo: break

                            #Bereinigen der DirtyData Liste
                            for linienfahrplanHash in linienFahrplanToRemove: serviceAbo.DirtyData.remove(linienfahrplanHash)

                            datenAbrufenAntwort.addAUSNachricht(ausNachricht)
                            # Es braucht nur ein Abo, dass noch Daten zum Senden übrig hat, um WeiterDaten zu setzten
                            if (len(serviceAbo.DirtyData) > 0): datenAbrufenAntwort.WeitereDaten = True
                            serviceAbo.State = PartnerServiceAboState.IDLE

                    elif (serviceAbo.State == PartnerServiceAboState.REFRESH_DATA):
                        # Sicherstellen, dass auch die Daten in einem nächsten Schritt noch abgefragt werden, die gerade aufbereitet werden (Wir haben keine DatenBereitAnfrage)
                        # So muss nicht auf eine StatusAnfrage gewartet werden
                        logger.info("{} => Abo {}: Daten werden momentan aufbereitet".format(self.ServiceName, serviceAbo.AboID))
                        datenAbrufenAntwort.WeitereDaten = True

                    elif (serviceAbo.State == PartnerServiceAboState.SENDING_DATA):
                        # Es kommt bereits die nächste DatenAbrufenAnfrage rein während wir senden => warum auch immer
                        # Wir schicken hier ein False, um eine weitere überholende DatenAbrufenAnfrage zu verhindern
                        logger.info("{} => Abo {}: Zuvor abgefragte Daten stehen kurz vor dem Senden".format(self.ServiceName, serviceAbo.AboID))
                        datenAbrufenAntwort.WeitereDaten = False

        except Exception as e:
            datenAbrufenAntwort.Bestaetigung.Ergebnis = 'notok'
            datenAbrufenAntwort.Bestaetigung.Fehlernummer = Fehlernummer.ERR_NOREP_INTERNAL.value
            datenAbrufenAntwort.Bestaetigung.Fehlertext = 'Interner Fehler beim Zusammenstellen der DatenAbrufenAntwort aufgetreten'
            logger.info("{} => Abo {}: Intern Fehler beim Zusammenstellen der DatenAbrufenAntwort aufgetreten: {}".format(self.ServiceName, serviceAbo.AboID, e))

        return datenAbrufenAntwort

class VdvPSAboAUSREF(VdvPartnerServiceAbo):
    """ Die Klasse beschreibt ein einzelnes VdV-Partnerservice-Abo des AUSREF """

    def __init__(self, aboID, verfallZst):
        super().__init__(aboID, verfallZst)
        # Filterkriterien
        self.__gueltigVon = None
        self.__gueltigBis = None
        # optionale Filterkriterien
        self.__linienFilter = list()
        self.__linienFilterHRDF = list()
        self.__betreiberFilter = list()
        self.__betreiberFilterHRDF = list()
        self.__produktFilter = list()
        self.__verkehrsmittelTextFilter = list()
        self.__haltFilter = list()
        self.__umlaufFilter = list()
        self.__umlaufID = list()
        self.__fahrplanVersionID = None
        self.__datenVorhandenBis = None
        self.__mitGesAnschluss = None
        self.__mitBereitsAktivenFahrten = None
        self.__mitFormation = None
        # Verwaltungsstrukturen
        self.__vdvLinienFahrplaene = dict()

    @property
    def GueltigVon(self): return self.__gueltigVon
    @property
    def GueltigBis(self): return self.__gueltigBis
    @property
    def LinienFilter(self): return self.__linienFilter
    @property
    def LinienFilterHRDF(self): return self.__linienFilterHRDF
    @property
    def BetreiberFilter(self): return self.__betreiberFilter
    @property
    def BetreiberFilterHRDF(self): return self.__betreiberFilterHRDF
    @property
    def ProduktFilter(self): return self.__produktFilter
    @property
    def VerkehrsmittelTextFilter(self): return self.__verkehrsmittelTextFilter
    @property
    def Haltfilter(self): return self.__haltFilter
    @property
    def UmlaufFilter(self): return self.__umlaufFilter
    @property
    def UmlaufID(self): return self.__umlaUmlaufID
    @property
    def FahrplanVersionID(self): return self.__fahrplanVersionID
    @property
    def DatenVorhandenBis(self): return self.__datenVorhandenBis
    @property
    def MitGesAnschluss(self): return self.__mitGesAnschluss
    @property
    def MitBereitsAktivenFahrten(self): return self.__mitBereitsAktiveFahrten
    @property
    def MitFormation(self): return self.__mitFormation


    @property
    def VDVLinienfahrplaene(self): return self.__vdvLinienFahrplaene.values()

    @GueltigVon.setter
    def GueltigVon(self, v): self.__gueltigVon = v
    @GueltigBis.setter
    def GueltigBis(self, v): self.__gueltigBis = v
    @LinienFilter.setter
    def LinienFilter(self, v): self.__linienFilter = v
    @LinienFilterHRDF.setter
    def LinienFilterHRDF(self, v): self.__linienFilterHRDF = v
    @BetreiberFilter.setter
    def BetreiberFilter(self, v): self.__betreiberFilter = v
    @BetreiberFilterHRDF.setter
    def BetreiberFilterHRDF(self, v): self.__betreiberFilterHRDF = v

    def isEqual(self, other):
        """ Vergleich von 2 VDVPartnerServiceAboAUSREF """
        return ( isinstance(other, VdvPSAboAUSREF)
                and super().isEqual(other)
                and self.GueltigVon == other.GueltigVon
                and self.GueltigBis == other.GueltigBis
                # Listen vergleichen
                and VDV.vdvIsEqualElementList(self.LinienFilter, other.LinienFilter, False)
                and VDV.vdvIsEqualElementList(self.BetreiberFilter, other.BetreiberFilter, False))
        

    def addLinienFilter(self, linienID, richtungsID, vdvMapper):
        self.__linienFilter.append((linienID,richtungsID))
        # die Linienangaben sind RV-Konform (85:827:10). Für die weitere Verarbeitung muss dies auf HRDF gemappt werden
        lineno = vdvMapper.mapLineno(linienID)
        self.__linienFilterHRDF.append((lineno,richtungsID))

    def addBetreiberFilter(self, betreiberID, vdvMapper):
        self.__betreiberFilter.append(betreiberID)
        # die Betreiberangaben sind RV-Konform (85:827). Für die weitere Verarbeitung muss dies auf HRDF gemappt werden
        operationalno = vdvMapper.mapOperationalno(betreiberID)
        self.__betreiberFilterHRDF.append(operationalno)

    def existsVDVLinienfahrplan(self, linenfahrplan):
        """ Prüft, ob ein Linienfahrplan bereits vorhanden ist """
        return (hash(linenfahrplan) in self.__vdvLinienFahrplaene)
    def vdvLinienfahrplan(self, linienfahrplanHash):
        """ liefert den gewünschten VDVLinienfahrplan """
        return self.__vdvLinienFahrplaene[linienfahrplanHash]
    def clearVDVLinienfahrplaene(self):
        """ Löscht alle VDVLinienfahrpläne """
        self.__vdvLinienFahrplaene.clear()

    def buildBetreiberSQL(self):
        """ Erzeugt die WHERE-Bedingung für die Betreiberangaben im Abo """
        if len(self.__betreiberFilterHRDF) > 0:
            return " operationalno in ('"+ "','".join(self.__betreiberFilterHRDF) + "')"
        else:
            return None

    def buildLinienSQL(self):
        """ Erzeugt die WHERE-Bedingung für die Linienangaben im Abo """
        if (len(self.__linienFilterHRDF) > 0):
            linienSQL = ""
            cnt = 1
            for linienRichtung in self.__linienFilterHRDF:
                # linienRichtung => tuple von linienID und richtungsID
                if cnt > 1: linienSQL += " or "
                linienSQL += "(CASE WHEN array_position(infotextcode, 'RN') IS NULL THEN coalesce(lineno, cast(tripno as varchar)) ELSE infotext_de[array_position(infotextcode, 'RN')] END='"+linienRichtung[0]+"'"
                if (linienRichtung[1] is not None): linienSQL += " and coalesce(directionshort, 'H') = '"+linienRichtung[1]+"'"
                linienSQL += ")"
                cnt += 1
            return linienSQL
        else:
            return None


    def addVDVLinienfahrplan(self, linienfahrplan):
        """ Fügt einen Linienfahrplan zur Sammlung der Linienfahrpläne hinzu """
        self.__vdvLinienFahrplaene[hash(linienfahrplan)] = linienfahrplan

    def addDirtyData(self, linienfahrplanHash):
        """ Nimmt eine Linienfahrplan (Hash) in die Liste der zu übertragenen Linienfahrpläne auf """
        self.DirtyData.append(linienfahrplanHash)

    def removeDirtyData(self, linienfahrplanHash):
        """ Entfernt einen Linienfahrplan (Hash) aus der Liste der zu übertragenen Linienfahrpläne """
        try:
            self.DirtyData.remove(linienfahrplanHash)
        except ValueError:
            pass        






