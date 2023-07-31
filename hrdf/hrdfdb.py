import psycopg2

class HrdfDB:
	"""
Die Klasse hält Verbindungsinformationen zur Datenbank.
Zudem stellt sie Funktionen zum Handling mit der Datenbank zur Verfügung

HrdfDB(dbname, host, port, user, password)
connect()
	"""
	def __init__(self, dbname, host, port, user, password):
		"""dbname	-	Name der Datenbank
			host		-	IP/Name des Datenbankrechners
			port		-	Port des Datenbankrechners
			user		-	Benutzer
			password	-	Passwort
		"""
		self.dbname = dbname
		self.host = host
		self.port = port
		self.user = user
		self.password = password


	def connect(self):
		"""
Versucht eine Verbindung zur Datenbank herzustellen wenn noch keine Verbindung besteht.
Liefert true wenn eine Verbindung besteht/hergestellt werden konnte ansonsten false
		"""
		connected = False;
		try:
			cur = self.connection.cursor()
			cur.execute('SELECT 1')
			connected = True;
		except:
			connstring = 'host='+self.host+' dbname='+self.dbname+' port='+str(self.port) +' user='+self.user+' password='+self.password+' connect_timeout=800'
			try:
				self.connection = psycopg2.connect(connstring)
				connected = True;
			except:
				connected = False;
				print('\nEs konnte keine Verbindung zur DB hergestellt werden')

		return connected

		



