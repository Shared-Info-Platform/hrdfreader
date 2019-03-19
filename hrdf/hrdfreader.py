import psycopg2
import zipfile
import fileinput
from datetime import datetime, date, timedelta
from io import StringIO
from bitstring import Bits
from hrdf.hrdfhelper import *


class HrdfReader:
	"""
	Die Klasse liest die HRDF-Dateien und schreibt diese in die Datenbank

	HrdfReader(hrdfzipfile, db, hrdffiles)

	"""
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


	def readfiles(self):
		"""Liest die gewünschten HRDF-Dateien und schreibt sie in die Datenbank"""

		for filename in self.__hrdffiles:
			if filename == "ECKDATEN":
				self.read_eckdaten(filename)
			elif filename == "BITFELD":
				self.read_bitfeld(filename)
			elif filename == "RICHTUNG":
				self.read_richtung(filename)
			elif filename == "ZUGART":
				self.read_zugart(filename)
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
			else:
				print("Das Lesen von [",filename,"] wird nicht unterstützt")


	def read_eckdaten(self, filename):
		"""Lesen der Datei ECKDATEN"""
		print('lesen und verarbeiten der ECKDATEN')
		lines = self.__hrdfzip.read(filename).decode(self.__charset).split('\r\n')[:-1]
 		# spezifisch für SBB-Version ist die Trenner in der Bezeichnung, die hier in separate Felder geschrieben werden
		bezeichnung,exportdatum,hrdfversion,lieferant = lines[2].split('$')
		cur = self.__hrdfdb.connection.cursor()
		sql_string = "INSERT INTO HRDF_ECKDATEN_TAB (validFrom, validTo, descriptionhrdf, description, creationdatetime, hrdfversion, exportsystem) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id;" 
		cur.execute(sql_string, (lines[0], lines[1], lines[2], bezeichnung, exportdatum, hrdfversion, lieferant))
		self.__fkdict["fk_eckdatenid"] = str(cur.fetchone()[0])
		self.__hrdfdb.connection.commit()
		self.__eckdaten_validFrom = datetime.strptime(lines[0], '%d.%m.%Y').date()
		self.__eckdaten_validTo = datetime.strptime(lines[1], '%d.%m.%Y').date()
		cur.close()
		

	def read_bitfeld(self, filename):
		"""Lesen der Datei BITFELD"""
		print('lesen und verarbeiten der BITFELD')
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

			validDaysString = "{'" + "','".join(map(str,validDays)) + "'}"
			bitfeld_strIO.write(self.__fkdict['fk_eckdatenid']+';'
										+line[:6]+';'
										+line[7:]+';'
										+bitfield+';'
										+validDaysString
										+'\n')
		bitfeld_strIO.seek(0)
		cur = self.__hrdfdb.connection.cursor()
		cur.copy_expert("COPY HRDF_BITFELD_TAB (fk_eckdatenid,bitfieldno,bitfield,bitfieldextend,bitfieldarray) FROM STDIN USING DELIMITERS ';' NULL AS ''",bitfeld_strIO)
		self.__hrdfdb.connection.commit()
		cur.close()
		bitfeld_strIO.close()


	def read_richtung(self, filename):
		"""Lesen der Datei RICHTUHNG"""
		print('lesen und verarbeiten der RICHTUNG')
		richtung_strIO = StringIO()
		for line in fileinput.input(filename, openhook=self.__hrdfzip.open):
			line = line.decode(self.__charset).replace('\r\n', '')
			richtung_strIO.write(self.__fkdict['fk_eckdatenid']+';'
										 +line[:7]+';'
										 +line[8:59]
										+'\n')
		richtung_strIO.seek(0)
		cur = self.__hrdfdb.connection.cursor()
		cur.copy_expert("COPY HRDF_RICHTUNG_TAB (fk_eckdatenid,directioncode, directiontext) FROM STDIN USING DELIMITERS ';' NULL AS ''", richtung_strIO)
		self.__hrdfdb.connection.commit()
		cur.close()
		richtung_strIO.close()


	def read_zugart(self, filename):
		"""Lesen der Datei ZUGART"""
		print('lesen und verarbeiten der ZUGART')
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
		cur.copy_expert("COPY HRDF_ZUGART_TAB (fk_eckdatenid,categorycode,classno,tariffgroup,outputcontrol,categorydesc,extracharge,flags,categoryimage,categoryno) FROM STDIN USING DELIMITERS ';' NULL AS ''", zugart_strIO)
		cur.copy_expert("COPY HRDF_ZUGARTKategorie_TAB (fk_eckdatenid,categoryno,languagecode,categorytext) FROM STDIN USING DELIMITERS ';' NULL AS ''",zugartcategory_strIO)
		cur.copy_expert("COPY HRDF_ZUGARTKlasse_TAB (fk_eckdatenid,classno,languagecode,classtext) FROM STDIN USING DELIMITERS ';' NULL AS ''",zugartclass_strIO)
		cur.copy_expert("COPY HRDF_ZUGARTOption_TAB (fk_eckdatenid,optionno,languagecode,optiontext) FROM STDIN USING DELIMITERS ';' NULL AS ''",zugartoption_strIO)
		self.__hrdfdb.connection.commit()
		cur.close()
		zugart_strIO.close()
		zugartcategory_strIO.close()
		zugartclass_strIO.close()
		zugartoption_strIO.close()


	def read_attribut(self, filename, sprache):
		"""Lesen der Datei ATTRIBUT
			ATTRIBUT aus INFO+ ist sprachabhängig in dem Format ATTRIBUT_XX
		"""
		print('lesen und verarbeiten der ATTRIBUT')
		if sprache.strip():	# wird keine Sprache übergeben, dann bleibt der Dateiname unverändert
			filename = filename + '_' + sprache
		else:
			sprache = '--'

		# Erster Durchlauf um die Ausgabeattributscodes für Teil- und Vollstrecke zu ermitteln
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
		cur.copy_expert("COPY HRDF_ATTRIBUT_TAB (fk_eckdatenid,attributecode,languagecode,stopcontext,outputprio,outputpriosort,attributetext,outputforsection,outputforcomplete) FROM STDIN USING DELIMITERS ';' NULL AS ''", attribute_strIO)
		self.__hrdfdb.connection.commit()
		cur.close()
		attribute_strIO.close()


	def read_infotext(self, filename, sprache):
		"""Lesen der Datei INFOTEXT
			INFOTEXT aus INFO+ ist sprachabhängig in dem Format INFOTEXT_XX
		"""
		print('lesen und verarbeiten der INFOTEXT')
		if sprache.strip():	# wird keine Sprache übergeben, dann bleibt der Dateiname unverändert
			filename = filename + '_' + sprache
		else:
			sprache = '--'

		infotext_strIO = StringIO()
		for line in fileinput.input(filename, openhook=self.__hrdfzip.open):
			line = line.decode(self.__charset).replace('\r\n', '')
			infotext_strIO.write(self.__fkdict['fk_eckdatenid']+';'
										+line[:7]+';'
										+sprache.lower()+';'
										+line[8:].replace(';','\;')
										+'\n')
		
		infotext_strIO.seek(0)
		cur = self.__hrdfdb.connection.cursor()
		cur.copy_expert("COPY HRDF_INFOTEXT_TAB (fk_eckdatenid,infotextno,infotextlanguage,infotext) FROM STDIN USING DELIMITERS ';' NULL AS ''", infotext_strIO)
		self.__hrdfdb.connection.commit()
		cur.close()
		infotext_strIO.close()


	def read_fplan(self, filename):
		"""Lesen der Datei FPLAN"""
		print('lesen und verarbeiten der FPLAN')
		curIns = self.__hrdfdb.connection.cursor()


		fplanFahrtG_strIO = StringIO()
		fplanFahrtAVE_strIO = StringIO()
		fplanFahrtLauf_strIO = StringIO()
		fplanFahrtA_strIO = StringIO()
		fplanFahrtR_strIO = StringIO()
		fplanFahrtI_strIO = StringIO()
		fplanFahrtL_strIO = StringIO()

		bDataLinesRead = False
		iSequenceCnt = 0
		for line in fileinput.input(filename, openhook=self.__hrdfzip.open):
			line = line.decode(self.__charset).replace('\r\n','')

			if line[:1] == '*':
				if bDataLinesRead:
					# Datenzeilen wurden gelesen, wir sind jetzt wieder beim nächsten Zug und schreiben den Vorgänger erstmal in die DB
					fplanFahrtG_strIO.seek(0)
					fplanFahrtAVE_strIO.seek(0)
					fplanFahrtLauf_strIO.seek(0)
					cur = self.__hrdfdb.connection.cursor()
					cur.copy_expert("COPY HRDF_FPLANFahrtG_TAB (fk_eckdatenid,fk_fplanfahrtid,categorycode,fromStop,toStop,deptimeFrom,arrtimeFrom) FROM STDIN USING DELIMITERS ';' NULL AS ''", fplanFahrtG_strIO)
					cur.copy_expert("COPY HRDF_FPLANFahrtVE_TAB (fk_eckdatenid,fk_fplanfahrtid,fromStop,toStop,bitfieldno,deptimeFrom,arrtimeFrom) FROM STDIN USING DELIMITERS ';' NULL AS ''", fplanFahrtAVE_strIO)
					cur.copy_expert("COPY HRDF_FPLANFahrtLaufweg_TAB (fk_eckdatenid,fk_fplanfahrtid,stopno,stopname,sequenceno,arrtime,deptime,tripno,operationalno,ontripsign) FROM STDIN USING DELIMITERS ';' NULL AS ''", fplanFahrtLauf_strIO)
					if fplanFahrtA_strIO.tell() > 0:
						fplanFahrtA_strIO.seek(0)
						cur.copy_expert("COPY HRDF_FPLANFahrtA_TAB (fk_eckdatenid,fk_fplanfahrtid,attributecode,fromStop,toStop,bitfieldno,deptimeFrom,arrtimeFrom) FROM STDIN USING DELIMITERS ';' NULL AS ''", fplanFahrtA_strIO)
					if fplanFahrtR_strIO.tell() > 0:
						fplanFahrtR_strIO.seek(0)
						cur.copy_expert("COPY HRDF_FPLANFahrtR_TAB (fk_eckdatenid,fk_fplanfahrtid,directionshort,directioncode,fromStop,toStop,deptimeFrom,arrtimeFrom) FROM STDIN USING DELIMITERS ';' NULL AS ''", fplanFahrtR_strIO)
					if fplanFahrtI_strIO.tell() > 0:
						fplanFahrtI_strIO.seek(0)
						cur.copy_expert("COPY HRDF_FPLANFahrtI_TAB (fk_eckdatenid,fk_fplanfahrtid,infotextcode,infotextno,fromStop,toStop,bitfieldno,deptimeFrom,arrtimeFrom) FROM STDIN USING DELIMITERS ';' NULL AS ''", fplanFahrtI_strIO)
					if fplanFahrtL_strIO.tell() > 0:
						fplanFahrtL_strIO.seek(0)
						cur.copy_expert("COPY HRDF_FPLANFahrtL_TAB (fk_eckdatenid,fk_fplanfahrtid,lineno,fromStop,toStop,deptimeFrom,arrtimeFrom) FROM STDIN USING DELIMITERS ';' NULL AS ''", fplanFahrtL_strIO)
		
					self.__hrdfdb.connection.commit()

					fplanFahrtG_strIO.close()
					fplanFahrtAVE_strIO.close()
					fplanFahrtLauf_strIO.close()
					fplanFahrtA_strIO.close()
					fplanFahrtR_strIO.close()
					fplanFahrtI_strIO.close()
					fplanFahrtL_strIO.close()


					fplanFahrtG_strIO = StringIO()
					fplanFahrtAVE_strIO = StringIO()
					fplanFahrtLauf_strIO = StringIO()
					fplanFahrtA_strIO = StringIO()
					fplanFahrtR_strIO = StringIO()
					fplanFahrtI_strIO = StringIO()
					fplanFahrtL_strIO = StringIO()

					self.__fkdict["fk_fplanfahrtid"] = -1
					bDataLinesRead = False
					iSequenceCnt = 0



				# Attribut-Zeilen
				if line[:2] == "*Z":
					sql_string = "INSERT INTO HRDF_FPLANFahrt_TAB (fk_eckdatenid,triptype,tripno,operationalno,tripversion,cyclecount,cycletimemin) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id;"
					cyclecount = line[22:25].strip()
					cycletimemin = line[26:29].strip()
					if not cyclecount:
						cyclecount = None
					if not cycletimemin:
						cycletimemin = None
					curIns.execute(sql_string, (self.__fkdict['fk_eckdatenid'], line[1:2], line[3:8], line[9:15], line[18:21], cyclecount, cycletimemin))
					self.__fkdict["fk_fplanfahrtid"] = str(curIns.fetchone()[0])

				elif line[:2] == "*T":
					sql_string = "INSERT INTO HRDF_FPLANFahrt_TAB (fk_eckdatenid,triptype,tripno,operationalno,triptimemin,cycletimesec) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id;"
					triptimemin = line[16:20].strip()
					cycletimesec = line[21:25].strip()
					if not triptimemin:
						triptimemin = None
					if not cycletimesec:
						cycletimesec = None
					curIns.execute(sql_string, (self.__fkdict['fk_eckdatenid'], line[1:2], line[3:8], line[9:15], triptimemin, cycletimesec))
					self.__fkdict["fk_fplanfahrtid"] = str(curIns.fetchone()[0])

				elif line[:2] == "*G":
					fplanFahrtG_strIO.write(self.__fkdict["fk_eckdatenid"]+';'
													+self.__fkdict["fk_fplanfahrtid"]+';'
													+line[3:6].strip()+';'
													+line[7:14].strip()+';'
													+line[15:22].strip()+';'
													+line[23:29].strip()+';'
													+line[30:36].strip()+
													'\n')

				elif line[:5] == "*A VE":
					fplanFahrtAVE_strIO.write(self.__fkdict["fk_eckdatenid"]+';'
													  +self.__fkdict["fk_fplanfahrtid"]+';'
													  +line[6:13].strip()+';'
													  +line[14:21].strip()+';'
													  +line[22:28].strip()+';'
													  +line[29:35].strip()+';'
													  +line[36:42].strip()+
													  '\n')

				elif line[:2] == "*A":
					fplanFahrtA_strIO.write(self.__fkdict["fk_eckdatenid"]+';'
													+self.__fkdict["fk_fplanfahrtid"]+';'
													+line[3:5].strip()+';'
													+line[6:13].strip()+';'
													+line[14:21].strip()+';'
													+line[22:28].strip()+';'
													+line[29:35].strip()+';'
													+line[36:42].strip()+
													'\n')

				elif line[:2] == "*R":
					fplanFahrtR_strIO.write(self.__fkdict["fk_eckdatenid"]+';'
													+self.__fkdict["fk_fplanfahrtid"]+';'
													+line[3:4].strip()+';'
													+line[5:12].strip()+';'
													+line[13:20].strip()+';'
													+line[21:28].strip()+';'
													+line[29:35].strip()+';'
													+line[36:42].strip()+
													'\n')
				elif line[:2] == "*I":
					fplanFahrtI_strIO.write(self.__fkdict["fk_eckdatenid"]+';'
													+self.__fkdict["fk_fplanfahrtid"]+';'
													+line[3:5].strip()+';'
													+line[29:36].strip()+';'
													+line[6:13].strip()+';'
													+line[14:21].strip()+';'
													+line[22:28].strip()+';'
													+line[37:43].strip()+';'
													+line[44:50].strip()+
													'\n')

				elif line[:2] == "*L":
					fplanFahrtL_strIO.write(self.__fkdict["fk_eckdatenid"]+';'
													+self.__fkdict["fk_fplanfahrtid"]+';'
													+line[3:11].strip()+';'
													+line[12:19].strip()+';'
													+line[20:27].strip()+';'
													+line[28:34].strip()+';'
													+line[35:41].strip()+
													'\n')
			else:
				# Datenzeilen
				bDataLinesRead = True
				fplanFahrtLauf_strIO.write(self.__fkdict["fk_eckdatenid"]+';'
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


		# Nach dem Durchlauf der Schleife ist noch ein Zug nicht gespeichert
		if bDataLinesRead:
			# Datenzeilen wurden gelesen, wir sind jetzt wieder beim nächsten Zug und schreiben den Vorgänger erstmal in die DB
			fplanFahrtG_strIO.seek(0)
			fplanFahrtAVE_strIO.seek(0)
			fplanFahrtLauf_strIO.seek(0)
			cur = self.__hrdfdb.connection.cursor()
			cur.copy_expert("COPY HRDF_FPLANFahrtG_TAB (fk_eckdatenid,fk_fplanfahrtid,categorycode,fromStop,toStop,deptimeFrom,arrtimeFrom) FROM STDIN USING DELIMITERS ';' NULL AS ''", fplanFahrtG_strIO)
			cur.copy_expert("COPY HRDF_FPLANFahrtVE_TAB (fk_eckdatenid,fk_fplanfahrtid,fromStop,toStop,bitfieldno,deptimeFrom,arrtimeFrom) FROM STDIN USING DELIMITERS ';' NULL AS ''", fplanFahrtAVE_strIO)
			cur.copy_expert("COPY HRDF_FPLANFahrtLaufweg_TAB (fk_eckdatenid,fk_fplanfahrtid,stopno,stopname,sequenceno,arrtime,deptime,tripno,operationalno,ontripsign) FROM STDIN USING DELIMITERS ';' NULL AS ''", fplanFahrtLauf_strIO)
			if fplanFahrtA_strIO.tell() > 0:
				fplanFahrtA_strIO.seek(0)
				cur.copy_expert("COPY HRDF_FPLANFahrtA_TAB (fk_eckdatenid,fk_fplanfahrtid,attributecode,fromStop,toStop,bitfieldno,deptimeFrom,arrtimeFrom) FROM STDIN USING DELIMITERS ';' NULL AS ''", fplanFahrtA_strIO)
			if fplanFahrtR_strIO.tell() > 0:
				fplanFahrtR_strIO.seek(0)
				cur.copy_expert("COPY HRDF_FPLANFahrtR_TAB (fk_eckdatenid,fk_fplanfahrtid,directionshort,directioncode,fromStop,toStop,deptimeFrom,arrtimeFrom) FROM STDIN USING DELIMITERS ';' NULL AS ''", fplanFahrtR_strIO)
			if fplanFahrtI_strIO.tell() > 0:
				fplanFahrtI_strIO.seek(0)
				cur.copy_expert("COPY HRDF_FPLANFahrtI_TAB (fk_eckdatenid,fk_fplanfahrtid,infotextcode,infotextno,fromStop,toStop,bitfieldno,deptimeFrom,arrtimeFrom) FROM STDIN USING DELIMITERS ';' NULL AS ''", fplanFahrtI_strIO)
			if fplanFahrtL_strIO.tell() > 0:
				fplanFahrtL_strIO.seek(0)
				cur.copy_expert("COPY HRDF_FPLANFahrtL_TAB (fk_eckdatenid,fk_fplanfahrtid,lineno,fromStop,toStop,deptimeFrom,arrtimeFrom) FROM STDIN USING DELIMITERS ';' NULL AS ''", fplanFahrtL_strIO)
		
			self.__hrdfdb.connection.commit()

			fplanFahrtG_strIO.close()
			fplanFahrtAVE_strIO.close()
			fplanFahrtLauf_strIO.close()
			fplanFahrtA_strIO.close()
			fplanFahrtR_strIO.close()
			fplanFahrtI_strIO.close()
			fplanFahrtL_strIO.close()


			fplanFahrtG_strIO = StringIO()
			fplanFahrtAVE_strIO = StringIO()
			fplanFahrtLauf_strIO = StringIO()
			fplanFahrtA_strIO = StringIO()
			fplanFahrtR_strIO = StringIO()
			fplanFahrtI_strIO = StringIO()
			fplanFahrtL_strIO = StringIO()

			self.__fkdict["fk_fplanfahrtid"] = -1
			bDataLinesRead = False
			iSequenceCnt = 0


		curIns.close()
