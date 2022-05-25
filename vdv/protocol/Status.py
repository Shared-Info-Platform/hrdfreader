import datetime
import time
import xml.etree.ElementTree as ET
import vdv.protocol.vdvProtocol as VDV

class StatusAntwort():
    """ Beschreibt die StatusAntwort """
    def __init__(self, zst, startDienstZst):
        self.__Zst = zst
        self.__Ergebnis = 'ok'
        self.__DatenBereit = False
        self.__StartDienstZst = startDienstZst
        self.__DatenVersionID = None

    @property
    def Zst(self):
        return self.__Zst
    @property
    def Ergebnis(self):
        return self.__Ergebnis
    @property
    def DatenBereit(self):
        return self.__DatenBereit
    @property
    def StartDienstZst(self):
        return self.__StartDienstZst
    @property
    def DatenVersionID(self):
        return self.__DatenVersionID

    @Zst.setter
    def Zst(self, v):
        self.__Zst = v
    @Ergebnis.setter
    def Ergebnis(self, v):
        self.__Ergebnis = v
    @DatenBereit.setter
    def DatenBereit(self, v):
        self.__DatenBereit = v
    @StartDienstZst.setter
    def StartDienstZst(self, v):
        self.__StartDienstZst = v
    @DatenVersionID.setter
    def DatenVersionID(self, v):
        self.__DatenVersionID = v

    def toXMLString(self):
        """ Liefert die StatusAntwort als XML """
        root = ET.Element('StatusAntwort')
        ET.SubElement(root, 'Status', {"Zst": VDV.vdvDateTimeFormat(self.Zst), "Ergebnis": self.Ergebnis})
        ET.SubElement(root, "DatenBereit").text = str(self.DatenBereit).lower()
        ET.SubElement(root, "StartDienstZst").text = VDV.vdvDateTimeFormat(self.StartDienstZst) #.strftime("%Y-%m-%dT%H:%M:%SZ")
        if (self.DatenVersionID is not None):
            ET.SubElement(root, "DatenVersionID").text = self.DatenVersionID

        statusXML = ET.tostring(root, encoding="unicode", short_empty_elements=False)
        return statusXML;

class StatusAnfrage():
    """Beschreibt die VDV-StatusAnfrage"""
    def __init__(self, xmlString):
        self.__Sender = '??'
        self.__Zst = VDV.vdvLocalToUTC(datetime.datetime.now())
        self.__fromXMLString(xmlString)

    @property
    def Sender(self):
        return self.__Sender
    @property
    def Zst(self):
        return self.__Zst
    @Sender.setter
    def Sender(self, v):
        self.__Sender = v
    @Zst.setter
    def Zst(self, v):
        self.__Zst = v

    def __fromXMLString(self, xmlString):
        """ Parst den xmlString und füllt das Objekt """
        tree = ET.fromstring(xmlString)
        self.__Sender = tree.attrib["Sender"]
        self.__Zst = VDV.vdvStrToDateTimeUTC(tree.attrib["Zst"])
        
        

