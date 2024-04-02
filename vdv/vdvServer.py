import time, threading
import datetime
import os
import enum
from http.server import HTTPServer, BaseHTTPRequestHandler, HTTPStatus
from socketserver import ThreadingMixIn
from vdv.vdvlog import logger
from vdv.vdvPartnerService import VdvPartnerService, PartnerServiceType, VdvPartnerServiceAbo
from vdv.vdvPSAUSREF import VdvPSAUSREF
from vdv.protocol.Status import StatusAnfrage, StatusAntwort
from vdv.protocol.AboVerwalten import AboAnfrage, AboAntwort
from vdv.protocol.Bestaetigung import Bestaetigung, BestaetigungMitAboID, Fehlernummer
from vdv.protocol.DatenAbrufen import DatenAbrufenAnfrage, DatenAbrufenAntwort
import vdv.protocol.vdvProtocol as VDV


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class VDVRequestIdent(enum.Enum):
    """ Enum für VDV-Request Kennungen """
    status = 1
    clientstatus = 2
    aboverwalten = 3
    datenbereit = 4
    datenabrufen = 5

class VdvServer(threading.Thread):
    """description of class"""

    def __init__(self, serverConfigName, vdvConfig):
        threading.Thread.__init__(self)
        self.__serverConfigName = serverConfigName
        self.__vdvConfig = vdvConfig
        self.__port = int(self.__vdvConfig[serverConfigName]['port'])
        self.__partnerServices = dict()
        self.daemon = True
        logger.info("Anlegen des VDVServers {} auf Port {}".format(self.__serverConfigName, self.__port))
        for x in range(int(self.__vdvConfig[serverConfigName]['partnerServiceCnt'])):
            partnerNo = x+1
            partnerConfigName = serverConfigName+"_P"+str(partnerNo)
            partnerServiceUrl = self.__vdvConfig[partnerConfigName]['serviceUrl']
            serviceType = PartnerServiceType[self.__vdvConfig[partnerConfigName]['serviceType']]
            if (serviceType == PartnerServiceType.AUSREF): self.__partnerServices[partnerServiceUrl] = VdvPSAUSREF(partnerConfigName, self.__vdvConfig)
        # Starten des VDVServers
        self.start()

    def run(self):
        server = self

        class VdvServerRequestHandler(BaseHTTPRequestHandler):
            """ Die Klasse stellt die allgemeinen VDV-RequestHandler-Funktionen zur Verfügung """

            def log_request(self, code='-', size='-'):
                """ Überschreiben des log_request() aus BaseHTTPRequestHandler => brauchen wir nicht """
                pass

            def do_GET(self):
                """ GET requests werden hier entgegen genommen und im Server weiter verarbeitet """
                server.handleGETRequest(self)

            def do_POST(self):
                """ POST requests werden hier entgegen genommen und im Server weiter verarbeitet """
                server.handleVdvRequest(self)

            def sendResponse(self, httpStatus, responseData):
                self.send_response(httpStatus)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(responseData.encode('iso-8859-1'))

            def vdvServiceUrl(self):
                """ liefert die Service-URL zur Erkennung des Partners """
                return os.path.dirname(self.path)

            def vdvRequestIdent(self):
                """ Liefert die aktuelle VDV-Request Kennung """
                return os.path.splitext(os.path.basename(self.path))[0].lower()

        server_address = ('0.0.0.0', self.__port)
        self.__httpd = ThreadingHTTPServer(server_address, VdvServerRequestHandler)        
        self.__httpd.serve_forever()

    def shutdown(self):
        self.__httpd.server_close()
        self.__httpd.shutdown()


    def handleGETRequest(self, vdvRequest):
        """ Bearbeiten von GET-Requests (Browser). Diese Requests werden den aktuellen Status des
            entsprechenden PartnerService zur Verfügung stellen
        """
        # Auswerten der GET-Daten
        responseData = "GET request for"
        httpStatusCode = HTTPStatus.OK
        vdvRequest.sendResponse(httpStatusCode, responseData)

    def handleVdvRequest(self, vdvRequest):
        """ Bearbeitet den eingehenden VDV-Request """
        responseData = "Bad request"
        httpStatusCode = HTTPStatus.BAD_REQUEST
        
        serviceUrl = vdvRequest.vdvServiceUrl()
        vdvPartnerService = self.__partnerServices.get(serviceUrl)

        try:
            if (vdvPartnerService is None):
                responseData = "The requested service '{}' is not registered".format(serviceUrl)
                httpStatusCode = HTTPStatus.NOT_FOUND
            else:
                content_length = int(vdvRequest.headers['Content-Length']) # <--- Gets the size of data
                xmlString = vdvRequest.rfile.read(content_length) # <--- Gets the data itself
                logger.info("{}: incoming request {}\n{}".format(vdvPartnerService.ServiceName, vdvRequest.path, xmlString.decode('utf-8')))
                # Auswerten der POST-Daten verteilen
                if (vdvRequest.vdvRequestIdent() == VDVRequestIdent.status.name):
                    statusAntwort = self.__handleStatusAnfrage(xmlString, vdvPartnerService)
                    responseData = '<?xml version="1.0" encoding="ISO-8859-1"?>'
                    responseData += statusAntwort.toXMLString();
                    httpStatusCode = HTTPStatus.OK

                elif (vdvRequest.vdvRequestIdent() == VDVRequestIdent.aboverwalten.name):
                    aboAntwort = self.__handleAboAnfrage(xmlString, vdvPartnerService)
                    responseData = '<?xml version="1.0" encoding="ISO-8859-1"?>'
                    responseData += aboAntwort.toXMLString()
                    httpStatusCode = HTTPStatus.OK

                elif (vdvRequest.vdvRequestIdent() == VDVRequestIdent.datenabrufen.name):
                    datenAbrufenAntwort = self.__handleDatenAbrufenAnfrage(xmlString, vdvPartnerService)
                    responseData = '<?xml version="1.0" encoding="ISO-8859-1"?>'
                    responseData += datenAbrufenAntwort.toXMLString()
                    httpStatusCode = HTTPStatus.OK

                logger.info("{}: outgoing response {}\n{}".format(vdvPartnerService.ServiceName, vdvRequest.path, responseData))

        except Exception as e:
            responseData = "Interner Server-Fehler aufgetreten"
            httpStatusCode = HTTPStatus.INTERNAL_SERVER_ERROR
            logger.info("{}: outgoing response {}\n{}: {}".format(vdvPartnerService.ServiceName, vdvRequest.path, responseData, e))

        vdvRequest.sendResponse(httpStatusCode, responseData)

    def __handleStatusAnfrage(self, xmlString, vdvPartnerService):
        """ Bearbeitet eine StatusAnfrage und liefert eine StatusAntwort bzgl des entsprechenden vdvPartnerService

            xmlString - erwartete StatusAnfrage als xmlString
            vdvPartnerService - Service an den diese StatusAnfrage gerichtet ist
        """        
        statusAntwort = StatusAntwort(VDV.vdvLocalToUTC(datetime.datetime.now()), vdvPartnerService.StartTime )

        try:
            statusAnfrage = StatusAnfrage(xmlString)
            if (vdvPartnerService.SenderName != statusAnfrage.Sender):
                statusAntwort.Ergebnis = 'notok'
                logger.warning("{} => Unbekannter Sender {}".format(vdvPartnerService.ServiceName, statusAnfrage.Sender))
            else:
                statusAntwort.DatenBereit = VDV.vdvToVDVBool(vdvPartnerService.isDataReady())
                statusAntwort.DatenVersionID = vdvPartnerService.DatenVersionID

        except Exception as e:
            statusAntwort.Ergebnis = 'notok'
            logger.error("{} => Fehler beim Parsen von '{}': {}".format(vdvPartnerService.ServiceName, xmlString, e))

        return statusAntwort

    def __handleAboAnfrage(self, xmlString, vdvPartnerService):
        """ Bearbeitet eine AboAnfrage und liefert eine AboAntwort bzgl des entsprechenden vdvPartnerService
            
            xmlString - erwartete AboAnfrage als xmlString
            vdvPartnerService - Service an den diese AboAnfrage gerichtet ist
        """
        try:
            aboAnfrage = AboAnfrage(xmlString)
            if (aboAnfrage.Sender != vdvPartnerService.SenderName):
                aboAntwort = AboAntwort(Bestaetigung())
                aboAntwort.Bestaetigung.Ergebnis = 'notok'
                aboAntwort.Bestaetigung.Fehlernummer = Fehlernummer.REF_SENDER.value
                aboAntwort.Bestaetigung.Fehlertext = "Unbekannter Sender"

            elif (aboAnfrage.AboLoeschenAlle is not None):
                # AboLoeschenAlle
                aboAntwort = AboAntwort(Bestaetigung())           
                vdvPartnerService.deleteAllAbos()

            elif(len(aboAnfrage.AboLoeschenList)>0):
                # AboLoeschen
                aboAntwort = AboAntwort(Bestaetigung())
                for aboID in aboAnfrage.AboLoeschenList:
                    vdvPartnerService.deleteAbo(aboID)
            else:
                # AboAnfragen dienstspezifisch
                aboAntwort = vdvPartnerService.createOrUpdateAbos(aboAnfrage.ServiceAboList)

        except Exception as e:
            aboAntwort = AboAntwort(Bestaetigung())
            aboAntwort.Bestaetigung.Ergebnis = 'notok'
            aboAntwort.Bestaetigung.Fehlernummer = Fehlernummer.ERR_NOREP.value
            aboAntwort.Bestaetigung.Fehlertext = "Unzulässiges XML"
            logger.error("{} => Fehler beim Empfang von AboAnfrage: {}".format(vdvPartnerService.ServiceName, e))

        return aboAntwort

    def __handleDatenAbrufenAnfrage(self, xmlString, vdvPartnerService):
        """ Bearbeitet eine DatenAbrufenAnfrage und liefert eine DatenAbrufenAntwort bzgl des entsprechenden vdvPartnerService
            
            xmlString - erwartete DatenAbrufenAnfrage als xmlString
            vdvPartnerService - Service an den diese DatenAbrufenAnfrage gerichtet ist
        """
        try:
            datenAbrufenAnfrage = DatenAbrufenAnfrage(xmlString)
            if (datenAbrufenAnfrage.Sender != vdvPartnerService.SenderName):
                datenAbrufenAntwort = DatenAbrufenAntwort(Bestaetigung())
                datenAbrufenAntwort.Bestaetigung.Ergebnis = 'notok'
                datenAbrufenAntwort.Bestaetigung.Fehlernummer = Fehlernummer.REF_SENDER.value
                datenAbrufenAntwort.Bestaetigung.Fehlertext = "Unbekannter Sender"
            else:
                datenAbrufenAntwort = vdvPartnerService.createDatenAbrufenAntwort(datenAbrufenAnfrage.DatenSatzAlle)

        except Exception as e:
            logger.error("{} => Fehler beim Empfang von DatenAbrufenAnfrage: {}".format(vdvPartnerService.ServiceName, e))

        return datenAbrufenAntwort

    def checkPartnerServices(self):
        """ Prüfen der ParnterServices, ob Aktionen anstehen """
        for partnerService in self.__partnerServices.values():
            # Aktualisieren der Mappingdaten
            partnerService.refreshMappingData()
            # Aktualisieren/Prüfen der ServiceAbos
            partnerService.checkPartnerServiceAbos()

