import sys
from datetime import date, timedelta
from io import StringIO
from copy import copy
import psycopg2
import codecs
import zipfile
import fileinput
from bitstring import Bits
from operator import itemgetter

charset = 'utf-8'

out = codecs.getwriter('utf-8')(sys.stdout)

dbname = 'hafas_minified'
host = 'xxxxxxxx'
user = 'xxxxxxxx'
password = 'xxxxxxxx'


trips = {}
stops = []
trip_attribute = []
trip_infotexte = []


def clean_date(mydate):
    mydate = mydate.split('.')
    return date(int(mydate[2]), int(mydate[1]), int(mydate[0]))


def check_tripcount():
	# ab einer bestimmten Grösse sollen die trips in die DB geschrieben werden 
	if len(trips) >= 100000:
		write_trips()



def write_trips():

	print('\nschreibe Daten in DB ...')
	trips_string = StringIO()
	stops_string = StringIO()
	attribute_string = StringIO()
	infotexte_string = StringIO()

	for trip in trips.values():
		trips_string.write(trip['id']+';'+trip['datum']+';'+trip['fahrtnummer']+';'+trip['verwaltung']+';'+trip['variante']+';'+str(trip['lw_variante'])+';'+str(trip['attr_variante'])+';'+str(trip['info_variante'])+'\n')

	for stop in stops:
		stops_string.write(str(stop['trip_id'])+';'
							+str(stop['lw_variante'])+';'
							+str(stop['sequenznummer'])+';'
							+stop['liniennummer']+';'
							+stop['hstnummer']+';'
							+stop['hstname']+';'
							+stop['ankunftszeit']+';'
							+stop['abfahrtszeit']+';'
							+stop['aussteigeverbot']+';'
							+stop['einsteigeverbot']+';'
							+stop['richtungsID']+';'
							+stop['richtung']+';'
							+stop['verkehrsmittel']+';'
							+stop['fahrtnummer']+';'
							+stop['verwaltung']+';'
							+stop['x']
							+'\n')

	for attribut in trip_attribute:
		attribute_string.write(str(attribut['trip_id'])+';'
								+str(attribut['attr_variante'])+';'
								+str(attribut['sequenznummer'])+';'
								+str(attribut['attributscode'])
								+'\n')


	for infotext in trip_infotexte:
		infotexte_string.write(str(infotext['trip_id'])+';'
								+str(infotext['info_variante'])+';'
								+str(infotext['sequenznummer'])+';'
								+infotext['infotextcode']+';'
								+infotext['infotextnummer']
								+'\n')



	trips_string.seek(0)
	stops_string.seek(0)
	attribute_string.seek(0)
	infotexte_string.seek(0)

	conn = psycopg2.connect('host='+host+' dbname='+dbname+' user='+user+' password='+password)

	cur = conn.cursor()
	cur.copy_expert("COPY trips (trip_id,datum,fahrtnummer,verwaltung,variante,lw_variante,attr_variante,info_variante) FROM STDIN USING DELIMITERS ';' NULL AS ''",trips_string)
	cur.copy_expert("COPY stops (trip_id,lw_variante,sequenznummer,liniennummer,hstnummer,hstname,ankunftszeit,abfahrtszeit,aussteigeverbot,einsteigeverbot,richtungsid,richtung,verkehrsmittel,fahrtnummer,verwaltung,x) FROM STDIN USING DELIMITERS ';' NULL AS ''",stops_string)
	cur.copy_expert("COPY trip_attribute (trip_id,attr_variante,sequenznummer,attributscode) FROM STDIN USING DELIMITERS ';' NULL AS ''",attribute_string)
	cur.copy_expert("COPY trip_infotexte (trip_id,info_variante,sequenznummer,infotextcode,infotextnummer) FROM STDIN USING DELIMITERS ';' NULL AS ''",infotexte_string)

	conn.commit()
	cur.close()
	trips_string.close()
	stops_string.close()
	attribute_string.close()
	infotexte_string.close()

	print(str(len(trips))+' trips in DB geschrieben')
	print(str(len(stops))+' stops in DB geschrieben')
	print(str(len(trip_attribute))+' Attribute in DB geschrieben')
	print(str(len(trip_infotexte))+' Infotexte in DB geschrieben')
	# nach dem schreiben werden alle dictionaries zurückgesetzt
	trips.clear()
	stops.clear()
	trip_attribute.clear()
	trip_infotexte.clear()

