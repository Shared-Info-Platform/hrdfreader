import psycopg2

class HrdfDB:
	"""
Die Klasse hält Verbindungsinformationen zur Datenbank.
Zudem stellt sie Funktionen zum Handling mit der Datenbank zur Verfügung

HrdfDB(dbname, host, user, password)
connect()
	"""
	def __init__(self, dbname, host, user, password):
		"""dbname	-	Name der Datenbank
			host		-	IP/Name des Datenbankrechners
			user		-	Benutzer
			password	-	Passwort
		"""
		self.__dbname = dbname
		self.__host = host
		self.__user = user
		self.__password = password


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
			connstring = 'host='+self.__host+' dbname='+self.__dbname+' user='+self.__user+' password='+self.__password
			try:
				self.connection = psycopg2.connect(connstring)
				connected = True;
			except:
				connected = False;
				print('\nEs konnte keine Verbindung zur DB hergestellt werden')

		return connected

		



