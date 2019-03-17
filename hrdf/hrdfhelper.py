from datetime import date, timedelta

def to_date(mydate):
	"""Konvertiert ein Datumsstring im Format dd.mm.yyyy in ein Datum"""
	mydate = mydate.split('.')
	return date(int(mydate[2]), int(mydate[1]), int(mydate[0]))