def get_eckdaten(hrdfzip,file):
	print('lese und verarbeite Eckdaten ...')
 	# spezifisch für SBB-Version 
	lines = hrdfzip.read(file).decode(charset).split('\r\n')[:-1]
	eckdaten = {}
	eckdaten['fpstart'] = clean_date(lines[0])
	eckdaten['fpende'] = clean_date(lines[1])
	eckdaten['fpende'] = eckdaten['fpstart'] + timedelta(days=30) # Zeile kann entfernt werden, wenn Fahrplanjahr vollständig erfasst werden soll. Achtung: grosse Datenmengen!    
	bezeichnung,exportdatum,hrdfversion,lieferant = lines[2].split('$')
	eckdaten['bezeichnung'] = bezeichnung
	eckdaten['exportdatum'] = exportdatum
	eckdaten['hrdfversion'] = hrdfversion
	eckdaten['lieferant'] = lieferant
	return eckdaten


def get_verkehrstage(hrdfzip,file,eckdaten):
	print('lese und verarbeite Verkehrstage ...')
	verkehrstage = {}
	for line in fileinput.input(file, openhook=hrdfzip.open):
		line = line.decode(charset).replace('\r', '').replace('\n', '')
		bitfeldnummer = line[:6]
		bitfeld = {'bitfeldnummer' : bitfeldnummer,'verkehrstage' : []}
		bitfeld_bits = str(Bits(hex=line[7:]).bin)
		# die ersten zwei Bits sind aus "technischen Gründen" mit "1" gefüllt und nicht zu berücksichtigen
		for b in range(2, len(bitfeld_bits)):
			if bitfeld_bits[b] == '1':
				current_date = eckdaten['fpstart']  + timedelta(days=b-2)
				if current_date <= eckdaten['fpende']:
					bitfeld['verkehrstage'].append(current_date)
		verkehrstage[bitfeldnummer] = bitfeld
	# für fehlende Verkehrstagenummer finden die Fahrten täglich statt, hierfür wird eine bitfeldnummer '0' verwendet
	bitfeld = {'bitfeldnummer' : '0', 'verkehrstage' : []}
	i = eckdaten['fpstart']
	while i <= eckdaten['fpende']:
		bitfeld['verkehrstage'].append(i)
		i += timedelta(days=1)
	verkehrstage[0] = bitfeld    
	return verkehrstage


def get_richtungen(hrdfzip,file):
	print('lese und verarbeite Richtungen ...')
	richtungen = {}
	for line in fileinput.input(file, openhook=hrdfzip.open):
		line = line.decode(charset).replace('\r', '').replace('\n', '')
		richtungen[line[:7]] = line[8:59]
	return richtungen


def get_bahnhoefe(hrdfzip,file):
	print('lese und verarbeite Bahnhöfe ...')
	bahnhoefe = []
	for line in fileinput.input(file, openhook=hrdfzip.open):
		line = line.decode(charset).replace('\r', '').replace('\n', '')
		bahnhof = {'didoknr':line[:7],'hstname':line[8:]} # <-- ToDo: Aufschlüsseln der Haltestellennamen (Varianten/Synonyme)
		bahnhoefe.append(bahnhof)
	return bahnhoefe


def handle_zugart(hrdfzip,file):
	print('lese und verarbeite Zugarten ...')
	zugarten_string = StringIO()
	categories_string = StringIO()
	classes_string = StringIO()
	options_string = StringIO()
	language = None
	text = False
	for line in fileinput.input(file, openhook=hrdfzip.open):
		line = line.decode(charset).replace('\r', '').replace('\n', '')
		# Eine Zeile mit dem Inhalt "<text>" gibt an, dass nun nur noch die Textangaben in verschiedenen Sprachen folgen
		if not text:
			# solange das nicht der Fall ist, sollen die Daten als Zugarten weiter eingearbeitet werden
			if not line == '<text>':
				# Der string setzt sich aus folgenden Elementen zusammen: code,produktklasse,tarifgruppe,ausgabesteuerung,gattungsbezeichnung,zuschlag,flag,gattungsbildernamen,kategorienummer
				zugarten_string.write(line[:3]+';'+str(int(line[4:6]))+';'+line[7:8]+';'+line[9:10]+';'+line[11:19].strip()+';'+line[20:21].strip()+';'+line[22:23]+';'+line[24:28].strip()+';'+line[30:33].lstrip('0')+'\n')
			# sobald die Textangaben beginnen, werden die Daten sprachspezifisch in das jeweilige dictionary geschrieben
			else:
				text = True
		elif line[0] == '<':
			language = line[1:-1].lower()
		elif line[:8] == 'category':
			categories_string.write(line[8:11].lstrip('0')+';'+language+';'+line[12:]+'\n')
		elif line[:6] == 'option':
			options_string.write(line[6:8]+';'+language+';'+line[9:]+'\n')
		elif line[:5] == 'class':
			classes_string.write(str(int(line[5:7]))+';'+language+';'+line[8:]+'\n')

	zugarten_string.seek(0)
	categories_string.seek(0)
	options_string.seek(0)
	classes_string.seek(0)

	#Daten in die DB schreiben
	print('schreibe Zugarten in DB ...')
	conn = psycopg2.connect("host="+host+" dbname="+dbname+" user="+user+" password="+password)

	cur = conn.cursor()
	cur.copy_expert("COPY zugarten (code,produktklasse,tarifgruppe,ausgabesteuerung,gattungsbezeichnung,zuschlag,flag,gattungsbildernamen,kategorienummer) FROM STDIN USING DELIMITERS ';' NULL AS ''",zugarten_string)
	cur.copy_expert("COPY zugart_kategorien (code,sprache,kategorie) FROM STDIN USING DELIMITERS ';' NULL AS ''",categories_string)	
	cur.copy_expert("COPY zugart_optionen (code,sprache,option) FROM STDIN USING DELIMITERS ';' NULL AS ''",options_string)
	cur.copy_expert("COPY zugart_klassen (code,sprache,klasse) FROM STDIN USING DELIMITERS ';' NULL AS ''",classes_string)
	conn.commit()
	cur.close()
	zugarten_string.close()
	categories_string.close()
	options_string.close()
	classes_string.close()


