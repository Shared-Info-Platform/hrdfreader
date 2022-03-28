import datetime
import time
import xml.etree.ElementTree as ET
import vdv.protocol.Bestaetigung
import vdv.protocol.vdvProtocol as VDV
from vdv.protocol.AUSNachricht import AUSNachricht

class DatenAbrufenAnfrage():
    """ Beschreibt die VDV-DatenAbrufenAnfrage """
    def __init__(self, xmlString):
        self.__Sender = '??'
        self.__Zst = datetime.datetime.utcnow()
        self.__DatensatzAlle = None
        self.__fromXMLString(xmlString)

    @property
    def Sender(self): return self.__Sender
    @property
    def Zst(self): return self.__Zst
    @property
    def DatenSatzAlle(self): return self.__DatensatzAlle
 
    def __fromXMLString(self, xmlString):
        """ Parst den xmlString und füllt das Objekt """
        tree = ET.fromstring(xmlString)
        self.__Sender = tree.attrib["Sender"]
        self.__Zst = VDV.vdvStrToDateTimeUTC(tree.attrib["Zst"])
        if (tree.find('DatensatzAlle') is not None): self.__DatensatzAlle = VDV.vdvTreeElementToBool(tree.find('DatensatzAlle'), False)

class DatenAbrufenAntwort():
    """ Beschreibt die DatenAbrufenAntwort """
    def __init__(self, bestaetigung):
        self.__Bestaetigung = bestaetigung
        self.__WeitereDaten = False
        self.__AUSNachricht = list()

    @property
    def Bestaetigung(self):
        return self.__Bestaetigung
    @property
    def WeitereDaten(self):
        return self.__WeitereDaten
    @WeitereDaten.setter
    def WeitereDaten(self, v): self.__WeitereDaten = v

    def addAUSNachricht(self, ausNachricht):
        self.__AUSNachricht.append(ausNachricht)

    def toXMLString(self):
        """ Liefert die DatenAbrufenAntwort als XMLString """
        root = ET.Element('DatenAbrufenAntwort')
        root.append(self.Bestaetigung.toXMLElement())
        ET.SubElement(root, 'WeitereDaten').text = str(self.__WeitereDaten).lower()
        for ausNachricht in self.__AUSNachricht:
            root.append(ausNachricht.toXMLElement())

        datenAbrufenAntwortXML = ET.tostring(root, encoding="unicode", short_empty_elements=False)
        return datenAbrufenAntwortXML;