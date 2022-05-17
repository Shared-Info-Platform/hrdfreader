import datetime
import time
import xml.etree.ElementTree as ET
import vdv.protocol.vdvProtocol as VDV

class ServiceAttribut():
    """
    Beschreibt eine ServiceAttribut
    """
    def __init__(self, name, wert):
        self.__Name = name
        self.__Wert = wert

    @property
    def Name(self): return self.__Name
    @property
    def Wert(self): return self.__Wert

    def isEqual(self, other):
        """ Vergleich von 2 ServiceAttributen """
        return (isinstance(other, ServiceAttribut) and self.Name == other.Name and self.Wert == other.Wert)

    def toXMLElement(self):
        """ Liefert ein ServiceAttribut als XML-Element """
        ownRoot = ET.Element('ServiceAttribut')
        if (self.Name is not None): ET.SubElement(ownRoot, 'Name').text = self.Name
        if (self.Wert is not None): ET.SubElement(ownRoot, 'Wert').text = self.Wert
        return ownRoot

class SollHalt():
    """
    Beschreibt einen VDV-SollHalt
    """
    def __init__(self, haltID):
        self.__HaltID = haltID
        self.__HaltestellenName = None
        self.__Abfahrtszeit = None
        self.__Ankunftszeit = None
        self.__AbfahrtssteigText = None
        self.__AnkunftssteigText = None
        self.__AbfahrtsSektorenText = None
        self.__AnkunftsSektorenText = None
        self.__Einsteigeverbot = None
        self.__Aussteigeverbot = None
        self.__Durchfahrt = None
        self.__RichtungsText = None
        self.__VonRichtungsText = None
        self.__HinweisText = list()
        self.__LinienfahrwegID = None
        self.__SollAnschluss = list()
        
    @property
    def HaltID(self) : return self.__HaltID
    @property
    def HaltestellenName(self): return self.__HaltestellenName
    @property
    def Abfahrtszeit(self): return self.__Abfahrtszeit
    @property
    def Ankunftszeit(self): return self.__Ankunftszeit
    @property
    def AbfahrtssteigText(self): return self.__AbfahrtssteigText
    @property
    def AnkunftssteigText(self): return self.__AnkunftssteigText
    @property
    def AbfahrtsSektorenText(self): return self.__AbfahrtsSektorenText
    @property
    def AnkunftsSektorenText(self): return self.__AnkunftsSektorenText
    @property
    def Einsteigeverbot(self): return self.__Einsteigeverbot
    @property
    def Aussteigeverbot(self): return self.__Aussteigeverbot
    @property
    def Durchfahrt(self): return self.__Durchfahrt
    @property
    def RichtungsText(self): return self.__RichtungsText
    @property
    def VonRichtungsText(self): return self.__VonRichtungsText
    @property
    def HinweisText(self): return self.__HinweisText
    @property
    def LinienfahrwegID(self): return self.__LinienfahrwegID
    @property
    def SollAnschluss(self): return self.__SollAnschluss

    @HaltestellenName.setter
    def HaltestellenName(self, v): self.__HaltestellenName = v
    @Abfahrtszeit.setter
    def Abfahrtszeit(self, v): self.__Abfahrtszeit = v
    @Ankunftszeit.setter
    def Ankunftszeit(self, v): self.__Ankunftszeit = v
    @AbfahrtssteigText.setter
    def AbfahrtssteigText(self, v): self.__Abfahrtszeit = v
    @AnkunftssteigText.setter
    def AnkunftssteigText(self, v): self.__AnkunftssteigText = v
    @AbfahrtsSektorenText.setter
    def AbfahrtsSektorenText(self, v): self.__AbfahrtsSektorenText = v
    @AnkunftsSektorenText.setter
    def AnkunftsSektorenText(self, v): self.__AnkunftsSektorenText = v
    @Einsteigeverbot.setter
    def Einsteigeverbot(self, v): self.__Einsteigeverbot = v
    @Aussteigeverbot.setter
    def Aussteigeverbot(self, v): self.__Aussteigeverbot = v
    @Durchfahrt.setter
    def Durchfahrt(self, v): self.__Durchfahrt = v
    @RichtungsText.setter
    def RichtungsText(self, v): self.__RichtungsText = v
    @VonRichtungsText.setter
    def VonRichtungsText(self, v): self.__VonRichtungsText = v
    @LinienfahrwegID.setter
    def LinienfahrwegID(self, v): self.__LinienfahrwegID = v

    def isEqual(self, other):
        """ Vergleich von 2 SollHalten """
        return ( isinstance(other, SollHalt)
                 and self.HaltID == other.HaltID
                 and self.HaltestellenName == other.HaltestellenName
                 and self.Abfahrtszeit == other.Abfahrtszeit
                 and self.Ankunftszeit == other.Ankunftszeit 
                 and self.AbfahrtssteigText == other.AbfahrtssteigText
                 and self.AnkunftssteigText == other.AnkunftssteigText
                 and self.AbfahrtsSektorenText == other.AbfahrtsSektorenText
                 and self.AnkunftsSektorenText == other.AnkunftsSektorenText
                 and self.Einsteigeverbot == other.Einsteigeverbot
                 and self.Aussteigeverbot == other.Aussteigeverbot
                 and self.Durchfahrt == other.Durchfahrt
                 and self.RichtungsText == other.RichtungsText
                 and self.VonRichtungsText == other.VonRichtungsText             
                 and self.LinienfahrwegID == other.LinienfahrwegID
                 # Einfache Elemente sind gleich => Prüfen der Listen
                 and VDV.vdvIsEqualElementList(self.HinweisText, other.HinweisText, False)
                 and VDV.vdvIsEqualElementList(self.SollAnschluss, other.SollAnschluss, True))

    def addHinweisText(self, hinweisText):
        """ Fügt einen Fahrtspezifischen Hinweis hinzu """
        self.__HinweisText.append(hinweisText)

    def addSollAnschluss(self, sollAnschluss):
        """ Fügt eine SollAnschluss hinzu """
        self.__SollAnschluss.append(sollAnschluss)

    def toXMLElement(self):
        """ Liefert eine SollFahrt als XML-Element """
        ownRoot = ET.Element('SollHalt')
        if (self.HaltID is not None): ET.SubElement(ownRoot, 'HaltID').text = self.HaltID
        if (self.HaltestellenName is not None): ET.SubElement(ownRoot, 'HaltestellenName').text = self.HaltestellenName
        if (self.Abfahrtszeit is not None): ET.SubElement(ownRoot, 'Abfahrtszeit').text = self.Abfahrtszeit.astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
        if (self.Ankunftszeit is not None): ET.SubElement(ownRoot, 'Ankunftszeit').text = self.Ankunftszeit.astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
        if (self.AbfahrtssteigText is not None): ET.SubElement(ownRoot, 'AbfahrtssteigText').text = self.AbfahrtssteigText
        if (self.AnkunftssteigText is not None): ET.SubElement(ownRoot, 'AnkunftssteigText').text = self.AnkunftssteigText
        if (self.AbfahrtsSektorenText is not None): ET.SubElement(ownRoot, 'AbfahrtsSektorenText').text = self.AbfahrtsSektorenText
        if (self.AnkunftsSektorenText is not None): ET.SubElement(ownRoot, 'AnkunftsSektorenText').text = self.AnkunftsSektorenText
        if (self.Einsteigeverbot is not None and self.Einsteigeverbot == True): ET.SubElement(ownRoot, 'Einsteigeverbot').text = VDV.vdvToVDVBool(self.Einsteigeverbot)
        if (self.Aussteigeverbot is not None and self.Aussteigeverbot == True): ET.SubElement(ownRoot, 'Aussteigeverbot').text = VDV.vdvToVDVBool(self.Aussteigeverbot)
        if (self.Durchfahrt is not None): ET.SubElement(ownRoot, 'Durchfahrt').text = VDV.vdvToVDVBool(self.Durchfahrt)
        if (self.RichtungsText is not None): ET.SubElement(ownRoot, 'RichtungsText').text = self.RichtungsText
        if (self.VonRichtungsText is not None): ET.SubElement(ownRoot, 'VonRichtungsText').text = self.VonRichtungsText
        for hinweisText in self.__HinweisText: ET.SubElement(ownRoot, 'HinweisText').text = hinweisText
        if (self.LinienfahrwegID is not None): ET.SubElement(ownRoot, 'LinienfahrwegID').text = self.LinienfahrwegID
        for sollAnschluss in self.__SollAnschluss: ownRoot.append(sollAnschluss.toXMLElement())
        return ownRoot