def handle_attribute(hrdfzip,file):
	print('lese und verarbeite Attribute ...')
	attribute_string = StringIO()

	for line in fileinput.input(file, openhook=hrdfzip.open):
		line = line.decode(charset).replace('\r', '').replace('\n', '')
		if not line[:1] == '#':															# <-- ToDo: Auch Zeilen beginnend mit "#" müssen eingearbeitet werden
			attribute_string.write( line[:2]+';'
									+line[3:4]+';'
									+line[5:8]+';'
									+line[9:11]+';'
									+line[12:-1].replace(';','\;')+
									'\n')

	attribute_string.seek(0)

	print('schreibe Attribute in DB ...')
	conn = psycopg2.connect("host="+host+" dbname="+dbname+" user="+user+" password="+password)

	cur = conn.cursor()
	cur.copy_expert("COPY attribute (code,hstzugehoerigkeit,ausgabeprio,feinsortierung,attributsklartext) FROM STDIN USING DELIMITERS ';' NULL AS ''",attribute_string)
	conn.commit()
	cur.close()
	attribute_string.close()


def handle_infotexte(hrdfzip,file):
	print('lese und verarbeite Infotexte ...')
	infotexte_string = StringIO()

	for line in fileinput.input(file, openhook=hrdfzip.open):
		line = line.decode(charset).replace('\r', '').replace('\n', '')
		infotexte_string.write( line[:7]+';'
								+line[9:].replace(';','\;')
								+'\n')

	infotexte_string.seek(0)

	print('schreibe Infotexte in DB ...')
	conn = psycopg2.connect("host="+host+" dbname="+dbname+" user="+user+" password="+password)

	cur = conn.cursor()
	cur.copy_expert("COPY infotexte (infotextnummer,infotext) FROM STDIN USING DELIMITERS ';' NULL AS ''",infotexte_string)
	conn.commit()
	cur.close()
	infotexte_string.close()




