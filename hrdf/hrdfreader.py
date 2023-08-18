import os
import re
import psycopg2
import zipfile
import fileinput
from datetime import datetime, date, timedelta
from io import StringIO
from bitstring import Bits
from hrdf.hrdflog import logger



class HrdfReader:
	"""
	Die Klasse liest die HRDF-Dateien und schreibt diese in die Datenbank

	HrdfReader(hrdfzipfile, db, hrdffiles)

	"""
	modulVersion = "2.1.1"
	hrdfFormats = ["5.40.41"]
	def __init__(self, hrdfzipfile, db, hrdffiles, charset='utf-8'):
		"""
		hrdfzipfile	- HRDF-ZipFile
		db - HRDF-DB
		hrdffiles - Liste der zu lesenden HRDF-Files
		charset - Charset der gezippten Dateien
		"""
		self.__hrdfzip = hrdfzipfile
		self.__hrdfdb = db
		self.__hrdffiles = hrdffiles
		self.__charset = charset
		self.__fkdict = dict(fk_eckdatenid="-1", fk_fplanfahrtid="-1")
		self.__eckdaten_validFrom = date.today()
		self.__eckdaten_validTo = date.today()

		# private Klassenvariablen, da über Funktion die Daten einer Fahrt gespeichert werden
		self.__fplanFahrtG_strIO = StringIO()
		self.__fplanFahrtAVE_strIO = StringIO()
		self.__fplanFahrtLauf_strIO = StringIO()
		self.__fplanFahrtA_strIO = StringIO()
		self.__fplanFahrtR_strIO = StringIO()
		self.__fplanFahrtI_strIO = StringIO()
		self.__fplanFahrtL_strIO = StringIO()
		self.__fplanFahrtSH_strIO = StringIO()
		self.__fplanFahrtC_strIO = StringIO()
		self.__fplanFahrtGR_strIO = StringIO()
		
		#Workaround um Zugehörigkeit einer AVE-Zeile prüfen zu können (gibt es auch bei Kurswagen)
		self.__AVE_type = "None"


	def readfiles(self):
		"""Liest die gewünschten HRDF-Dateien und schreibt sie in die Datenbank"""
		readFilesOk = False

		try:
			for filename in self.__hrdffiles:
				if filename == "ECKDATEN":
					self.read_eckdaten(filename)
				elif filename == "BITFELD":
					self.read_bitfeld(filename)
				elif filename == "RICHTUNG":
					self.read_richtung(filename)
				elif filename == "ZUGART":
					self.read_zugart(filename)
				elif filename == "LINIE":
					self.read_linie(filename)
				elif filename == "ATTRIBUT":
					self.read_attribut(filename, "DE")
					self.read_attribut(filename, "EN")
					self.read_attribut(filename, "FR")
					self.read_attribut(filename, "IT")
				elif filename == "INFOTEXT":
					self.read_infotext(filename, "DE")
					self.read_infotext(filename, "EN")
					self.read_infotext(filename, "FR")
					self.read_infotext(filename, "IT")
				elif filename == "FPLAN":
					self.read_fplan(filename)
				elif filename == "BAHNHOF":
					self.read_bahnhof(filename)
				elif filename == "GLEIS":
					self.read_gleis(filename)
				elif filename == "DURCHBI":
					self.read_durchbi(filename)
				elif filename == "BFKOORD_WGS":
					self.read_bfkoordgeo(filename)
				elif filename == "UMSTEIGB":
					self.read_umsteigb(filename)
				elif filename == "BFPRIOS":
					self.read_bfprios(filename)
				elif filename == "METABHF":
					self.read_metabhf(filename)
				else:
					logger.error("Das Lesen der Datei ["+filename+"] wird nicht unterstützt")

			# Aufbereitung und Verdichtung der importierten Daten
			self.determine_linesperstop(self.__fkdict['fk_eckdatenid'])
			self.determine_tripcount(self.__fkdict['fk_eckdatenid'])

			readFilesOk = True
			logger.info("Der HRDF-Import <{}> wurde eingearbeitet".format(self.__hrdfzip.filename))

		except Exception as e:
			logger.info("Der HRDF-Import wurde <{}> wegen Fehler abgebrochen {}".format(self.__hrdfzip.filename), e)

		# Setzen des Import-Status in der Eckdaten-Tabelle
		cur = self.__hrdfdb.connection.cursor()
		sql_string = "UPDATE HRDF.HRDF_ECKDATEN_TAB SET importstatus = %s WHERE id = %s"
		if readFilesOk:
			importStatus = "ok"
		else:
			importStatus = "error"
		cur.execute(sql_string, (importStatus, self.__fkdict["fk_eckdatenid"]))
		self.__hrdfdb.connection.commit()
		cur.close()
		
		
	def read_eckdaten(self, filename):
		"""Lesen der Datei ECKDATEN"""
		logger.info('lesen und verarbeiten der Datei ECKDATEN')
		lines = self.__hrdfzip.read(filename).decode(self.__charset).split('\r\n')[:-1]
 		# spezifisch für SBB-Version sind die Trenner in der Bezeichnung, die hier in separate Felder geschrieben werden
		bezeichnung,exportdatum,hrdfversion,lieferant = lines[2].split('$')
		cur = self.__hrdfdb.connection.cursor()
		try: # Absichern des DB-Cursor
			sql_string = "INSERT INTO HRDF_ECKDATEN_TAB (importFileName, importDateTime, validFrom, validTo, descriptionhrdf, description, creationdatetime, hrdfversion, exportsystem) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id;" 
			importFileName = os.path.basename(self.__hrdfzip.filename)
			importDateTime = str(datetime.now())
			validFrom = str(datetime.strptime(lines[0], '%d.%m.%Y').date())
			validTo = str(datetime.strptime(lines[1], '%d.%m.%Y').date())
			exportdatum = str(datetime.strptime(exportdatum, '%d.%m.%Y %H:%M:%S'))
			cur.execute(sql_string, (importFileName, importDateTime, validFrom, validTo, lines[2], bezeichnung, exportdatum, hrdfversion, lieferant))
			self.__fkdict["fk_eckdatenid"] = str(cur.fetchone()[0])
			self.__hrdfdb.connection.commit()
			self.__eckdaten_validFrom = datetime.strptime(lines[0], '%d.%m.%Y').date()
			self.__eckdaten_validTo = datetime.strptime(lines[1], '%d.%m.%Y').date()
		except Exception as e:
			logger.error('Fehler beim Lesen und Verarbeiten der Datei ECKDATEN aufgetreten {}'.format(e))
		cur.close()

	def determine_linesperstop(self, fk_eckdatenid):
		"""Ermitteln und Schreiben der Linien, die in der aktuellen Fahrplanperiode an einem Halt vorkommen"""
		logger.info('ermitteln der Linien pro Halt')
		#"INSERT INTO HRDF.HRDF_LINESPERSTOP_TAB (fk_eckdatenid, stopno, operationalno, lineno, categorycode) "\
		sql_stopsLookup = "(SELECT DISTINCT fahrt.fk_eckdatenid, flw.stopno, fahrt.operationalno, line.lineno, cat.categorycode "\
					"FROM hrdf.hrdf_fplanfahrtlaufweg_tab flw "\
					"INNER JOIN hrdf.hrdf_fplanfahrt_tab fahrt on flw.fk_fplanfahrtid = fahrt.id and flw.fk_eckdatenid = fahrt.fk_eckdatenid "\
					"INNER JOIN hrdf.hrdf_fplanfahrtg_tab cat on cat.fk_fplanfahrtid = fahrt.id and cat.fk_eckdatenid = fahrt.fk_eckdatenid "\
					"LEFT OUTER JOIN hrdf.hrdf_fplanfahrtl_tab line on line.fk_fplanfahrtid = fahrt.id and line.fk_eckdatenid = fahrt.fk_eckdatenid "\
					"WHERE fahrt.fk_eckdatenid = %s)"

		curLookup = self.__hrdfdb.connection.cursor()
		try: # Absichern des DB-Cursor
			curLookup.execute(sql_stopsLookup, (fk_eckdatenid,))
			allLinesPerStop = curLookup.fetchall()
			curLookup.close()
			# Aufbereiten des Ergebnis, um es per COPY in die Tabelle zu schreiben. COPY erzeugt keinen Exclusive-Lock
			linesPerStop_strIO = StringIO()
			for linePerStop in allLinesPerStop:
				lineNo = linePerStop[3]
				if ( lineNo is None): lineNo = ''

				linesPerStop_strIO.write(str(linePerStop[0])+';'
							+str(linePerStop[1])+';'
							+linePerStop[2]+';'
							+lineNo+';'
							+linePerStop[4]
							+'\n')
			allLinesPerStop.clear()
			linesPerStop_strIO.seek(0)
			cur = self.__hrdfdb.connection.cursor()
			try: # Absichern des DB-Cursor
				cur.copy_expert("COPY HRDF.HRDF_LINESPERSTOP_TAB (fk_eckdatenid, stopno, operationalno, lineno, categorycode) FROM STDIN USING DELIMITERS ';' NULL AS ''",linesPerStop_strIO)
				self.__hrdfdb.connection.commit()
				logger.debug('LinesPerStop: {} eingefügte Datensätze'.format(curLookup.rowcount))
			except Exception as e:
				logger.error('Fehler beim Ermitteln der Linien pro Halt aufgetreten {}'.format(e))
			cur.close()						
		except Exception as e:
			logger.error('Fehler beim Ermitteln der Linien pro Halt aufgetreten {}'.format(e))
			curLookup.close()

	def determine_tripcount(self, fk_eckdatenid):
		"""Ermitteln und Schreiben der Anzahl Fahrten (Linien/Kategorie) pro Verwaltungsnummer - Taktdefinitionen mit eingeschlossen"""
		logger.info('ermitteln der Anzahl Fahrten (Linien/Kategorie) pro Verwaltung')

		sql_tripsLookup = "INSERT INTO HRDF.HRDF_TripCount_Operator_TAB (fk_eckdatenid, operationalno, lineno, categorycode, tripcount) "\
					"(SELECT fahrt.fk_eckdatenid, fahrt.operationalno, line.lineno, cat.categorycode, sum(coalesce(array_length(bit.bitfieldarray, 1), eckdaten.maxdays)*coalesce(cyclecount+1,1)) "\
					"   FROM hrdf.hrdf_fplanfahrt_tab fahrt "\
					"        inner join (SELECT id, validto + 1 - validfrom as maxdays FROM hrdf.hrdf_eckdaten_tab) eckdaten on fahrt.fk_eckdatenid = eckdaten.id "\
					"        LEFT OUTER JOIN hrdf.hrdf_fplanfahrtve_tab ve on fahrt.fk_eckdatenid = ve.fk_eckdatenid and fahrt.id = ve.fk_fplanfahrtid "\
					"        LEFT OUTER JOIN hrdf.hrdf_bitfeld_tab bit on ve.bitfieldno = bit.bitfieldno and ve.fk_eckdatenid = bit.fk_eckdatenid "\
					"        LEFT OUTER JOIN hrdf.hrdf_fplanfahrtl_tab line on line.fk_fplanfahrtid = fahrt.id and line.fk_eckdatenid = fahrt.fk_eckdatenid "\
					"        LEFT OUTER JOIN hrdf.hrdf_fplanfahrtg_tab cat on cat.fk_fplanfahrtid = fahrt.id and cat.fk_eckdatenid = fahrt.fk_eckdatenid "\
					"  WHERE fahrt.fk_eckdatenid = %s "\
					"  GROUP BY fahrt.fk_eckdatenid, fahrt.operationalno, line.lineno, cat.categorycode)"

		curLookup = self.__hrdfdb.connection.cursor()
		try: # Absichern des DB-Cursor
			curLookup.execute(sql_tripsLookup, (fk_eckdatenid,))
			self.__hrdfdb.connection.commit()
			logger.debug('TripCountPerOperator: {} eingefügte Datensätze'.format(curLookup.rowcount))
		except Exception as e:
			logger.error('Fehler beim Ermitteln der Anzahl Fahrten (Linien/Kategorie) pro Verwaltung aufgetreten {}'.format(e))
		curLookup.close()

	def read_bitfeld(self, filename):
		"""Lesen der Datei BITFELD"""
		logger.info('lesen und verarbeiten der Datei BITFELD')
		bitfeld_strIO = StringIO()
		for line in fileinput.input(filename, openhook=self.__hrdfzip.open):
			line = line.decode(self.__charset).replace('\r\n','')
			bitfield = str(Bits(hex=line[7:]).bin)[2:-2]
			daycnt = (self.__eckdaten_validTo - self.__eckdaten_validFrom).days
			# Aufbauen des Datums-Array auf Grund der gesetzen Bits
			validDays = []
			i = 0
			while i <= daycnt:
				if bitfield[i] == "1":
					validDays.append(str(self.__eckdaten_validFrom + timedelta(days=i)))
				i += 1

			if len(validDays) == 0:
				validDaysString = "{}"
			else:
				validDaysString = "{'" + "','".join(map(str,validDays)) + "'}"

			bitfeld_strIO.write(self.__fkdict['fk_eckdatenid']+';'
										+line[:6]+';'
										+line[7:]+';'
										+bitfield+';'
										+validDaysString
										+'\n')
		bitfeld_strIO.seek(0)
		cur = self.__hrdfdb.connection.cursor()
		try: # Absichern des DB-Cursor
			cur.copy_expert("COPY HRDF_BITFELD_TAB (fk_eckdatenid,bitfieldno,bitfield,bitfieldextend,bitfieldarray) FROM STDIN USING DELIMITERS ';' NULL AS ''",bitfeld_strIO)
			self.__hrdfdb.connection.commit()
			logger.debug('BitField: {} eingefügte Datensätze'.format(cur.rowcount))
		except Exception as e:
			logger.error('Fehler beim Lesen und Verarbeiten der Datei BITFELD aufgetreten {}'.format(e))
		cur.close()
		bitfeld_strIO.close()

	def read_bahnhof(self, filename):
		"""Lesen der Datei BAHNHOF"""
		logger.info('lesen und verarbeiten der Datei BAHNHOF')
		bahnhof_strIO = StringIO()
		for line in fileinput.input(filename, openhook=self.__hrdfzip.open):
			line = line.decode(self.__charset).replace('\r\n', '')
			stopname = ''
			stopnamelong = ''
			stopnameshort = ''
			stopnamealias = ''
			# Die Analyse betrachtet noch keine Sprachangaben
			for tmpName in re.split(">", line[12:62].strip()):
				pos = tmpName.find("<");
				typeinfo = tmpName[pos:]
				name = tmpName[:pos].replace("$", "")
				for c in typeinfo[1:]:
					if c == "1": stopname = name[:30]
					if c == "2": stopnamelong = name[:50]
					if c == "3": stopnameshort = name
					if c == "4": stopnamealias = name

			bahnhof_strIO.write(self.__fkdict['fk_eckdatenid']+';'
										 +line[:7].strip()+';'
										 +line[8:11].strip()+';'
										 +stopname+';'
										 +stopnamelong+';'
										 +stopnameshort+';'
										 +stopnamealias
										+'\n')
		bahnhof_strIO.seek(0)
		cur = self.__hrdfdb.connection.cursor()
		try: # Absichern des DB-Cursor
			cur.copy_expert("COPY HRDF_BAHNHOF_TAB (fk_eckdatenid,stopno,transportUnion,stopname,stopnamelong,stopnameshort,stopnamealias) FROM STDIN USING DELIMITERS ';' NULL AS ''", bahnhof_strIO)
			self.__hrdfdb.connection.commit()
			logger.debug('Bahnhof: {} eingefügte Datensätze'.format(cur.rowcount))
		except Exception as e:
			logger.error('Fehler beim Lesen und Verarbeiten der Datei BAHNHOF aufgetreten {}'.format(e))
		cur.close()
		bahnhof_strIO.close()

	def read_gleis(self, filename):
		"""Lesen der Datei GLEIS"""
		logger.info('lesen und verarbeiten der Datei GLEIS')
		# Lesen der kompletten Datei, um Index-Tabelle mit Gleis-Bezeichnungen aufzubauen.
		gleisTexte = dict();
		gleisInfoList = list();
		for line in fileinput.input(filename, openhook=self.__hrdfzip.open):
			line = line.decode(self.__charset).replace('\r\n', '')
			if (line[8] == "#"):
				# Es handelt sich um das Zeilenformat "Definition der Gleistexte"
				gleisTextKey = line[:7]+'-'+line[8:16];
				text = line[17:].strip()
				# extrahieren der einzelnen Gleistext-Komponenten
				result = re.findall("G '([\w\/-]+)'( A '([\w\/-]+)')?( T '(.+)')?", text)
				if (len(result) == 0):
					logger.warning("Gleisbezeichnung konnte nicht ermittelt werden <{}>".format(text))
				else:
					gleisTexte[gleisTextKey] = "{}{}{}".format(result[0][0], result[0][4], result[0][2])
			else:
				# Es handelt sich um das Zeilenformat "Zuordnung der Gleistexte"
				stopno = line[:7].strip();
				tripno = line[8:14].strip();
				operationalno = line[15:21].strip()				
				indexText = line[22:30].strip()
				stoppointtime = line[31:35].strip()
				bitfieldno = line[36:42].strip()
				gleisTextKey = stopno+'-'+indexText
				gleisInfoList.append(tuple((gleisTextKey, stopno, tripno, operationalno, stoppointtime, bitfieldno)))

		gleis_strIO = StringIO()
		for gleisInfo in gleisInfoList:
			stoppointtext = ""
			try:
				stoppointtext = gleisTexte[gleisInfo[0]]
				gleis_strIO.write(self.__fkdict['fk_eckdatenid']+';'
								+gleisInfo[1]+';'
								+gleisInfo[2]+';'
								+gleisInfo[3]+';'
								+stoppointtext+';'
								+gleisInfo[4]+';'
								+gleisInfo[5]+'\n')
			except:
				logger.warning("Gleisbezeichnung wurde nicht eingetragen für {}".format(gleisInfo))


		gleis_strIO.seek(0)
		cur = self.__hrdfdb.connection.cursor()
		try: # Absichern des DB-Cursor
			cur.copy_expert("COPY HRDF_GLEIS_TAB (fk_eckdatenid,stopno,tripno,operationalno,stoppointtext,stoppointtime,bitfieldno) FROM STDIN USING DELIMITERS ';' NULL AS ''", gleis_strIO)
			self.__hrdfdb.connection.commit()
			logger.debug('Gleis: {} eingefügte Datensätze'.format(cur.rowcount))
		except Exception as e:
			logger.error('Fehler beim Lesen und Verarbeiten der Datei GLEIS aufgetreten {}'.format(e))
		cur.close()
		gleis_strIO.close()

	def read_richtung(self, filename):
		"""Lesen der Datei RICHTUNG"""
		logger.info('lesen und verarbeiten der Datei RICHTUNG')
		richtung_strIO = StringIO()
		for line in fileinput.input(filename, openhook=self.__hrdfzip.open):
			line = line.decode(self.__charset).replace('\r\n', '')
			richtung_strIO.write(self.__fkdict['fk_eckdatenid']+';'
										 +line[:7].strip()+';'
										 +line[8:59].strip()
										+'\n')
		richtung_strIO.seek(0)
		cur = self.__hrdfdb.connection.cursor()
		try:
			cur.copy_expert("COPY HRDF_RICHTUNG_TAB (fk_eckdatenid,directioncode, directiontext) FROM STDIN USING DELIMITERS ';' NULL AS ''", richtung_strIO)
			self.__hrdfdb.connection.commit()
			logger.debug('Richtung: {} eingefügte Datensätze'.format(cur.rowcount))
		except Exception as e:
			logger.error('Fehler beim Lesen und Verarbeiten der Datei RICHTUNG aufgetreten {}'.format(e))
		cur.close()
		richtung_strIO.close()


	def read_zugart(self, filename):
		"""Lesen der Datei ZUGART"""
		logger.info('lesen und verarbeiten der Datei ZUGART')
		zugart_strIO = StringIO()
		zugartcategory_strIO = StringIO()
		zugartclass_strIO = StringIO()
		zugartoption_strIO = StringIO()

		languagecode = "--"
		bTextblock = False
		for line in fileinput.input(filename, openhook=self.__hrdfzip.open):
			line = line.decode(self.__charset).replace('\r\n', '')
			# Eine Zeile mit dem Inhalt "<text>" gibt an, dass nun nur noch die Textangaben in verschiedenen Sprachen folgen
			if not bTextblock:
				# solange das nicht der Fall ist, sollen die Daten als Zugarten weiter eingearbeitet werden
				if line != '<text>':
					# Der string setzt sich aus folgenden Elementen zusammen: code,produktklasse,tarifgruppe,ausgabesteuerung,gattungsbezeichnung,zuschlag,flag,gattungsbildernamen,kategorienummer
					zugart_strIO.write(self.__fkdict['fk_eckdatenid']+';'
											+line[:3].strip()+';'
											+line[4:6].strip()+';'
											+line[7:8]+';'
											+line[9:10]+';'
											+line[11:19].strip()+';'
											+line[20:21].strip()+';'
											+line[22:23]+';'
											+line[24:28].strip()+';'
											+line[30:33]+
											'\n')
				# sobald die Textangaben beginnen, werden die Daten sprachspezifisch in das jeweilige dictionary geschrieben
				else:
					bTextblock = True
			elif line[0] == '<':
				languagecode = line[1:3].lower()
			elif line[:8] == 'category':
				zugartcategory_strIO.write(self.__fkdict['fk_eckdatenid']+';'+line[8:11]+';'+languagecode+';'+line[12:]+'\n')
			elif line[:6] == 'option':
				zugartoption_strIO.write(self.__fkdict['fk_eckdatenid']+';'+line[6:8]+';'+languagecode+';'+line[9:]+'\n')
			elif line[:5] == 'class':
				zugartclass_strIO.write(self.__fkdict['fk_eckdatenid']+';'+line[5:7]+';'+languagecode+';'+line[8:]+'\n')

		zugart_strIO.seek(0)
		zugartcategory_strIO.seek(0)
		zugartclass_strIO.seek(0)
		zugartoption_strIO.seek(0)

		cur = self.__hrdfdb.connection.cursor()
		try:
			cur.copy_expert("COPY HRDF_ZUGART_TAB (fk_eckdatenid,categorycode,classno,tariffgroup,outputcontrol,categorydesc,extracharge,flags,categoryimage,categoryno) FROM STDIN USING DELIMITERS ';' NULL AS ''", zugart_strIO)
			zugartRows = cur.rowcount
			cur.copy_expert("COPY HRDF_ZUGARTKategorie_TAB (fk_eckdatenid,categoryno,languagecode,categorytext) FROM STDIN USING DELIMITERS ';' NULL AS ''",zugartcategory_strIO)
			zugartKatRows = cur.rowcount
			cur.copy_expert("COPY HRDF_ZUGARTKlasse_TAB (fk_eckdatenid,classno,languagecode,classtext) FROM STDIN USING DELIMITERS ';' NULL AS ''",zugartclass_strIO)
			zugartClassRows = cur.rowcount
			cur.copy_expert("COPY HRDF_ZUGARTOption_TAB (fk_eckdatenid,optionno,languagecode,optiontext) FROM STDIN USING DELIMITERS ';' NULL AS ''",zugartoption_strIO)
			zugartOptRows = cur.rowcount
			self.__hrdfdb.connection.commit()
			logger.debug('Zugart: {} ZugartKategorie: {} ZugartKlasse: {} ZuartOption: {} eingefügte Datensätze'.format(zugartRows, zugartKatRows, zugartClassRows, zugartOptRows))
		except Exception as e:
			logger.error('Fehler beim Lesen und Verarbeiten der Datei Zugart aufgetreten {}'.format(e))
		cur.close()
		zugart_strIO.close()
		zugartcategory_strIO.close()
		zugartclass_strIO.close()
		zugartoption_strIO.close()


	def read_linie(self, filename):
		"""Lesen der Datei LINIE"""
		logger.info('lesen und verarbeiten der Datei LINIE')
		linie_strIO = StringIO()

		languagecode = "--"
		bTextblock = False
		curLinienId = ''
		linienDict = dict();

		for line in fileinput.input(filename, openhook=self.__hrdfzip.open):
			line = line.decode(self.__charset).replace('\r\n', '')
			# Eine Zeile mit dem Inhalt "<text>" gibt an, dass nun nur noch die Textangaben in verschiedenen Sprachen folgen
			if not bTextblock:
				# solange das nicht der Fall ist, sollen die Daten als Zugarten weiter eingearbeitet werden
				if line != '<text>':
					curLinienId = line[:7]
					# Jede LinienID wird durch ein Dict im LinienDict aufgenommen
					if curLinienId not in linienDict:
						linienDict[curLinienId] = dict();
					# Behandeln der einzelnen Zeilentypen und Auffüllen des LinienDict
					if line[8] == 'K':
						linienDict[curLinienId]['line_key'] = line[10:].strip()
					elif line[8] == 'W':
						linienDict[curLinienId]['number_intern'] = line[10:].strip()
					elif line[8] == 'N':
						if line[11] == 'T':
							linienDict[curLinienId]['name_short'] = line[12:].strip()
						elif line[11] == 'I':
							linienDict[curLinienId]['name_short_index'] = line[12:15]
					elif line[8] == 'L':
						if line[11] == 'T':
							linienDict[curLinienId]['name_long'] = line[12:].strip()
						elif line[11] == 'I':
							linienDict[curLinienId]['name_long_index'] = line[12:15]
					elif line[8] == 'F':
						linienDict[curLinienId]['color_font'] = line[10:12]+','+line[14:16]+','+line[18:20]
					elif line[8] == 'B':
						linienDict[curLinienId]['color_back'] = line[10:12]+','+line[14:16]+','+line[18:20]						
				# sobald die Textangaben beginnen, werden die Daten sprachspezifisch in das jeweilige dictionary geschrieben
				else:
					bTextblock = True
			elif line[0] == '<':
				languagecode = line[1:3].lower()

		for line in linienDict:
			logger.debug('Add Linie to strIO')
			linie_strIO.write(self.__fkdict['fk_eckdatenid']+';'
									+linienDict[line].get('line_key')+';'
									+linienDict[line].get('number_intern', None)+';'
									+linienDict[line].get('name_short', None)+';'
									+linienDict[line].get('name_short_index', None)+';'
									+linienDict[line].get('name_long', None)+';'
									+linienDict[line].get('name_long_index', None)+';'
									+linienDict[line].get('color_font', None)+';'
									+linienDict[line].get('color_back', None)
									+'\n')

		linie_strIO.seek(0)
		cur = self.__hrdfdb.connection.cursor()
		try:
			cur.copy_expert("COPY HRDF_LINIE_TAB (fk_eckdatenid,line_key,number_intern,name_short,name_short_index,name_long,name_long_index,color_font,color_back) FROM STDIN USING DELIMITERS ';' NULL AS ''", linie_strIO)
			self.__hrdfdb.connection.commit()
			logger.debug('Linien: {} eingefügte Datensätze'.format(cur.rowcount))
		except Exception as e:
			logger.error('Fehler beim Lesen und Verarbeiten der Datei {} aufgetreten {}'.format(filename, e))
		cur.close()
		linie_strIO.close()


	def read_attribut(self, filename, sprache):
		"""Lesen der Datei ATTRIBUT
			ATTRIBUT aus INFO+ ist sprachabhängig in dem Format ATTRIBUT_XX
		"""
		if sprache.strip():	# wird keine Sprache übergeben, dann bleibt der Dateiname unverändert
			filename = filename + '_' + sprache
		else:
			sprache = '--'
		logger.info('lesen und verarbeiten der Datei '+filename)

		# Erster Durchlauf um die Ausgabeattributcodes für Teil- und Vollstrecke zu ermitteln
		targetcodes = {}
		for line in fileinput.input(filename, openhook=self.__hrdfzip.open):
			line = line.decode(self.__charset).replace('\r\n', '')
			if line[:1] == '#':
				targetcodes[line[2:4].strip()] = [line[5:7].strip(), line[8:10].strip()]

		attribute_strIO = StringIO()
		for line in fileinput.input(filename, openhook=self.__hrdfzip.open):
			line = line.decode(self.__charset).replace('\r\n', '')
			if line[:1] != '#':
				attrcode = line[:2].strip()
				if attrcode in targetcodes:
					attrcode_section = targetcodes[attrcode][0]
					attrcode_complete = targetcodes[attrcode][1]
				else:
					attrcode_section = ""
					attrcode_complete = ""

				attribute_strIO.write(self.__fkdict['fk_eckdatenid']+';'
											+attrcode+';'
											+sprache.lower()+';'
											+line[3:4]+';'
											+line[5:8]+';'
											+line[9:11]+';'
											+line[12:-1].replace(';','\;')+';'
											+attrcode_section+';'
											+attrcode_complete
											+'\n')
		
		attribute_strIO.seek(0)
		cur = self.__hrdfdb.connection.cursor()
		try:
			cur.copy_expert("COPY HRDF_ATTRIBUT_TAB (fk_eckdatenid,attributecode,languagecode,stopcontext,outputprio,outputpriosort,attributetext,outputforsection,outputforcomplete) FROM STDIN USING DELIMITERS ';' NULL AS ''", attribute_strIO)
			self.__hrdfdb.connection.commit()
			logger.debug('Attribute: {} eingefügte Datensätze'.format(cur.rowcount))
		except Exception as e:
			logger.error('Fehler beim Lesen und Verarbeiten der Datei {} aufgetreten {}'.format(filename, e))
		cur.close()
		attribute_strIO.close()


	def read_infotext(self, filename, sprache):
		"""Lesen der Datei INFOTEXT
			INFOTEXT aus INFO+ ist sprachabhängig in dem Format INFOTEXT_XX
		"""
		if sprache.strip():	# wird keine Sprache übergeben, dann bleibt der Dateiname unverändert
			filename = filename + '_' + sprache
		else:
			sprache = '--'
		logger.info('lesen und verarbeiten der Datei '+filename)

		infotext_strIO = StringIO()
		for line in fileinput.input(filename, openhook=self.__hrdfzip.open):
			line = line.decode(self.__charset).replace('\r\n', '')
			infotext_strIO.write(self.__fkdict['fk_eckdatenid']+';'
										+line[:9]+';'
										+sprache.lower()+';'
										+line[10:].replace(';','\;')
										+'\n')
		
		infotext_strIO.seek(0) 
		cur = self.__hrdfdb.connection.cursor()
		try:
			cur.copy_expert("COPY HRDF_INFOTEXT_TAB (fk_eckdatenid,infotextno,languagecode,infotext) FROM STDIN USING DELIMITERS ';' NULL AS ''", infotext_strIO)
			self.__hrdfdb.connection.commit()
			logger.debug('InfoText: {} eingefügte Datensätze'.format(cur.rowcount))
		except Exception as e:
			logger.error('Fehler beim Lesen und Verarbeiten der Datei {} aufgetreten {}'.format(filename, e))
		cur.close()
		infotext_strIO.close()

	def read_durchbi(self, filename):
		"""Lesen der Datei DURCHBI"""
		logger.info('lesen und verarbeiten der Datei DURCHBI')
		durchbi_strIO = StringIO()
		for line in fileinput.input(filename, openhook=self.__hrdfzip.open):
			line = line.decode(self.__charset).replace('\r\n', '')
			durchbi_strIO.write(self.__fkdict['fk_eckdatenid']+';'
										 +line[:6]+';'
										 +line[7:13].strip()+';'
										 +line[14:21]+';'
										 +line[22:28]+';'
										 +line[29:35].strip()+';'
										 +line[36:42]+';'
										 +line[43:50]+';'
										 +line[51:53].strip()+';'
										 +line[54:].strip()
										+'\n')
		durchbi_strIO.seek(0)
		cur = self.__hrdfdb.connection.cursor()
		try:
			cur.copy_expert("COPY HRDF_DURCHBI_TAB (fk_eckdatenid,tripno1,operationalno1,laststopno1,tripno2,operationalno2,bitfieldno,firststopno2,attribute,comment) FROM STDIN USING DELIMITERS ';' NULL AS ''", durchbi_strIO)
			self.__hrdfdb.connection.commit()
			logger.debug('Durchbindung: {} eingefügte Datensätze'.format(cur.rowcount))
		except Exception as e:
			logger.error('Fehler beim Lesen und Verarbeiten der Datei DURCHBI aufgetreten {}'.format(e))
		cur.close()
		durchbi_strIO.close()

	def read_bfkoordgeo(self, filename):
		"""Lesen der Datei BFKOORD_GEO"""
		logger.info('lesen und verarbeiten der Datei BFKOORD_WGS')
		bfkoordgeo_strIO = StringIO()
		for line in fileinput.input(filename, openhook=self.__hrdfzip.open):
			line = line.decode(self.__charset).replace('\r\n', '')
			bfkoordgeo_strIO.write(self.__fkdict['fk_eckdatenid']+';'
										 +line[:7]+';'
										 +line[8:18]+';'
										 +line[19:29]+';'
										 +line[30:36]
										+'\n')
		bfkoordgeo_strIO.seek(0)
		cur = self.__hrdfdb.connection.cursor()
		try:
			cur.copy_expert("COPY HRDF_BFKOORD_TAB (fk_eckdatenid,stopno,longitude_geo,latitude_geo,altitude_geo) FROM STDIN USING DELIMITERS ';' NULL AS ''", bfkoordgeo_strIO)
			self.__hrdfdb.connection.commit()
			logger.debug('BFKoord_WGS: {} eingefügte Datensätze'.format(cur.rowcount))
		except Exception as e:
			logger.error('Fehler beim Lesen und Verarbeiten der Datei BFKOORD_WGS aufgetreten {}'.format(e))
		cur.close()
		bfkoordgeo_strIO.close()

	def read_umsteigb(self, filename):
		"""Lesen der Datei UMSTEIGB"""
		logger.info('lesen und verarbeiten der Datei UMSTEIGB')
		umsteigb_strIO = StringIO()
		for line in fileinput.input(filename, openhook=self.__hrdfzip.open):
			line = line.decode(self.__charset).replace('\r\n', '')
			umsteigb_strIO.write(self.__fkdict['fk_eckdatenid']+';'
										 +line[:7]+';'
										 +line[8:10]+';'
										 +line[11:13]
										+'\n')
		umsteigb_strIO.seek(0)
		cur = self.__hrdfdb.connection.cursor()
		try:
			cur.copy_expert("COPY HRDF_UMSTEIGB_TAB (fk_eckdatenid,stopno,transfertime1,transfertime2) FROM STDIN USING DELIMITERS ';' NULL AS ''", umsteigb_strIO)
			self.__hrdfdb.connection.commit()
			logger.debug('UmsteigB: {} eingefügte Datensätze'.format(cur.rowcount))
		except Exception as e:
			logger.error('Fehler beim Lesen und Verarbeiten der Datei UMSTEIGB aufgetreten {}'.format(e))
		cur.close()
		umsteigb_strIO.close()

	def read_bfprios(self, filename):
		"""Lesen der Datei BFPRIOS"""
		logger.info('lesen und verarbeiten der Datei BFPRIOS')
		bfprios_strIO = StringIO()
		for line in fileinput.input(filename, openhook=self.__hrdfzip.open):
			line = line.decode(self.__charset).replace('\r\n', '')
			bfprios_strIO.write(self.__fkdict['fk_eckdatenid']+';'
										 +line[:7]+';'
										 +line[8:10]
										+'\n')
		bfprios_strIO.seek(0)
		cur = self.__hrdfdb.connection.cursor()
		try:
			cur.copy_expert("COPY HRDF_BFPRIOS_TAB (fk_eckdatenid,stopno,transferprio) FROM STDIN USING DELIMITERS ';' NULL AS ''", bfprios_strIO)
			self.__hrdfdb.connection.commit()
			logger.debug('BFPRIOS: {} eingefügte Datensätze'.format(cur.rowcount))
		except Exception as e:
			logger.error('Fehler beim Lesen und Verarbeiten der Datei BFPRIOS aufgetreten {}'.format(e))
		cur.close()
		bfprios_strIO.close()

	def read_metabhf(self, filename):
		"""Lesen der Datei METABHF"""
		logger.info('lesen und verarbeiten der Datei METABHF')
		metabhfUB_strIO = StringIO()
		metabhfHG_strIO = StringIO()

		previousUB = False
		strStopNoFrom = None;
		strStopNoTo = None;
		strTransferTimeMin = None;
		strTransferTimeSec = None;
		strAttributeCodes = "";
		attributeCodeList = list();
		stopMemberList = list();
		groupDict = dict(); 
		for line in fileinput.input(filename, openhook=self.__hrdfzip.open):
			line = line.decode(self.__charset).replace('\r\n', '')
			
			if line[:1] == '*':
				# Attributszeile der Übergangsbeziehung				
				if line[1:2] == 'A':
					# Uns interessieren momentan nur die A-Zeilen (Attributecode)
					attributeCodeList.append(line[3:5].strip())

			elif line[7:8] == ':':
				# Haltestellengruppen-Zeile
				# Ist noch eine offene Übergangsbeziehung vorhanden? Die muss noch gespeichert werden
				if (previousUB):
					if (len(attributeCodeList) > 0): strAttributeCodes = "{'" + "','".join(map(str,attributeCodeList)) + "'}"
					metabhfUB_strIO.write(self.__fkdict['fk_eckdatenid']+';'
												 +strStopNoFrom+';'
												 +strStopNoTo+';'
												 +strTransferTimeMin+';'
												 +strTransferTimeSec+';'
												 +strAttributeCodes
												+'\n')
					# Zurücksetzen der Attributcodes-Liste
					attributeCodeList.clear();
					strAttributeCodes = "";
					previousUB = False;

				# Behandlung der Haltestellengruppen-Zeile
				# Erster Stop beginnt bei Zeichen 10, danach beliebig viele Stops in der Länge von 7 Zeichen
				stopMemberList.clear()
				strStopMember = ""
				nextMemberStart = 10
				while (nextMemberStart < len(line)):
					stopMemberList.append(line[nextMemberStart:nextMemberStart+7])
					nextMemberStart = nextMemberStart+9
				if (len(stopMemberList) > 0): strStopMember = "{" + ",".join(map(str,stopMemberList)) + "}"
				strStopGroupNo = line[10:17]
				if (strStopGroupNo in groupDict):
					pass
				else:
					groupDict[strStopGroupNo] = strStopMember
					metabhfHG_strIO.write(self.__fkdict['fk_eckdatenid']+';'
									+strStopGroupNo+';'
									+strStopMember
								+'\n')

			else:
				# 1. Zeile einer Übergangsbeziehung
				if (previousUB):
					# Sichern der Übergangsbeziehung
					if (len(attributeCodeList) > 0): strAttributeCodes = "{'" + "','".join(map(str,attributeCodeList)) + "'}"
					metabhfUB_strIO.write(self.__fkdict['fk_eckdatenid']+';'
												 +strStopNoFrom+';'
												 +strStopNoTo+';'
												 +strTransferTimeMin+';'
												 +strTransferTimeSec+';'
												 +strAttributeCodes
												+'\n')

				# Zurücksetzen der Attributcodes-Liste
				attributeCodeList.clear();
				strAttributeCodes = "";
				strStopNoFrom = line[:7]
				strStopNoTo = line[8:15]
				strTransferTimeMin = line[16:19]
				strTransferTimeSec = line[20:22]
				previousUB = True

		metabhfUB_strIO.seek(0)
		metabhfHG_strIO.seek(0)
		curUB = self.__hrdfdb.connection.cursor()
		curHG = self.__hrdfdb.connection.cursor()
		try: # Absichern der DB-Cursor
			curUB.copy_expert("COPY HRDF_METABHF_TAB (fk_eckdatenid,stopnofrom,stopnoto,transfertimemin,transfertimesec,attributecode) FROM STDIN USING DELIMITERS ';' NULL AS ''", metabhfUB_strIO)
			self.__hrdfdb.connection.commit()
			logger.debug('METABHF: {} eingefügte Datensätze'.format(curUB.rowcount))

			curHG.copy_expert("COPY HRDF_METABHFGRUPPE_TAB (fk_eckdatenid,stopgroupno,stopmember) FROM STDIN USING DELIMITERS ';' NULL AS ''", metabhfHG_strIO)
			self.__hrdfdb.connection.commit()
			logger.debug('METABHFGRUPPE: {} eingefügte Datensätze'.format(curHG.rowcount))
		except Exception as e:
			logger.error('Fehler beim Lesen und Verarbeiten der Datei METABHF aufgetreten {}'.format(e))
		curUB.close()
		curHG.close()
		metabhfUB_strIO.close()
		metabhfHG_strIO.close()


	def save_currentFplanFahrt(self):
		"""Funkion speichert die aktuellen Werte zu einer FPLAN-Fahrt"""
		self.__fplanFahrtG_strIO.seek(0)
		self.__fplanFahrtAVE_strIO.seek(0)
		self.__fplanFahrtLauf_strIO.seek(0)
		cur = self.__hrdfdb.connection.cursor()
		try: # Absichern des DB-Cursor
			cur.copy_expert("COPY HRDF_FPLANFahrtG_TAB (fk_eckdatenid,fk_fplanfahrtid,categorycode,fromStop,toStop,deptimeFrom,arrtimeTo) FROM STDIN USING DELIMITERS ';' NULL AS ''", self.__fplanFahrtG_strIO)
			cur.copy_expert("COPY HRDF_FPLANFahrtVE_TAB (fk_eckdatenid,fk_fplanfahrtid,fromStop,toStop,bitfieldno,deptimeFrom,arrtimeTo) FROM STDIN USING DELIMITERS ';' NULL AS ''", self.__fplanFahrtAVE_strIO)
			cur.copy_expert("COPY HRDF_FPLANFahrtLaufweg_TAB (fk_eckdatenid,fk_fplanfahrtid,stopno,stopname,sequenceno,arrtime,deptime,tripno,operationalno,ontripsign) FROM STDIN USING DELIMITERS ';' NULL AS ''", self.__fplanFahrtLauf_strIO)
			if self.__fplanFahrtA_strIO.tell() > 0:
				self.__fplanFahrtA_strIO.seek(0)
				cur.copy_expert("COPY HRDF_FPLANFahrtA_TAB (fk_eckdatenid,fk_fplanfahrtid,attributecode,fromStop,toStop,bitfieldno,deptimeFrom,arrtimeTo) FROM STDIN USING DELIMITERS ';' NULL AS ''", self.__fplanFahrtA_strIO)
			if self.__fplanFahrtR_strIO.tell() > 0:
				self.__fplanFahrtR_strIO.seek(0)
				cur.copy_expert("COPY HRDF_FPLANFahrtR_TAB (fk_eckdatenid,fk_fplanfahrtid,directionshort,directioncode,fromStop,toStop,deptimeFrom,arrtimeTo) FROM STDIN USING DELIMITERS ';' NULL AS ''", self.__fplanFahrtR_strIO)
			if self.__fplanFahrtI_strIO.tell() > 0:
				self.__fplanFahrtI_strIO.seek(0)
				cur.copy_expert("COPY HRDF_FPLANFahrtI_TAB (fk_eckdatenid,fk_fplanfahrtid,infotextcode,infotextno,fromStop,toStop,bitfieldno,deptimeFrom,arrtimeTo) FROM STDIN USING DELIMITERS ';' NULL AS ''", self.__fplanFahrtI_strIO)
			if self.__fplanFahrtL_strIO.tell() > 0:
				self.__fplanFahrtL_strIO.seek(0)
				cur.copy_expert("COPY HRDF_FPLANFahrtL_TAB (fk_eckdatenid,fk_fplanfahrtid,lineno,fromStop,toStop,deptimeFrom,arrtimeTo) FROM STDIN USING DELIMITERS ';' NULL AS ''", self.__fplanFahrtL_strIO)
			if self.__fplanFahrtSH_strIO.tell() > 0:
				self.__fplanFahrtSH_strIO.seek(0)
				cur.copy_expert("COPY HRDF_FPLANFahrtSH_TAB (fk_eckdatenid,fk_fplanfahrtid,stop,bitfieldno,deptimeFrom) FROM STDIN USING DELIMITERS ';' NULL AS ''", self.__fplanFahrtSH_strIO)
			if self.__fplanFahrtC_strIO.tell() > 0:
				self.__fplanFahrtC_strIO.seek(0)
				cur.copy_expert("COPY HRDF_FPLANFahrtC_TAB (fk_eckdatenid,fk_fplanfahrtid,checkintime,checkouttime,fromStop,toStop,deptimeFrom,arrtimeTo) FROM STDIN USING DELIMITERS ';' NULL AS ''", self.__fplanFahrtC_strIO)
			if self.__fplanFahrtGR_strIO.tell() > 0:
				self.__fplanFahrtGR_strIO.seek(0)
				cur.copy_expert("COPY HRDF_FPLANFahrtGR_TAB (fk_eckdatenid,fk_fplanfahrtid,borderStop,prevStop,nextStop,deptimePrev,arrtimeNext) FROM STDIN USING DELIMITERS ';' NULL AS ''", self.__fplanFahrtGR_strIO)
		
			self.__hrdfdb.connection.commit()
		except Exception as e:
			logger.error('Fehler beim Sichern der aktuellen Fahrt aufgetreten {}'.format(e))
		cur.close()

		# Schließen der StringIOs und anschließendes neu anlegen soll performanter sein als truncate(0)
		self.__fplanFahrtG_strIO.close()
		self.__fplanFahrtAVE_strIO.close()
		self.__fplanFahrtLauf_strIO.close()
		self.__fplanFahrtA_strIO.close()
		self.__fplanFahrtR_strIO.close()
		self.__fplanFahrtI_strIO.close()
		self.__fplanFahrtL_strIO.close()
		self.__fplanFahrtSH_strIO.close()
		self.__fplanFahrtC_strIO.close()
		self.__fplanFahrtGR_strIO.close()

		self.__fplanFahrtG_strIO = StringIO()
		self.__fplanFahrtAVE_strIO = StringIO()
		self.__fplanFahrtLauf_strIO = StringIO()
		self.__fplanFahrtA_strIO = StringIO()
		self.__fplanFahrtR_strIO = StringIO()
		self.__fplanFahrtI_strIO = StringIO()
		self.__fplanFahrtL_strIO = StringIO()
		self.__fplanFahrtSH_strIO = StringIO()
		self.__fplanFahrtC_strIO = StringIO()
		self.__fplanFahrtGR_strIO = StringIO()

		self.__fkdict["fk_fplanfahrtid"] = -1

	def read_fplan(self, filename):
		"""Lesen der Datei FPLAN"""
		logger.info('lesen und verarbeiten der Datei FPLAN')
		curIns = self.__hrdfdb.connection.cursor()
		try: # Absichern des DB-Cursors (wird für *Z und *T Zeilen verwendet)
			bDataLinesRead = False
			iSequenceCnt = 0
			iNumberFplanFahrt = 0
			for line in fileinput.input(filename, openhook=self.__hrdfzip.open):
				line = line.decode(self.__charset).replace('\r\n','')

				if line[:1] == '*':
					if bDataLinesRead:
						# Datenzeilen wurden gelesen, wir sind jetzt wieder beim nächsten Zug und schreiben den Vorgänger erstmal in die DB
						self.save_currentFplanFahrt()
						iNumberFplanFahrt += 1
						bDataLinesRead = False
						iSequenceCnt = 0

					# Attribut-Zeilen (!! längste Attribut-Kennung zuerst abfragen, dann weiter absteigend !!)
					if line[:5] == "*A VE":
						if self.__AVE_type == "*Z" or self.__AVE_type == "*T":
							self.__fplanFahrtAVE_strIO.write(self.__fkdict["fk_eckdatenid"]+';'
														  +self.__fkdict["fk_fplanfahrtid"]+';'
														  +line[6:13].strip()+';'
														  +line[14:21].strip()+';'
														  +line[22:28].strip()+';'
														  +line[29:35].strip()+';'
														  +line[36:42].strip()+
														  '\n')
						else:
							logger.warning("*A VE-Zeile gehört zu nicht unterstützter "+self.__AVE_type+"-Zeile und wird nicht verarbeitet")
						
					elif line[:4] == "*KWZ":
						self.__AVE_type = line[:4]
						logger.warning("Zeile "+line[:4]+" wird derzeit nicht unterstützt")

					elif line[:3] == "*KW" or line[:3] == "*TT":
						self.__AVE_type = line[:3]
						logger.warning("Zeile "+line[:3]+" wird derzeit nicht unterstützt")

					elif line[:3] == "*SH":
						self.__fplanFahrtSH_strIO.write(self.__fkdict["fk_eckdatenid"]+';'
														+self.__fkdict["fk_fplanfahrtid"]+';'
														+line[4:11].strip()+';'
														+line[12:18].strip()+';'
														+line[19:25].strip()+
														'\n')

					elif line[:3] == "*GR":
						self.__fplanFahrtGR_strIO.write(self.__fkdict["fk_eckdatenid"]+';'
														+self.__fkdict["fk_fplanfahrtid"]+';'
														+line[4:11].strip()+';'
														+line[12:19].strip()+';'
														+line[20:27].strip()+';'
														+line[28:34].strip()+';'
														+line[35:41].strip()+
														'\n')


					elif line[:2] == "*B" or line[:2] == "*E":
						logger.warning("Zeile "+line[:2]+" wird derzeit nicht unterstützt")

					elif line[:2] == "*Z":
						self.__AVE_type = line[:2]
						sql_string = "INSERT INTO HRDF_FPLANFahrt_TAB (fk_eckdatenid,triptype,tripno,operationalno,tripversion,cyclecount,cycletimemin) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id;"
						cyclecount = line[23:26].strip()
						cycletimemin = line[27:30].strip()
						if not cyclecount:
							cyclecount = None
						if not cycletimemin:
							cycletimemin = None
						curIns.execute(sql_string, (self.__fkdict['fk_eckdatenid'], line[1:2], line[3:9], line[10:16], line[17:22], cyclecount, cycletimemin))
						self.__fkdict["fk_fplanfahrtid"] = str(curIns.fetchone()[0])

					elif line[:2] == "*T":
						self.__AVE_type = line[:2]
						sql_string = "INSERT INTO HRDF_FPLANFahrt_TAB (fk_eckdatenid,triptype,tripno,operationalno,triptimemin,cycletimesec) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id;"
						triptimemin = line[16:20].strip()
						cycletimesec = line[21:25].strip()
						if not triptimemin:
							triptimemin = None
						if not cycletimesec:
							cycletimesec = None
						curIns.execute(sql_string, (self.__fkdict['fk_eckdatenid'], line[1:2], line[3:8], line[9:15], triptimemin, cycletimesec))
						self.__fkdict["fk_fplanfahrtid"] = str(curIns.fetchone()[0])

					elif line[:2] == "*C":
						checkinTime = '';
						checkoutTime = '';
						if line[:3] == "*CI":
							checkinTime = line[4:8].strip();
						if line[:3] == "*CO":
							checkoutTime = line[4:8].strip();
						self.__fplanFahrtC_strIO.write(self.__fkdict["fk_eckdatenid"]+';'
														+self.__fkdict["fk_fplanfahrtid"]+';'
														+checkinTime+';'
														+checkoutTime+';'
														+line[9:16].strip()+';'
														+line[17:24].strip()+';'
														+line[25:31].strip()+';'
														+line[32:38].strip()+
														'\n')

					elif line[:2] == "*G":
						self.__fplanFahrtG_strIO.write(self.__fkdict["fk_eckdatenid"]+';'
														+self.__fkdict["fk_fplanfahrtid"]+';'
														+line[3:6].strip()+';'
														+line[7:14].strip()+';'
														+line[15:22].strip()+';'
														+line[23:29].strip()+';'
														+line[30:36].strip()+
														'\n')
					elif line[:2] == "*A":
						if self.__AVE_type == "*Z" or self.__AVE_type == "*T":
							self.__fplanFahrtA_strIO.write(self.__fkdict["fk_eckdatenid"]+';'
															+self.__fkdict["fk_fplanfahrtid"]+';'
															+line[3:5].strip()+';'
															+line[6:13].strip()+';'
															+line[14:21].strip()+';'
															+line[22:28].strip()+';'
															+line[29:35].strip()+';'
															+line[36:42].strip()+
															'\n')
						else:
							logger.warning("*A Zeile gehört zu nicht unterstützter "+self.__AVE_type+"-Zeile und wird nicht verarbeitet")

					elif line[:2] == "*R":
						self.__fplanFahrtR_strIO.write(self.__fkdict["fk_eckdatenid"]+';'
														+self.__fkdict["fk_fplanfahrtid"]+';'
														+line[3:4].strip()+';'
														+line[5:12].strip()+';'
														+line[13:20].strip()+';'
														+line[21:28].strip()+';'
														+line[29:35].strip()+';'
														+line[36:42].strip()+
														'\n')
					elif line[:2] == "*I":
						self.__fplanFahrtI_strIO.write(self.__fkdict["fk_eckdatenid"]+';'
														+self.__fkdict["fk_fplanfahrtid"]+';'
														+line[3:5].strip()+';'
														+line[29:38].strip()+';'
														+line[6:13].strip()+';'
														+line[14:21].strip()+';'
														+line[22:28].strip()+';'
														+line[39:45].strip()+';'
														+line[46:52].strip()+
														'\n')

					elif line[:2] == "*L":
						self.__fplanFahrtL_strIO.write(self.__fkdict["fk_eckdatenid"]+';'
														+self.__fkdict["fk_fplanfahrtid"]+';'
														+line[3:11].strip()+';'
														+line[12:19].strip()+';'
														+line[20:27].strip()+';'
														+line[28:34].strip()+';'
														+line[35:41].strip()+
														'\n')

				else:
					# Laufwegszeilen
					bDataLinesRead = True
					if (line[:1] == "+"):
						logger.warning("Laufwegsdaten mit Regionen werden nicht unterstützt")
					else:
						self.__fplanFahrtLauf_strIO.write(self.__fkdict["fk_eckdatenid"]+';'
															+self.__fkdict["fk_fplanfahrtid"]+';'
															+line[:7].strip()+';'
															+line[8:29].strip()+';'
															+str(iSequenceCnt)+';'
															+line[29:35].strip()+';'
															+line[36:42].strip()+';'
															+line[43:48].strip()+';'
															+line[49:55].strip()+';'
															+line[56:57].strip()+
															'\n')
						iSequenceCnt += 1

			# Nach dem Durchlauf der Schleife muss der letzte Zug noch gespeichert werden
			if bDataLinesRead:
				self.save_currentFplanFahrt()
				iNumberFplanFahrt += 1
				bDataLinesRead = False
				iSequenceCnt = 0

			logger.debug('FplanFahrt: {} eingefügte Datensätze'.format(iNumberFplanFahrt))
		except Exception as e:
			logger.error('Fehler beim Lesen und Verarbeiten der Datei FPLAN aufgetreten {}'.format(e))
		curIns.close()
