from datetime import datetime

import logging

# Erzeugen des Loggers
logger = logging.getLogger('HRDF-Reader')
logger.setLevel(logging.DEBUG)

# Handler für das Schreiben der Logausgaben in Datei
logFH = logging.FileHandler('log/hrdfreader.log')
logFH.setLevel(logging.DEBUG)
# Handler für das Schreiben direkt auf die Console
logCH = logging.StreamHandler()
logCH.setLevel(logging.DEBUG)

# Formattierung der Ausgabe
logFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logFH.setFormatter(logFormatter)
logCH.setFormatter(logFormatter)

# Aktivierung der Log-Handler
logger.addHandler(logFH)
logger.addHandler(logCH)