def handle_fplan(hrdfzip,file,verkehrstage,richtungen):
	current_trip = {}

	for line in fileinput.input(file, openhook=hrdfzip.open):
		line = line.decode(charset).replace('\r', '').replace('\n', '')

		if line[:2] == '*Z':

        # wenn bereits Fahrten vorhanden sind, sind mit der neuen *Z-Zeile die Informationen dazu vollständig vorhanden und müssen nun noch verarbeitet werden
			if len(current_trip) > 0:
				generate_trips(current_trip, verkehrstage, richtungen)
				current_trip = {}

        	# die neue *Z-Zeile wird nun bearbeitet
        	# die Laufwegsequenznummer wird zurückgesetzt, weil eine neue Fahrt verarbeitet wird
			lw_seqno = 0

			current_trip['id'] = fileinput.lineno()
			current_trip['fahrtnummer'] = line[3:8].strip()
			current_trip['verwaltung'] = line[9:15].strip()
			current_trip['variante'] = line[18:21].strip()
			current_trip['taktanzahl'] = line[22:25].strip()
			current_trip['taktzeit'] = line[26:29].strip()
			current_trip['aves'] = []
			current_trip['gs'] = []
			current_trip['as'] = []
			current_trip['is'] = []
			current_trip['ls'] = []
			current_trip['rs'] = []
			current_trip['route'] = []

			print('\rbearbeite Fahrtnummer '+current_trip['fahrtnummer']+' von Verwaltung '+current_trip['verwaltung']+' mit Variante '+current_trip['variante']+' aus Zeile '+str(current_trip['id']), end="", flush=True)

		elif line[:5] == '*A VE':
			ave = { 'laufwegsindexab': line[6:13].strip(),
					'laufwegsindexbis': line[14:21].strip(),
					'verkehrstagenummer': line[22:28].strip(),
					'indexab': line[29:35].strip(),
					'indexbis': line[36:42].strip() }
			if ave['verkehrstagenummer'] == '':
				ave['verkehrstagenummer'] = 0                 
			current_trip['aves'].append(ave)

		elif line[:2] == '*T':
			# gemäss Realisierungsvorgaben nicht unterstützt
			pass 

		elif line[:2] == '*G':
			g = {	'verkehrsmittel': line[3:6].strip(),
					'laufwegsindexab': line[7:14].strip(),
					'laufwegsindexbis': line[15:22].strip(),
					'indexab': line[23:29].strip(),
					'indexbis': line[30:36].strip() }
			current_trip['gs'].append(g)

		elif line[:2] == '*A':
			a = {	'attributscode': line[3:5].strip(),
					'laufwegsindexab': line[6:13].strip(),
					'laufwegsindexbis': line[14:21].strip(),
					'bitfeldnummer': line[22:28].strip(),
					'indexab': line[29:35].strip(),
					'indexbis': line[36:42].strip() }
			if a['bitfeldnummer'] == '':
				a['bitfeldnummer'] = 0					
			current_trip['as'].append(a)

		elif line[:2] == '*I':
			i = {	'infotextcode': line[3:5].strip(),
					'laufwegsindexab': line[6:13].strip(),
					'laufwegsindexbis': line[14:21].strip(),
					'bitfeldnummer': line[22:28].strip(),
					'infotextnummer': line[29:36].strip(),
					'indexab': line[37:43].strip(),
					'indexbis': line[44:50].strip() }
			if i['bitfeldnummer'] == '':
				i['bitfeldnummer'] = 0	
			current_trip['is'].append(i)

		elif line[:2] == '*L':
			l = {	'liniennummer': line[3:11].strip(),
					'laufwegsindexab': line[12:19].strip(),
					'laufwegsindexbis': line[20:27].strip(),
					'indexab': line[28:34].strip(),
					'indexbis': line[35:41].strip() }
			current_trip['ls'].append(l)

		elif line[:2] == '*R':
			r = {	'kennung': line[3:4].strip(),
					'richtungscode': line[5:12].strip(),
					'laufwegsindexab': line[13:20].strip(),
					'laufwegsindexbis': line[21:28].strip(),
					'indexab': line[29:35].strip(),
					'indexbis': line[36:42].strip() }
			current_trip['rs'].append(r)

		elif line[:3] == '*GR':
			pass

		elif line[:3] == '*SH':
			pass

		elif line[:3] == '*CI':
			pass

		elif line[:3] == '*CO':
			pass

		elif line[:3] == '*KW':
			# Achtung, hier muss noch zwischen *KW und *KWZ unterschieden werden
			pass

		else:
			# alle anderen Zeilen sind Laufwegszeilen
			# hier werden Regionen noch nicht berücksichtigt (Zeilen beginnen mit "+")
			lw = { 'sequenznummer': lw_seqno,
				'liniennummer': '', #wird leer eingefügt, damit der Schlüssel vorhanden ist
				'hstnummer': line[:7].strip(),
				'hstname': line[8:29].strip(),
				'ankunftszeit': line[30:35].strip(),
				'abfahrtszeit': line[37:42].strip(),
				'aussteigeverbot': ('true' if line[29:30].strip() == '-' else ''),
				'einsteigeverbot': ('true' if line[36:37].strip() == '-' else ''),
				'richtungsID': '', #wird leer eingefügt, damit der Schlüssel vorhanden ist
				'richtung': '', #wird leer eingefügt, damit der Schlüssel vorhanden ist
				'verkehrsmittel': '', #wird leer eingefügt, damit der Schlüssel vorhanden ist
				'fahrtnummer': line[44:48].strip(),
				'verwaltung': line[49:55].strip(),
				'x': line[56:57].strip() }

			lw_seqno += 1
			current_trip['route'].append(lw)

	# Für die letzte "*Z"-Zeile kann das Verarbeiten nicht mit Erkennen der nächsten *Z-Zeile angestossen werden und muss im Anschluss an den Loop separat initiiert werden
	generate_trips(current_trip, verkehrstage, richtungen)
	current_trip = {}