class SollFahrt():
    """ Beschreibt eine VDV-Sollfahrt

    fahrtbezeichner - Fahrbezeichner der Fahrt
    betriebstag - Betriebstag der Fahrt
    """
    def __init__(self, fahrtBezeichner, betriebstag):
        self.__Zst = datetime.datetime.utcnow()
        self.__FahrtBezeichner = fahrtBezeichner
        self.__Betriebstag = betriebstag
        self.__SollHalt = list()
        self.__UmlaufId = None
        self.__KursNr = None
        self.__FahrtBezeichnerText = list()
        self.__VerkehrsmittelNummer = None
        self.__LinienText = None
        self.__ProduktID = None
        self.__RichtungsText = None
        self.__VonRichtungsText = None
        self.__HinweisText = list()
        self.__LinienfahrwegID = None
        self.__Zugname = None
        self.__VerkehrsmittelText = None
        self.__Zusatzfahrt = None
        self.__FaelltAus = None
        self.__FahrradMitnahme = None
        self.__FahrzeugTypID = None
        self.__ServiceAttribut = list()
        self.__SollFormation = None
        self.__FahrtBeziehung = list()

    @property
    def Zst(self) : return self.__Zst
    @property
    def FahrtBezeichner(self): return self.__FahrtBezeichner
    @property
    def Betriebstag(self): return self.__Betriebstag
    @property
    def SollHalt(self): return self.__SollHalt
    @property
    def UmlaufID(self): return self.__UmlaufId
    @property
    def KursNr(self): return self.__KursNr
    @property
    def FahrtBezeichnerText(self): return self.__FahrtBezeichnerText
    @property
    def VerkehrsmittelNummer(self): return self.__VerkehrsmittelNummer
    @property
    def LinienText(self): return self.__LinienText
    @property
    def ProduktID(self): return self.__ProduktID    
    @property
    def RichtungsText(self): return self.__RichtungsText
    @property
    def VonRichtungsText(self): return self.__VonRichtungsText
    @property
    def HinweisText(self): return self.__HinweisText
    @property
    def LinienfahrwegID(self): return self.__LinienfahrwegID
    @property
    def Zugname(self): return self.__Zugname
    @property
    def VerkehrsmittelText(self): return self.__VerkehrsmittelText
    @property
    def Zusatzfahrt(self): return self.__Zusatzfahrt
    @property
    def FaelltAus(self): return self.__FaelltAus
    @property
    def FahrradMitnahme(self): return self.__FahrradMitnahme
    @property
    def FahrzeugTypID(self): return self.__FahrzeugTypID
    @property
    def ServiceAttribut(self): return self.__ServiceAttribut
    @property
    def SollFormation(self): return self.__SollFormation
    @property
    def FahrtBeziehung(self): return self.__FahrtBeziehung

    @UmlaufID.setter
    def UmlaufID(self, v): self.__UmlaufId = v
    @KursNr.setter
    def KursNr(self, v): self.__KursNr = v
    @VerkehrsmittelNummer.setter
    def VerkehrsmittelNummer(self, v): self.__VerkehrsmittelNummer = v
    @LinienText.setter
    def LinienText(self, v): self.__LinienText = v
    @ProduktID.setter
    def ProduktID(self, v): self.__ProduktID = v
    @RichtungsText.setter
    def RichtungsText(self, v): self.__RichtungsText = v
    @VonRichtungsText.setter
    def VonRichtungsText(self, v): self.__VonRichtungsText = v
    @LinienfahrwegID.setter
    def LinienfahrwegID(self, v): self.__LinienfahrwegID = v
    @Zugname.setter
    def Zugname(self, v): self.__Zugname = v
    @VerkehrsmittelText.setter
    def VerkehrsmittelText(self, v): self.__VerkehrsmittelText = v
    @Zusatzfahrt.setter
    def Zusatzfahrt(self, v): self.__Zusatzfahrt = v
    @FaelltAus.setter
    def FaelltAus(self, v): self.__FaelltAus = v
    @FahrradMitnahme.setter
    def FahrradMitnahme(self, v): self.__FahrradMitnahme = v
    @FahrzeugTypID.setter
    def FahrzeugTypID(self, v): self.__FahrzeugTypID = v
    @SollFormation.setter
    def SollFormation(self, v): self.__SollFormation = v

    def isEqual(self, other):
        """ Vergleich von 2 SollFahrten """
        return ( isinstance(other, SollFahrt)
                # Zst wird nicht mit verglichen
                and self.FahrtBezeichner == other.FahrtBezeichner
                and self.Betriebstag == other.Betriebstag
                and self.UmlaufID == other.UmlaufID
                and self.KursNr == other.KursNr
                and self.VerkehrsmittelNummer == other.VerkehrsmittelNummer
                and self.LinienText == other.LinienText
                and self.ProduktID == other.ProduktID
                and self.RichtungsText == other.RichtungsText
                and self.VonRichtungsText == other.VonRichtungsText
                and self.LinienfahrwegID == other.LinienfahrwegID
                and self.Zugname == other.Zugname
                and self.VerkehrsmittelText == other.VerkehrsmittelText
                and self.Zusatzfahrt == other.Zusatzfahrt
                and self.FaelltAus == other.FaelltAus
                and self.FahrradMitnahme == other.FahrradMitnahme
                and self.FahrzeugTypID == other.FahrzeugTypID
                and self.SollFormation == other.SollFormation
                #Elemente sind identisch => Prüfung der einzelnen Listen
                and VDV.vdvIsEqualElementList(self.SollHalt, other.SollHalt, True)
                and VDV.vdvIsEqualElementList(self.FahrtBezeichnerText, other.FahrtBezeichnerText, False)
                and VDV.vdvIsEqualElementList(self.HinweisText, other.HinweisText, False)
                and VDV.vdvIsEqualElementList(self.ServiceAttribut, other.ServiceAttribut, True)
                and VDV.vdvIsEqualElementList(self.FahrtBeziehung, other.FahrtBeziehung, True) )

    def addSollHalt(self, sollHalt):
        """ Fügt eine neue Haltestelle der Fahrt hinzu """
        self.__SollHalt.append(sollHalt)

    def addFahrtBezeichnerText(self, fahrtBezeichnerText):
        """ Fügt einen FahrtbezeichnerText hinzu """
        self.__FahrtBezeichnerText.append(fahrtBezeichnerText)

    def addHinweisText(self, hinweisText):
        """ Fügt einen Fahrtspezifischen Hinweis hinzu """
        self.__HinweisText.append(hinweisText)

    def addServiceAttribut(self, serviceAttribut):
        """ Fügt der Fahrt ein ServiceAttribut hinzu """
        self.__ServiceAttribut.append(serviceAttribut)

    def addFahrtBeziehung(self, fahrtBeziehung):
        """ Fügt eine FahrtBeziehung der SollFahrt hinzu """
        self.__FahrtBeziehung.append(fahrtBeziehung)

    def toXMLElement(self):
        """ Liefert eine SollFahrt als XML-Element """
        ownRoot = ET.Element('SollFahrt', {"Zst": self.Zst.strftime("%Y-%m-%dT%H:%M:%SZ")})
        fahrtID = ET.SubElement(ownRoot, 'FahrtID')
        if (self.FahrtBezeichner is not None): ET.SubElement(fahrtID, 'FahrtBezeichner').text = self.__FahrtBezeichner
        if (self.Betriebstag is not None): ET.SubElement(fahrtID, 'Betriebstag').text = self.__Betriebstag.strftime("%Y-%m-%d")
        for sollHalt in self.__SollHalt: ownRoot.append(sollHalt.toXMLElement())
        if (self.UmlaufID is not None): ET.SubElement(ownRoot, 'UmlaufID').text = self.UmlaufID
        if (self.KursNr is not None): ET.SubElement(ownRoot, 'KursNr').text = self.KursNr
        for fahrtBezeichnerText in self.__FahrtBezeichnerText: ET.SubElement(ownRoot, 'FahrtBezeichnerText').text = fahrtBezeichnerText
        if (self.VerkehrsmittelNummer is not None): ET.SubElement(ownRoot, 'VerkehrsmittelNummer').text = self.VerkehrsmittelNummer
        if (self.LinienText is not None): ET.SubElement(ownRoot, 'LinienText').text = self.LinienText
        if (self.ProduktID is not None): ET.SubElement(ownRoot, 'ProduktID').text = self.ProduktID
        if (self.RichtungsText is not None): ET.SubElement(ownRoot, 'RichtungsText').text = self.RichtungsText
        if (self.VonRichtungsText is not None): ET.SubElement(ownRoot, 'VonRichtungsText').text = self.VonRichtungsText
        for hinweisText in self.__HinweisText: ET.SubElement(ownRoot, 'HinweisText').text = hinweisText
        if (self.LinienfahrwegID is not None): ET.SubElement(ownRoot, 'LinienfahrwegID').text = self.LinienfahrwegID
        if (self.Zugname is not None): ET.SubElement(ownRoot, 'Zugname').text = self.Zugname
        if (self.FaelltAus is not None): ET.SubElement(ownRoot, 'FaelltAus').text = VDV.vdvToVDVBool(self.FaelltAus)
        if (self.FahrradMitnahme is not None): ET.SubElement(ownRoot, 'FahrradMitnahme').text = VDV.vdvToVDVBool(self.FahrradMitnahme)
        if (self.FahrzeugTypID is not None): ET.SubElement(ownRoot, 'FahrzeugTypID').text = self.FahrzeugTypID
        for serviceAttribut in self.__ServiceAttribut: ownRoot.append(serviceAttribut.toXMLElement())
        if (self.SollFormation is not None): ownRoot.append(self.SollFormation.toXMLElement())
        for fahrtBeziehung in self.__FahrtBeziehung: ownRoot.append(fahrtBeziehung.toXMLElement())
        return ownRoot

        

