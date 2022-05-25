# Funktionen, Klassen und Defines für das VDV-Protokoll
import datetime
from datetime import timezone
import time
import xml.etree.ElementTree as ET

def vdvTreeElementToBool(treeElement, defaultValue):
	""" Liefert den Wert des treeElements als VDV-Boolean-Wert """
	if (treeElement is None):
		return defaultValue
	else:
		if (treeElement.text.lower() == 'true') or (treeElement.text == '1'):
			return True
		else:
			return False

def vdvToVDVBool(booleanValue):
	""" Wandelt einen boolean-Value in einen VDV boolean """
	if (booleanValue is None): return None
	elif (booleanValue == True): return "true"
	else: return "false"

def vdvStrToBool(strBooleanValue):
	""" Wandelt einen String in einen Bool """
	if (strBooleanValue is None): return None
	elif (strBooleanValue.lower() == 'true') : return True
	return False
	

def vdvStrToDateTimeUTC(strDateTime):
	""" Liefert DateTime-String als VDV-Datetime-Wert (UTC) """
	if (strDateTime is not None):
		if (strDateTime.find('+',18) ==-1 and strDateTime.find('-',18) ==-1):
			if (strDateTime.find('Z',18)>=0): strDateTime = strDateTime[:-1]
			return datetime.datetime.strptime(strDateTime, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
		else:
			# Die Zeit ist als lokale Zeit angegeben => auf UTC zurückrechnen (hier nicht der Weisheit letzter Schluss)
			strDateTime = strDateTime[:18]
			return (datetime.datetime.strptime(strDateTime, '%Y-%m-%dT%H:%M:%S') + (datetime.datetime.utcnow() - datetime.datetime.now())).replace(tzinfo=timezone.utc)
	else:
		return None

def vdvUTCToLocal(utcDateTime):
	""" Wandelt UTC in LocalTime um """
	if (utcDateTime is not None):
		epoch = time.mktime(utcDateTime.timetuple())
		offset = datetime.datetime.fromtimestamp(epoch) - datetime.datetime.utcfromtimestamp(epoch)
		localT = utcDateTime + offset
		return localT	
	else:
		return None

def vdvLocalToUTC(localDateTime):
	""" Wandelt LocalTime in UTC um """
	if (localDateTime is not None):		
		localTimeStamp = localDateTime.timestamp()
		utcT = datetime.datetime.fromtimestamp(localTimeStamp, tz=timezone.utc)
		return utcT
	else:
		return None

def vdvDateTimeFormat(dateTime):
	if (dateTime is not None):
		return dateTime.astimezone().isoformat()
	else:
		return None

def vdvIsEqualElementList(list1, list2, complex):
	""" Prüft ob zwei Element-Listen (complex/simple) gleich sind """
	if (len(list1) == len(list2)):
		listIsEqual = True
		if complex:
			for i in range(len(list1)):
				if list1[i].isEqual(list2[i]) == False:
					listIsEqual = False
					break;
		else:
			for i in range(len(list1)):
				if list1[i] != list2[i]:
					listIsEqual = False
					break;
	else:
		listIsEqual = False

	return listIsEqual