# Aufbereiten der Daten aus den verschiedenen Linientypen
# dabei müssen die unterschiedlichen Gültigkeiten berücksichtigt werden, wobei sich die Gültigkeiten mehrerer Zeilen gleichen Typs auch überschneiden/ergänzen können
def generate_trips(current_trip, verkehrstage, richtungen):
	indexdict = {}

	# Bearbeiten aller "*L"-Zeilen ######################################################################		<-- ToDo: Das Bestimmen des ersten und letzten Halts der Gültigkeit wiederholt sich für mehrere Zeilentypen und kann in eine eigene Funktion ausgelagert werden
	for l in current_trip['ls']:
		# Bestimmen des Gültigkeitsbereichs für die L-Angabe
		# Ist Laufwegsindexab nicht gesetzt, gilt die Angabe ab dem ersten Halt
		if l['laufwegsindexab'] == '':
			l_ab = 0
		# Ist Laufwegsindexab gesetzt, wird im Laufweg von vorn nach der passenden Haltestelle gesucht	
		else:
			for stop in current_trip['route']:
				if l['laufwegsindexab'] == stop['hstnummer']:
					l_ab = stop['sequenznummer']
					break
		# Ist Laufwegsindexbis nicht gesetzt, gilt die Angabe bis zur letzten Haltestelle
		if l['laufwegsindexbis'] == '':
			l_bis = len(current_trip['route']) -1
		# Ist Laufwegsindexbis gesetzt, wird im Laufweg von hinten nach der zugehörigen Haltestelle gesucht
		else:
			for stop in reversed(current_trip['route']):
				if l['laufwegsindexbis'] ==	stop['hstnummer']:
					l_bis = stop['sequenznummer']
					break

		# Hinzufügen der L-Angabe zu allen Haltestellen des Laufwegs, die im Gültigkeitsbereich liegen			<-- ToDo: Entspricht die gültigkeit dem gesamten Fahrweg, könnte die Information auch auf Ebene Fahrt abgelegt werden, statt auf Ebene Halt
		x = l_ab
		while x <= l_bis:
			current_trip['route'][x].update({'liniennummer':l['liniennummer']})
			x += 1
	# "*L"-Zeilen eingearbeitet


	# Bearbeiten aller "*R"-Zeilen ######################################################################
	for r in current_trip['rs']:
		# enthält die "*R"-Zeile keine weiteren Angaben, ist der Name der letzten Haltestelle des Laufwegs als Richtung zu verwenden
		if (r['kennung'] == '' and r['richtungscode'] == '' and r['laufwegsindexab'] == '' and r['laufwegsindexbis'] == '' and r['indexab'] == '' and r['indexbis'] == ''):
			r_ab = 0
			r_bis = len(current_trip['route']) -1
			richtung = current_trip['route'][r_bis]['hstnummer'] # liefert die didoknr der letzten Haltestelle im Laufweg <-- ToDo: ersetzen durch Name aus BAHNHOF-File
		# enthält die "*R"-Zeile weitere Angaben, müssen diese verarbeitet werden
		else:
			richtung = richtungen[r['richtungscode']]
		# Ist Laufwegsindexab nicht gesetzt, gilt die Angabe ab dem ersten Halt
			if r['laufwegsindexab'] == '':
				r_ab = 0
		# Ist Laufwegsindexab gesetzt, wird im Laufweg von vorn nach der passenden Haltestelle gesucht
			else:
				for stop in current_trip['route']:
					if r['laufwegsindexab'] == stop['hstnummer']:
						r_ab = stop['sequenznummer']
						break

		# Ist Laufwegsindexbis nicht gesetzt, gilt die Angabe bis zur letzten Haltestelle
			if r['laufwegsindexbis'] == '':
				r_bis = len(current_trip['route']) -1
		# Ist Laufwegsindexbis gesetzt, wird im Laufweg von hinten nach der zugehörigen Haltestelle gesucht
			else:
				for stop in reversed(current_trip['route']):
					if r['laufwegsindexbis'] ==	stop['hstnummer']:
						r_bis = stop['sequenznummer']
						break

		# Hinzufügen der R-Angabe zu allen Haltestellen des Laufwegs, die im Gültigkeitsbereich liegen
		x = r_ab
		while x <= r_bis:
			current_trip['route'][x].update({'richtungsID':r['kennung'],'richtung':richtung})
			x += 1
	# "*R"-Zeilen eingearbeitet


	# Bearbeiten aller "*G"-Zeilen ######################################################################
	for g in current_trip['gs']:
		# Ist Laufwegsindexab nicht gesetzt, gilt die Angabe ab dem ersten Halt
		if g['laufwegsindexab'] == '':
			g_ab = 0
		# Ist Laufwegsindexab gesetzt, wird im Laufweg von vorn nach der passenden Haltestelle gesucht
		else:
			for stop in current_trip['route']:
				if g['laufwegsindexab'] == stop['hstnummer']:
					g_ab = stop['sequenznummer']
					break

		# Ist Laufwegsindexbis nicht gesetzt, gilt die Angabe bis zur letzten Haltestelle
		if g['laufwegsindexbis'] == '':
			g_bis = len(current_trip['route']) -1
		# Ist Laufwegsindexbis gesetzt, wird im Laufweg von hinten nach der zugehörigen Haltestelle gesucht
		else:
			for stop in reversed(current_trip['route']):
				if g['laufwegsindexbis'] ==	stop['hstnummer']:
					g_bis = stop['sequenznummer']
					break
		# Hinzufügen der G-Angabe zu allen Haltestellen des Laufwegs, die im Gültigkeitsbereich liegen
		x = g_ab
		while x <= g_bis:
			current_trip['route'][x].update({'verkehrsmittel':g['verkehrsmittel']})
			x += 1


	# Bearbeiten aller "*A"-Zeilen ###################################################################
	for a in current_trip['as']:
		# Bestimmen der Haltestellen im Laufweg, die für diese Gültigkeit berücksichtigt werden müssen <-- ToDo: hier müssen noch weitere Elemente ausgewertet werden (laufwegsindex mit '#' gekennzeichnet, index ..), leere Felder beim Bahnhof stehen für die erste bzw. letzte Bahnhofsnummer des Laufwegs
		# Die "Ab"-Haltestelle wird im Laufweg von vorn gesucht
		if a['laufwegsindexab'] == '':
			a['a_ab'] = 0
		else:
			for stop in current_trip['route']:
					if a['laufwegsindexab'] == stop['hstnummer']:
						a['a_ab'] = stop['sequenznummer']
						break

		# Die "Bis"-Haltestelle wird im Laufweg von hinten gesucht
			if a['laufwegsindexbis'] == '':
				a['a_bis'] = len(current_trip['route']) -1
			else:
				for stop in reversed(current_trip['route']):
					if a['laufwegsindexbis'] == stop['hstnummer']:	
						a['a_bis'] = stop['sequenznummer']
						break


	# Bearbeiten aller "*I"-Zeilen ###################################################################
	for i in current_trip['is']:
		# Bestimmen der Haltestellen im Laufweg, die für diese Gültigkeit berücksichtigt werden müssen <-- ToDo: hier müssen noch weitere Elemente ausgewertet werden (laufwegsindex mit '#' gekennzeichnet, index ..), leere Felder beim Bahnhof stehen für die erste bzw. letzte Bahnhofsnummer des Laufwegs
		# Die "Ab"-Haltestelle wird im Laufweg von vorn gesucht
		if i['laufwegsindexab'] == '':
			i['i_ab'] = 0
		else:
			for stop in current_trip['route']:
					if i['laufwegsindexab'] == stop['hstnummer']:
						i['i_ab'] = stop['sequenznummer']
						break

		# Die "Bis"-Haltestelle wird im Laufweg von hinten gesucht
		if i['laufwegsindexbis'] == '':
			i['i_bis'] = len(current_trip['route']) -1
		else:
			for stop in reversed(current_trip['route']):
				if i['laufwegsindexbis'] == stop['hstnummer']:	
					i['i_bis'] = stop['sequenznummer']
					break


	# Bearbeiten aller "*A VE"-Zeilen ###################################################################
	for ave in current_trip['aves']:
		# Bestimmen der Haltestellen im Laufweg, die für diese Gültigkeit berücksichtigt werden müssen <-- ToDo: hier müssen noch weitere Elemente ausgewertet werden (laufwegsindex mit '#' gekennzeichnet, index ..), leere Felder beim Bahnhof stehen für die erste bzw. letzte Bahnhofsnummer des Laufwegs
		# Die "Ab"-Haltestelle wird im Laufweg von vorn gesucht
		for stop in current_trip['route']:
			if ave['laufwegsindexab'] == stop['hstnummer']:
				ave_ab = stop['sequenznummer']
				break
		# Die "Bis"-Haltestelle wird im Laufweg von hinten gesucht
		for stop in reversed(current_trip['route']):
			if ave['laufwegsindexbis'] == stop['hstnummer']:	
				ave_bis = stop['sequenznummer']
				break

		current_stops = []
		
		x = ave_ab
		while x <= ave_bis:
			current_stops.append(current_trip['route'][x])
			x += 1

		# für jeden Verkehrstag werden die betroffenen Halte zum Laufweg hinzugefügt
		for vtag in verkehrstage[ave['verkehrstagenummer']]['verkehrstage']:
			index = str(vtag).replace('-','')+'-'+str(current_trip['id'])
			indexdict[index] = index

			if not index in trips:
				trips[index] = {}			
				trip = {'id': str(current_trip['id']),
						'datum': str(vtag),
						'fahrtnummer': current_trip['fahrtnummer'],
						'verwaltung': current_trip['verwaltung'],
						'variante': current_trip['variante']}			
				trips[index] = trip

			if not 'stops_tmp' in trips[index]:
				trips[index]['stops_tmp'] = {}

			for stop in current_stops:
				trips[index]['stops_tmp'][stop['sequenznummer']] = stop.copy()
				trips[index]['stops_tmp'][stop['sequenznummer']]['attribute'] = [] # zum Aufnehmen eventuell vorhandener Attribute
				trips[index]['stops_tmp'][stop['sequenznummer']]['infotexte'] = [] # zum Aufnehmen eventuell vorhandener Infotexte

			# Einarbeiten der Attribute pro Verkehrstag und Halt 
				for a in current_trip['as']:
					if vtag in verkehrstage[a['bitfeldnummer']]['verkehrstage']:
						if stop['sequenznummer'] >= a['a_ab'] and stop['sequenznummer'] <= a['a_bis']:
							trips[index]['stops_tmp'][stop['sequenznummer']]['attribute'].append(a['attributscode'])

			# Einarbeiten der Infotexte pro Verkehrstag und Halt
				for i in current_trip['is']:
					if vtag in verkehrstage[i['bitfeldnummer']]['verkehrstage']:
						if stop['sequenznummer'] >= i['i_ab'] and stop['sequenznummer'] <= i['i_bis']:
							trips[index]['stops_tmp'][stop['sequenznummer']]['infotexte'].append(i['infotextcode']+':'+i['infotextnummer'])



		current_stops = []
		index = None

	# Die Laufwege müssen noch bereinigt werden. Erste Halte haben z.B. keine Ankunftszeit, letzte keine Abfahrtszeit, die Seqeunznummern sollten ausserdem wieder bei "0" beginnen.
	# Das sollte passieren, nachdem alle "*A VE"-Zeilen verarbeitet sind, da sie sich gegenseitig ergänzen können.
	# Die unterschiedlichen Ausprägungen der Laufwege und Attribute werden erfasst und ihre Nummer dem Trip für diesen Tag zugeordnet
	lw_varianten = {}
	attr_varianten = {}
	info_varianten = {}
	lw_var_counter = 0
	attr_var_counter = 0
	info_var_counter = 0
	for index in indexdict.values():
		lw_variante = {}
		attr_variante = {}
		info_variante = {}
		x = 0
		for stop in trips[index]['stops_tmp'].values():
			lw_variante[x] = stop.copy()
			attr_variante[x] = lw_variante[x]['attribute'].copy()
			del lw_variante[x]['attribute']
			info_variante[x] = lw_variante[x]['infotexte'].copy()
			del lw_variante[x]['infotexte']
			lw_variante[x]['sequenznummer'] = x
			x += 1
		
		lw_variante[0]['ankunftszeit'] = ''
		lw_variante[0]['aussteigeverbot'] = ''
		lw_variante[x-1]['abfahrtszeit'] = ''
		lw_variante[x-1]['einsteigeverbot'] = ''

		# besteht diese Ausprägung des Laufwegs bereits oder muss eine neue Variante gespeichert werden?
		if lw_var_counter > 0:
			match = False
			for key, variante in lw_varianten.items():
				if hash(frozenset(lw_variante[0].items())) == hash(frozenset(variante[0].items())) and hash(frozenset(lw_variante[x-1].items())) == hash(frozenset(variante[len(variante)-1].items())):
					trips[index]['lw_variante'] = key
					match = True
					break
			if not match:
				lw_var_counter += 1
				lw_varianten[lw_var_counter] = lw_variante
				trips[index]['lw_variante'] = lw_var_counter
		else:
			lw_var_counter += 1
			lw_varianten[lw_var_counter] = lw_variante
			trips[index]['lw_variante'] = lw_var_counter

		# besteht diese Ausprägung der Attribute pro Halt bereits oder muss eine neue Variante gespeichert werden?
		if attr_var_counter > 0:
			match = False
			for key, variante in attr_varianten.items():
				if hash(frozenset(attr_variante[0])) == hash(frozenset(variante[0])) and hash(frozenset(attr_variante[x-1])) == hash(frozenset(variante[len(variante)-1])):
					trips[index]['attr_variante'] = key
					match = True
					break
			if not match:
				attr_var_counter += 1
				attr_varianten[attr_var_counter] = attr_variante
				trips[index]['attr_variante'] = attr_var_counter
		else:
			attr_var_counter += 1
			attr_varianten[attr_var_counter] = attr_variante
			trips[index]['attr_variante'] = attr_var_counter

		# besteht diese Ausprägung der Infotexte pro Halt bereits oder muss eine neue Variante gespeichert werden?
		if info_var_counter > 0:
			match = False
			for key, variante in info_varianten.items():
				if hash(frozenset(info_variante[0])) == hash(frozenset(variante[0])) and hash(frozenset(info_variante[x-1])) == hash(frozenset(variante[len(variante)-1])):
					trips[index]['info_variante'] = key
					match = True
					break
			if not match:
				info_var_counter += 1
				info_varianten[info_var_counter] = info_variante
				trips[index]['info_variante'] = info_var_counter
		else:
			info_var_counter += 1
			info_varianten[info_var_counter] = info_variante
			trips[index]['info_variante'] = info_var_counter

		del trips[index]['stops_tmp']

	# die verschiedenen Varianten für Laufwege müssen in die entsprechenden dictionaries geschrieben werden
	for lw_key,lw_value in lw_varianten.items():
		for stop_key,stop_value in lw_value.items():
			temp = stop_value.copy()
			temp.update({'trip_id':current_trip['id'],'lw_variante':lw_key})
			stops.append(temp)

	# die verschiedenen Varianten für Attribute müssen in die entsprechenden dictionaries geschrieben werden
	for var_key,var_value in attr_varianten.items():
		for attr_key,attr_value in var_value.items():
			for item in attr_value:
				temp = ({'trip_id':current_trip['id'],'attr_variante':var_key,'sequenznummer':attr_key,'attributscode':item})
				trip_attribute.append(temp)

	# die verschiedenen Varianten für Infotexte müssen in die entsprechenden dictionaries geschrieben werden
	for var_key,var_value in info_varianten.items():
		for info_key,info_value in var_value.items():
			for item in info_value:
				infotextsplit = item.split(":")
				temp = ({'trip_id':current_trip['id'],'info_variante':var_key,'sequenznummer':info_key,'infotextcode':infotextsplit[0],'infotextnummer':infotextsplit[1]})
				trip_infotexte.append(temp)


	check_tripcount()




