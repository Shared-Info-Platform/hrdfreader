import datetime
import time
import xml.etree.ElementTree as ET
import vdv.protocol.Bestaetigung
import vdv.protocol.vdvProtocol as VDV

class AboAntwort():
    """ Beschreibt die AboAntwort """
    def __init__(self, bestaetigung):
        self.__XSDVersionID = 'xsd_2017d'
        self.__Bestaetigung = bestaetigung
        self.__BestaetigungMitAboIDs = list()

    @property
    def XSDVersionID(self):
        return self.__XSDVersionID
    @property
    def Bestaetigung(self):
        return self.__Bestaetigung
    @property
    def BestaetigungMitAboIDs(self):
        return self.__BestaetigungMitAboIDs

    @XSDVersionID.setter
    def XSDVersionID(self, v):
        self.__XSDVersionID = v
    @Bestaetigung.setter
    def Bestaetigung(self, v):
        self.__Bestaetigung = v
    def addBestaetigungMitAboID(self, newBestaetigung):
        self.__BestaetigungMitAboIDs.append(newBestaetigung)

    def toXMLString(self):
        """ Liefert die AboAntwort als XML """
        root = ET.Element('AboAntwort', {"XSDVersionID": self.__XSDVersionID})
        # Zuerst prüfen, ob BestaetigungMitAboID geschickt werden soll
        # Danach nur die einfache Bestaetigung
        if (len(self.BestaetigungMitAboIDs) > 0 ):
            for bestaetigungMitAboID in self.BestaetigungMitAboIDs:
                root.append(bestaetigungMitAboID.toXMLElement())
        elif (self.Bestaetigung is not None):
            root.append(self.Bestaetigung.toXMLElement())

        aboAntwortXML = ET.tostring(root, encoding="unicode", short_empty_elements=False)
        return aboAntwortXML;



class AboAnfrage():
    """ Beschreibt die VDV-AboAnfrage """
    def __init__(self, xmlString):
        self.__Sender = None
        self.__Zst = None
        self.__XSDVersionID = None
        self.__AboLoeschenList = list()
        self.__AboLoeschenAlle = None
        self.__ServiceAboList = list()
        self.__fromXMLString(xmlString)

    @property
    def Sender(self):
        return self.__Sender
    @property
    def Zst(self):
        return self.__Zst
    @property
    def XSDVersionID(self):
        return self.__XSDVersionID
    @property
    def AboLoeschenList(self):
        return self.__AboLoeschenList
    @property
    def AboLoeschenAlle(self):
        return self.__AboLoeschenAlle
    @property
    def ServiceAboList(self):
        return self.__ServiceAboList


    def __fromXMLString(self, xmlString):
        """ Parst den xmlString und füllt das Objekt """
        tree = ET.fromstring(xmlString)
        self.__Sender = tree.attrib["Sender"]
        self.__Zst = VDV.vdvStrToDateTimeUTC(tree.attrib["Zst"])
        if "XSDVersionID" in tree.attrib: self.__XSDVersionID = tree.attrib["XSDVersionID"]
        
        # Prüfen auf einzelne AboLoeschen Elemente
        for aboLoeschen in tree.findall('AboLoeschen'):
            self.__AboLoeschenList.append(aboLoeschen.text)

        if (tree.find('AboLoeschenAlle') is not None): self.__AboLoeschenAlle = True

        if ((len(self.__AboLoeschenList) == 0) and (self.__AboLoeschenAlle is None)):
            # Jetzt schauen wir nach den unterschiedlichen dienstspezifischen AboAnfragen
            for serviceAbo in tree:
                self.__ServiceAboList.append(serviceAbo)