class Linienfahrplan():
    """    Beschreibt einen VDV-Linienfahrplan
    linienID - ID der Linie
    richtungsID - ID der Richtung (H,R)
    """
    def __init__(self, linienID, richtungsID):
        self.__LinienID = linienID
        self.__RichtungsID = richtungsID
        self.__SollFahrt = list()
        self.__ProduktID = None
        self.__BetreiberID = None
        self.__LinienText = None
        self.__RichtungsText = None
        self.__VonRichtungsText = None
        self.__VerkehrsmittelText = None
        self.__FahrradMitnahme = None
        self.__HinweisText = list()

    def __hash__(self):
        return hash((self.__LinienID, self.__RichtungsID, self.__BetreiberID))
    def __eq__(self, other):
        return isinstance(other, Linienfahrplan) and self.__LinienID == other.__LinienID and self.__RichtungsID == other.__RichtungsID and self.__BetreiberID == other.__BetreiberID

    @property
    def LinienID(self): return self.__LinienID
    @property
    def RichtungsID(self): return self.__RichtungsID
    @property
    def SollFahrt(self): return self.__SollFahrt
    @property
    def ProduktID(self): return self.__ProduktID
    @property
    def BetreiberID(self): return self.__BetreiberID
    @property
    def LinienText(self): return self.__LinienText
    @property
    def RichtungsText(self): return self.__RichtungsText
    @property
    def VonRichtungsText(self): return self.__VonRichtungsText
    @property
    def VerkehrsmittelText(self): return self.__VerkehrsmittelText
    @property
    def FahrradMitnahme(self): return self.__FahrradMitnahme
    @property
    def HinweisText(self): return self.__HinweisText

    @ProduktID.setter
    def ProduktID(self, v): self.__ProduktID = v
    @BetreiberID.setter
    def BetreiberID(self, v): self.__BetreiberID = v
    @LinienText.setter
    def LinienText(self, v): self.__LinienText = v
    @RichtungsText.setter
    def RichtungsText(self, v): self.__RichtungsText = v
    @VonRichtungsText.setter
    def VonRichtungsText(self, v): self.__VonRichtungsText = v
    @VerkehrsmittelText.setter
    def VerkehrsmittelText(self, v): self.__VerkehrsmittelText = v
    @FahrradMitnahme.setter
    def FahrradMitnahme(self, v): self.__FahrradMitnahme = v

    def isEqual(self, other):
        """ Vergleich von 2 Linienfahrplaenen """
        return ( isinstance(other, Linienfahrplan)
                and self.LinienID == other.LinienID
                and self.RichtungsID == other. RichtungsID
                and self.ProduktID == other.ProduktID
                and self.BetreiberID == other.BetreiberID
                and self.LinienText == other.LinienText
                and self.RichtungsText == other.RichtungsText
                and self.VonRichtungsText == other.VonRichtungsText
                and self.VerkehrsmittelText == other.VerkehrsmittelText
                and self.RichtungsText == other.RichtungsText
                and self.VonRichtungsText == other.VonRichtungsText
                and self.FahrradMitnahme == other.FahrradMitnahme
                #Elemente sind identisch => Prüfung der einzelnen Listen
                and VDV.vdvIsEqualElementList(self.SollFahrt, other.SollFahrt, True)
                and VDV.vdvIsEqualElementList(self.HinweisText, other.HinweisText, False))

    def addSollFahrt(self, sollFahrt): self.__SollFahrt.append(sollFahrt)
    def addHinweisText(self, hinweisText): self.__HinweisText.append(hinweisText)

    def toXMLElement(self):
        """ Liefert den LinienFahrplan als XML-Element """
        ownRoot = ET.Element('Linienfahrplan')
        if (self.LinienID is not None): ET.SubElement(ownRoot, 'LinienID').text = self.LinienID
        if (self.RichtungsID is not None): ET.SubElement(ownRoot, 'RichtungsID').text = self.RichtungsID
        for sollFahrt in self.__SollFahrt: ownRoot.append(sollFahrt.toXMLElement())
        if (self.ProduktID is not None): ET.SubElement(ownRoot, 'ProduktID').text = self.ProduktID
        if (self.BetreiberID is not None): ET.SubElement(ownRoot, 'BetreiberID').text = self.BetreiberID
        if (self.LinienText is not None): ET.SubElement(ownRoot, 'LinienText').text = self.LinienText
        if (self.RichtungsText is not None): ET.SubElement(ownRoot, 'RichtungsText').text = self.RichtungsText
        if (self.VonRichtungsText is not None): ET.SubElement(ownRoot, 'VonRichtungsText').text = self.VonRichtungsText
        if (self.VerkehrsmittelText is not None): ET.SubElement(ownRoot, 'VerkehrsmittelText').text = self.VerkehrsmittelText
        if (self.FahrradMitnahme is not None): ET.SubElement(ownRoot, 'FahrradMitnahme').text = VDV.vdvToVDVBool(self.FahrradMitnahme)
        for hinweisText in self.__HinweisText: ET.SubElement(ownRoot, 'HinweisText').text = hinweisText
        return ownRoot


class AUSNachricht():
    """
    Beschreibt eine AUSNachricht zu einer bestimmten AboID
    Momentan wird nur der Linienfahrplan in der AUSNachricht unterstützt
    """
    def __init__(self, aboID):
        self.__AboID = aboID
        self.__LinienFahrplan = list()

    @property
    def AboID(self): return self.__AboID

    def addLinienFahrplan(self, linienFahrplan): self.__LinienFahrplan.append(linienFahrplan)

    def toXMLElement(self):
        """ Liefert die AUSNachricht als XML-Element """
        ownRoot = ET.Element('AUSNachricht', {"AboID": self.AboID})
        for linienfahrplan in self.__LinienFahrplan: ownRoot.append(linienfahrplan.toXMLElement())
        return ownRoot



