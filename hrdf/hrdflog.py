from datetime import datetime

import logging

logger = logging.getLogger('HRDF-Reader')
logger.setLevel(logging.DEBUG)
logFH = logging.FileHandler('log/hrdfreader.log')
logFH.setLevel(logging.DEBUG)
logFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logFH.setFormatter(logFormatter)

logger.addHandler(logFH)