def load(filename,db):

	dbname = db

	hrdfzip = zipfile.ZipFile(filename,'r')
	hrdffiles = {}
	for name in hrdfzip.namelist():
		hrdffiles[name] = name

	# die verschiedenen Files stehen zum Teil in Abhängigkeit zueinander, zuerst müssen Eckdaten und Bitfelder verarbeitet werden
	eckdaten = get_eckdaten(hrdfzip,hrdffiles['ECKDATEN'])

	verkehrstage = get_verkehrstage(hrdfzip,hrdffiles['BITFELD'],eckdaten)

	richtungen = get_richtungen(hrdfzip,hrdffiles['RICHTUNG'])

	bahnhoefe = get_bahnhoefe(hrdfzip,hrdffiles['BAHNHOF'])

	# Zugarten werden in separate db-tabelle geschrieben und in den Fahrplandaten referenziert
	handle_zugart(hrdfzip,hrdffiles['ZUGART'])

	# Attribute werden in separate db-tabelle geschrieben und in den Fahrplandaten referenziert 
	# hier werden bis auf weiteres nur die deutschsprachigen Attribute aus dem File Attribut_DE berücksichtigt
	handle_attribute(hrdfzip,hrdffiles['ATTRIBUT_DE'])

	# Infotexte werden in separate db-tabelle geschrieben und in den Fahrplandaten referenziert 
	# hier werden bis auf weiteres nur die deutschsprachigen Infotexte aus dem File INFOTEXT_DE berücksichtigt
	handle_infotexte(hrdfzip,hrdffiles['INFOTEXT_DE'])

	# das FPLAN-File enthält die eigentlichen Fahrten
	handle_fplan(hrdfzip,hrdffiles['FPLAN'],verkehrstage,richtungen)

	write_trips()

#	for keys,values in trips.items():
#		print(keys)
#		print(values)


if __name__ == '__main__':
    load(sys.argv[1],sys.argv[2])