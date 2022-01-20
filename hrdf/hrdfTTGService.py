import sys
import os
import logging
import configparser
from datetime import datetime, date, timedelta
from hrdf.hrdfdb import HrdfDB
from hrdf.hrdfTTG import HrdfTTG
from hrdf.hrdflog import logger

class HrdfTTGService:
    """
    Die Klasse stellt die Funktionen für den HRDF-TTG-Service zur Verfügung

    """
    def __init__(self, hrdfConfig):
        self.__hrdfConfig = hrdfConfig
        # self.__hrdfdb wird in initialise initialisiert
        # self.__ttGenerator wird in initialise initialisiert

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
            self.__ttGenerator = HrdfTTG(self.__hrdfdb)
            initOk = True

        return initOk

    def run(self):
        """ Startet den TTG-Service """

        # Sicherstellen, dass der Generierungs-Service nur einmal gestartet wird
        if ( self.lockGeneration()):
            try:
                previewDays = int(self.__hrdfConfig['HRDFGeneration']['previewDays'])

                # Bereinigung der alten, und in der Zukunft "falschen" zu löschenden Tagesfahrpläne
                self.cleanupDailyTimetable(previewDays)

                # Welches sind die aktuellsten Eckdaten auf denen der Fahrplan für die nächsten Tage generiert werden soll                
                generationList = self.buildGenerationList(previewDays)

                # Generierung des Tagesfahrplans für die ermittelten Tage
                if (len(generationList) == 0):
                    logger.info("Der Tagesfahrplan für die nächsten {} Tage ist vollständig".format(previewDays))
                else:
                    for generationIssue in generationList:
                        try:
                            dtGenerateFrom = generationIssue["generationFrom"]
                            dtGenerateTo = generationIssue["generationTo"]
                            eckdatenId = str(generationIssue["eckdatenId"])
                            logger.info("Generierung des Tagesfahrplan für den Zeitraum von {:%d.%m.%Y} bis {:%d.%m.%Y} ({}):".format(dtGenerateFrom, dtGenerateTo, eckdatenId))
                            if ( self.__ttGenerator.setup(eckdatenId, dtGenerateFrom, dtGenerateTo) ):
                                iErrorCnt = self.__ttGenerator.generateTT()
                                if ( iErrorCnt == 0):
                                    logger.info("Der Tagesfahrplan für den Zeitraum von {:%d.%m.%Y} bis {:%d.%m.%Y} wurde erfolgreich generiert".format(dtGenerateFrom, dtGenerateTo))
                                else:
                                    logger.warning("Der Tagesfahrplan für den Zeitraum von {:%d.%m.%Y} bis {:%d.%m.%Y} konnte nicht vollständig generiert werden. {} fehlerhafte Fahrten".format(dtGenerateFrom, dtGenerateTo, iErrorCnt))
                            else:
                                logger.error("Der Tagesfahrplan-Generator konnte nicht initialisiert werden")
                        except Exception as e:
                            logger.error("Fehler beim Generieren des Tagesfahrplans für die Zeit vom {:%d.%m.%Y} bis {:%d.%m.%Y} (EckdatenId={}) => {}".format(dtGenerateFrom, dtGenerateTo, eckdatenId, e))
            except Exception as e:
                logger.error("Fehler beim Generieren des Tagesfahrplans => {}".format(e))

            # Entriegeln der Tagsfahrplangenerierung
            self.unlockGeneration()
        else:
            # Generierung kann nicht verriegelt werden
            logger.warning("Der Service zur Tagsfahrplangenerierung kann nicht verriegelt werden")

    def lockGeneration(self):
        """ Verriegelt die Tagesfahrplangenerierung, so dass dieser Service nur einmal gestartet werden kann"""
        locked = False
        if (os.path.exists("generationLock")):
            logger.warning("Der Service zur Tagesfahrplangenerierung läuft bereits")
        else:
            fp = open('generationLock', 'x')
            fp.close()
            locked = True
        return locked

    def unlockGeneration(self):
        """ Entriegelt die Tagesfahrplangenerierung, so dass dieser Service wieder gestartet werden kann """
        if (os.path.exists("generationLock")):
            os.remove("generationLock")

    def buildGenerationList(self, previewDays):
        """ Erstellt eine Liste mit den zu generierenden Tagen und der dazugehörigen EckdatenId

            previewDays -- Anzahl der nächsten zu generierenden Tage
        """

        i = 0
        startingDate = datetime.now().date()
        curSelEckdaten = self.__hrdfdb.connection.cursor()
        generationList = list()
        lastEckdatenId = -1
        while i <= previewDays:
            # Für jeden Tag der generiert werden soll wird die korrekte Eckdaten-Version ermittelt
            currentDate = startingDate + timedelta(days=i)
            sql_SelEckdaten = "SELECT id, ttgenerated FROM HRDF.HRDF_Eckdaten_TAB "\
                               " WHERE '{}' BETWEEN validfrom AND validto "\
                               "   AND importstatus = 'ok' "\
                               "   AND coalesce(deleteflag, false) = false "\
                               "   AND coalesce(inactive, false) = false "\
                               " ORDER BY creationdatetime desc limit 1".format(currentDate, currentDate, currentDate)
            curSelEckdaten.execute(sql_SelEckdaten)
            eckdaten = curSelEckdaten.fetchall()            
            if (len(eckdaten) == 0):
                # Für diesen Tag wurden keine Eckdaten gefunden. Es entsteht eine Lücke => Es muss dafür gesorgt werden dass ein neues GenerationIssue angelegt wird
                lastEckdatenId = -1
            else:
                # Es existieren gültige Eckdaten für diesen Tag.
                # Ist dieser Tag bereits generiert?
                if ( (eckdaten[0][1] is not None) and (currentDate in eckdaten[0][1] )):
                    # Tag ist bereits generiert => Es entsteht eine Lücke => Es muss dafür gesorgt werden dass ein neues GenerationIssue angelegt wird
                    lastEckdatenId = -1
                else:
                    if (lastEckdatenId != eckdaten[0][0]):
                        generationIssue = dict()
                        generationIssue["eckdatenId"] = eckdaten[0][0]
                        generationIssue["generationFrom"] = currentDate
                        generationIssue["generationTo"] = currentDate
                        generationList.append(generationIssue)
                        lastEckdatenId = eckdaten[0][0]
                    else:
                        generationList[-1]["generationTo"] = currentDate
            i += 1
        curSelEckdaten.close()
        return generationList


    def cleanupDailyTimetable(self, previewDays):
        """ Aufräumen der alten Tagesfahrplandaten
            Es werden folgende Tagesfahrpläne gelöscht:
            - alle Tagesfahrpläne, die älter als die konfigurierten Tage (deleteAfterDays) sind
            - alle Tagesfahrpläne in der Zukunft, die zu Eckdaten gehören, die nicht mehr relevant sind

            previewDays -- Anzahl der nächsten zu generierenden Tage
        """
        deleteAfterDays = self.__hrdfConfig['HRDFGeneration']['deleteAfterDays']
        logger.info('Ermitteln und Löschen der Tagesfahrplandaten, die älter als {} Tage sind'.format(deleteAfterDays))
        
        sql_SelOperatingDay = "SELECT DISTINCT fk_eckdatenid, operatingday FROM HRDF.HRDF_DailyTimeTable_TAB WHERE operatingday < current_date - {}".format(deleteAfterDays)
        curSelOperatingDay = self.__hrdfdb.connection.cursor()
        curSelOperatingDay.execute(sql_SelOperatingDay)
        operatingDays = curSelOperatingDay.fetchall()
        curSelOperatingDay.close()
        
        # Jeden zu löschenden Betriebstag einzelnd löschen
        if (len(operatingDays) == 0):
            logger.info("Es sind keine Tagesfahrpläne zu löschen")
        else:
            for operatingDay in operatingDays:
                try:
                    self.__ttGenerator.deleteDailyTimetable(operatingDay[0], operatingDay[1]);
                except Exception as e:
                    logger.info("Betriebstag {:%d.%m.%Y}-{} => Fehler beim Löschen des Tagesfahrplans => {}".format(operatingDay[1], operatingDay[0], e))


        logger.info('Ermitteln und Löschen der Tagesfahrplandaten, die bereits in der Zukunft über nicht mehr relevante Eckdaten generiert wurden')
        startingDate = datetime.now().date()
        curSelFutureTT = self.__hrdfdb.connection.cursor()
        i = 0
        while i <= previewDays:
            # Für jeden Tag, der ab heute generiert werden soll werden alle Eckdaten durchsucht, die nicht für den heutigen Tag zuständig/valide sind
            currentDate = startingDate + timedelta(days=i)
            # Folgendes, geklammertes SQL-Statement entspricht dem Statement aus buildGenerationList()
            sql_SelEckdaten =  "SELECT id FROM HRDF.HRDF_Eckdaten_TAB "\
                               " WHERE id NOT IN "\
                               "(SELECT id FROM HRDF.HRDF_Eckdaten_TAB "\
                               " WHERE '{}' BETWEEN validfrom AND validto "\
                               "   AND importstatus = 'ok' "\
                               "   AND coalesce(deleteflag, false) = false "\
                               "   AND coalesce(inactive, false) = false "\
                               " ORDER BY creationdatetime desc limit 1)".format(currentDate, currentDate, currentDate)
            curSelFutureTT.execute(sql_SelEckdaten)
            futureTTs = curSelFutureTT.fetchall()
            # Jeden zu löschenden Betriebstag einzelnd löschen
            if (len(futureTTs) == 0):
                logger.info("Es sind keine Tagesfahrpläne in der Zukunft zu löschen")
            else:
                for futureTT in futureTTs:
                    try:
                        self.__ttGenerator.deleteDailyTimetable(futureTT[0], currentDate);
                    except Exception as e:
                        logger.info("Betriebstag {:%d.%m.%Y}-{} => Fehler beim Löschen des Tagesfahrplans => {}".format(currentDate, futureTT[0], e))
            i += 1
        curSelFutureTT.close()