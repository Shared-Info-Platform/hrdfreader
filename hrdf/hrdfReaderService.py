import sys
import os
import logging
import configparser
import zipfile
import requests
from hrdf.hrdfdb import HrdfDB
from hrdf.hrdfreader import HrdfReader
from hrdf.hrdflog import logger

class HrdfReaderService:
    """
    Die Klasse stellt die Funktionen für den HRDF-Import-Service zur Verfügung

    """
    def __init__(self, hrdfConfig):
        self.__hrdfConfig = hrdfConfig
        # self.__hrdfdb wird in initialise initialisiert

    def initialise(self):
        """ Initialisierung-Tasks für den Reader-Service
            Liefert True wenn erfolgreich initialisiert werden konnte ansonsten False
        """
        initOk = False
        # Aufbau der Datenbankverbindung
        dbname = self.__hrdfConfig['DATABASE']['dbname']
        host = self.__hrdfConfig['DATABASE']['host']
        user = self.__hrdfConfig['DATABASE']['user']
        pwd = self.__hrdfConfig['DATABASE']['pwd']
        self.__hrdfdb = HrdfDB(dbname, host, user, pwd)
        if self.__hrdfdb.connect():
            initOk = True

        return initOk

    def run(self):
        """ Startet den Import-Service """

        # Cleanup der zu löschenden Eckdaten (Feld: deletflag=true)
        self.cleanupHRDF()

        # download zipFile to folder
        newImportFile = self.checkForNewImportFile()
        if (newImportFile is not None):
            # Download war erfolgreich und das "newImportFile" wurde gespeichert
            if (self.verifyImportFile(newImportFile)):
                logger.info("Neuer HRDF-Import {} wird importiert".format(newImportFile))
                self.importHRDFZip(newImportFile)

    def checkForNewImportFile(self):
        """ Lädt die aktuelle HRDF-Import-Datei über den PermalLink und legt die Datei in das entsprechende Verzeichnis """
        newFile = None
        permalink = self.__hrdfConfig['HRDFImport']['permalink']
        downloadFolder = self.__hrdfConfig['HRDFImport']['downloadFolder']

        r = requests.get(permalink)
        if (r.status_code == requests.codes.ok):
            # Analyse der URL um den Dateinamen zu extrahieren
            fileName = os.path.basename(r.url)

            # Prüfen, ob momentan die gleiche Datei bereits importiert wird
            sql_eckdaten = "SELECT count(1) FROM HRDF.HRDF_ECKDATEN_TAB WHERE importfilename = %s and importstatus = %s"
            curEckdaten = self.__hrdfdb.connection.cursor()
            curEckdaten.execute(sql_eckdaten, (fileName, 'running'))
            eckdaten = curEckdaten.fetchall()
            curEckdaten.close()
            if (eckdaten[0][0] == 0):
                # Datei kann gespeichert werden
                tmpFile = "{}/{}".format(downloadFolder, fileName)
                try:
                    with open(tmpFile, "wb") as file:
                        file.write(r.content)
                        file.close()
                        newFile = tmpFile
                except Exception as e:
                    logger.error("Fehler beim Speichern der HRDF-Datei => {}".format(e))
            else:
                logger.info("HRDF-Datei <{}> wird gerade importiert importiert".format(fileName))
        else:
            logger.error("HTTP-Fehler beim Laden der HRDF-Zip-Datei {}".format(r.status_code))

        r.close()

        return newFile

    def verifyImportFile(self, importFile):
        """ Prüft die Angaben des HRDF-ImportFiles mit den bestehenden Importen in der Datenbank
            Ist ein entsprechender Import noch nicht vorhanden, dann liefert die Funktion True ansonsten False

            importFile -- Zu prüfende Import-Datei
        """
        importOk = False
        # Ermitteln der Angaben aus den ECKDATEN
        hrdfzip = zipfile.ZipFile(importFile, 'r')
        lines = hrdfzip.read('ECKDATEN').decode('utf-8').split('\r\n')[:-1]
        # In der dritten Zeile befindet sich die Beschreibung, die den Import eindeutig macht
        uniqueImportDescription = lines[2]
        hrdfzip.close()

        # Vergleich der Eckdaten mit den Angaben in der Datenbank
        sql_eckdaten = "SELECT count(1) FROM HRDF.HRDF_ECKDATEN_TAB WHERE descriptionhrdf = %s"
        curEckdaten = self.__hrdfdb.connection.cursor()
        curEckdaten.execute(sql_eckdaten, (uniqueImportDescription,))
        eckdaten = curEckdaten.fetchall()
        curEckdaten.close()
        if (eckdaten[0][0] == 0):
            importOk = True
        else:
            logger.info("HRDF-Import <{}> ist bereits importiert".format(lines[2]))

        return importOk

    def importHRDFZip(self, importFile):
        """ Importiert die angegebene HRDF-Datei.
            Die Datei sollte über verifyImportFile bereits für den Import verifiziert sein.
            Es werden entsprechende "Locks" vor dem Import gesetzt und anschließend wieder aufgehoben.

            importFile -- Zu importierende HRDF-Datei
        """
        # ZipFile öffnen und zu lesende Dateien bestimmen
        hrdfzip = zipfile.ZipFile(importFile, 'r')
        hrdffiles = ['ECKDATEN','BITFELD','RICHTUNG','BAHNHOF','GLEIS','ZUGART','ATTRIBUT','INFOTEXT','DURCHBI','BFKOORD_WGS','UMSTEIGB','BFPRIOS','METABHF','FPLAN']

        # Initialisierung des HRDF-Readers und lesen der gewünschten HRDF-Dateien
        reader = HrdfReader(hrdfzip, self.__hrdfdb, hrdffiles)
        reader.readfiles()
        hrdfzip.close()

    def cleanupHRDF(self):
        """ Aufräumen der HRDF-Daten """
        logger.info('Zu löschende EckdatenIDs werden gesucht.')
        sql_eckdatenIds = "SELECT id, descriptionhrdf FROM HRDF.HRDF_Eckdaten_TAB WHERE deleteFlag = true;"
        curEckdaten = self.__hrdfdb.connection.cursor()
        curEckdaten.execute(sql_eckdatenIds)
        eckdatenListe = curEckdaten.fetchall()
        curEckdaten.close()

        # Alle Tabellen die in Abhängigkeit der EckdatenId stehen
        cleanup_tables = ["hrdf.hrdf_attribut_tab",
                          "hrdf.hrdf_bahnhof_tab",
                          "hrdf.hrdf_bfkoord_tab",
                          "hrdf.hrdf_bfprios_tab",
                          "hrdf.hrdf_bitfeld_tab",
                          "hrdf.hrdf_durchbi_tab",
                          "hrdf.hrdf_fplanfahrt_tab",
                          "hrdf.hrdf_fplanfahrta_tab",
                          "hrdf.hrdf_fplanfahrtc_tab",
                          "hrdf.hrdf_fplanfahrtg_tab",
                          "hrdf.hrdf_fplanfahrtgr_tab",
                          "hrdf.hrdf_fplanfahrti_tab",
                          "hrdf.hrdf_fplanfahrtl_tab",
                          "hrdf.hrdf_fplanfahrtlaufweg_tab",
                          "hrdf.hrdf_fplanfahrtr_tab",
                          "hrdf.hrdf_fplanfahrtsh_tab",
                          "hrdf.hrdf_fplanfahrtve_tab",
                          "hrdf.hrdf_gleis_tab",
                          "hrdf.hrdf_infotext_tab",
                          "hrdf.hrdf_metabhf_tab",
                          "hrdf.hrdf_metabhfgruppe_tab",
                          "hrdf.hrdf_richtung_tab",
                          "hrdf.hrdf_umsteigb_tab",
                          "hrdf.hrdf_zugart_tab",
                          "hrdf.hrdf_zugartkategorie_tab",
                          "hrdf.hrdf_zugartklasse_tab",
                          "hrdf.hrdf_zugartoption_tab",
                          "hrdf.hrdf_tripcount_operator_tab",
                          "hrdf.hrdf_linesperstop_tab",
                          "hrdf.hrdf_dailytimetable_tab"]

        # Für alle zu löschenden EckdatenIds
        curDelEckdaten = self.__hrdfdb.connection.cursor()
        for eckdaten in eckdatenListe:
            logger.info("Entferne HRDF-Daten für EckdatenId {} => {}".format(eckdaten[0], eckdaten[1]))
            curDelEckdaten.execute("DELETE FROM HRDF.HRDF_ECKDATEN_TAB WHERE id = %s", (eckdaten[0],))
            for table in cleanup_tables:
                try:
                    sql_delEckdaten = "DELETE FROM {} WHERE fk_eckdatenid = {}".format(table, eckdaten[0])
                    curDelEckdaten.execute(sql_delEckdaten)
                    logger.info("EckdatenId {}: In Tabelle {} wurden {} Datensätze gelöscht".format(eckdaten[0], table, curDelEckdaten.rowcount))
                except Exception as e:
                    logger.error("EckdatenId {}: Fehler beim Löschen der Daten in Tabelle {} => {}".format(eckdaten[0], table, e))

            self.__hrdfdb.connection.commit()

        curDelEckdaten.close()
