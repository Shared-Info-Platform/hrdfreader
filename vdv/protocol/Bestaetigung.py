import datetime
import time
import enum
import xml.etree.ElementTree as ET

class Fehlernummer(enum.Enum):
    OK = 0
    XML = 100           # genereller XML-Fehler
    REF = 200           # generelle Referenzdatenverletzung
    REF_SENDER = 201    # falscher/unbekannter Sendername
    ERR_NOREP = 300     # Fehler auf Grund dessen die Anfrage nicht wiederholt werden sollte
    ERR_NOREP_SERVICE = 301     # Anfrage passt nicht zum Dienst
    ERR_NOREP_INTERNAL = 302    # Interner Fehler aufgetreten
    ERR_REP = 400       # Fehler auf Grund dessen die Anfrage wiederholt werden kann

class Bestaetigung():
    """ Beschreibt die Bestaetigung
        Fehlernummern:
        0 => ok
        100-199 => XML-Fehler
        200-299 => Referenzdatenverletzung (z.B. ungültiges Attribut "Sender" in einer Anfrage)
        300-399 => übrige Fehler auf Grund von fehlerhaften Anfragen. Anfrage soll nicht wiederholt werden
        400-499 => übrige Antworten auf Grund von fehlerhaften Anfragen . Anfrage kann später wiederholt werden
    """

    def __init__(self):
        # Attribute
        self.__Zst = datetime.datetime.utcnow()
        self.__Ergebnis = "ok"
        self.__Fehlernummer = Fehlernummer.OK.value
        # Elemente
        self.__Fehlertext = None
        self.__DatenGueltigAb = None
        self.__DatenGueltigBis = None
        self.__KuerzMoeglicherZyklus = None

    @property
    def Zst(self):
        return self.__Zst
    @property
    def Ergebnis(self):
        return self.__Ergebnis
    @property
    def Fehlernummer(self):
        return self.__Fehlernummer
    @property
    def Fehlertext(self):
        return self.__Fehlertext
    @property
    def DatenGueltigAb(self):
        return self.__DatenGueltigAb
    @property
    def DatenGueltigBis(self):
        return self.__DatenGueltigBis
    @property
    def KuerzMoeglicherZyklus(self):
        return self.__KuerzMoeglicherZyklus

    @Zst.setter
    def Zst(self, v):
        self.__Zst = v
    @Ergebnis.setter
    def Ergebnis(self, v):
        self.__Ergebnis = v
    @Fehlernummer.setter
    def Fehlernummer(self, v):
        self.__Fehlernummer = v
    @Fehlertext.setter
    def Fehlertext(self, v):
        self.__Fehlertext = v
    @DatenGueltigAb.setter
    def DatenGueltigAb(self, v):
        self.__DatenGueltigAb = v
    @DatenGueltigBis.setter
    def DatenGueltigBis(self, v):
        return self.__DatenGueltigBis
    @KuerzMoeglicherZyklus.setter
    def KuerzMoeglicherZyklus(self, v):
        self.__KuerzMoeglicherZyklus = v

    def toXMLElement(self):
        """ Liefert die Bestätigung als XML """
        ownRoot = ET.Element('Bestaetigung', {"Zst": self.Zst.strftime("%Y-%m-%dT%H:%M:%SZ"), "Ergebnis": self.Ergebnis, "Fehlernummer": str(self.Fehlernummer)})
        if (self.Fehlertext is not None): ET.SubElement(ownRoot, 'Fehlertext').text = self.Fehlertext
        if (self.DatenGueltigAb is not None): ET.SubElement(ownRoot, "DatenGueltigAb").text = self.DatenGueltigAb.strftime("%Y-%m-%dT%H:%M:%SZ")
        if (self.DatenGueltigBis is not None): ET.SubElement(ownRoot, "DatenGueltigBis").text = self.DatenGueltigBis.strftime("%Y-%m-%dT%H:%M:%SZ")
        if (self.KuerzMoeglicherZyklus is not None): ET.SubElement(ownRoot, "KuerzMoeglicherZyklus").text = str(self.KuerzMoeglicherZyklus)
        return ownRoot

class BestaetigungMitAboID():
    """ Beschreibt die Bestaetigung mit AboId """
    def __init__(self, aboID):
        # Attribute
        self.__AboID = aboID
        # Elemente
        self.__Bestaetigung = Bestaetigung()
    @property
    def AboID(self):
        return self.__AboID
    @property
    def Bestaetigung(self):
        return self.__Bestaetigung
    @AboID.setter
    def AboID(self, v):
        self.__AboID = v
    @Bestaetigung.setter
    def Bestaetigung(self, v):
        self.__Bestaetigung

    def toXMLElement(self):
        """ Liefert die Bestätigung als XML-Element """
        ownRoot = ET.Element('BestaetigungMitAboID', {"AboID": self.AboID})
        ownRoot.append(self.Bestaetigung.toXMLElement())
        return ownRoot