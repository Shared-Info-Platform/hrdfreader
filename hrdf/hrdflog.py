from datetime import datetime

class HrdfLog:
	"""
	Die Klasse dient zum Loggen von Ausgaben in einem festen Format
	Sie stellt unterschiedliche Severity-Level zur Verfügung

	Format der Logzeile:
	<yyyy-MM-dd'T'hh:mm:ss.ssss> - <Sverity-Level> - <message>
	"""

	def info(self, text):
		msgLine = "{} - INFO - {}".format(datetime.now().isoformat(), text)
		print(msgLine)

	def error(self, text):
		msgLine = "{} - ERROR - {}".format(datetime.now().isoformat(), text)
		print(msgLine)

	def warning(self, text):
		msgLine = "{} - WARNING - {}".format(datetime.now().isoformat(), text)
		print(msgLine)


# Einen logger pro importiertem Modul => noch nicht die beste Lösung
logger = HrdfLog()