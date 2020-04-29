from datetime import datetime
from pymongo import MongoClient

class Logger(object):

    def __init__(self, client, logname='ccpnc-log'):

        self.client = client
        logdb = client[logname]

        self.logs = logdb.logs

    def log(self, message, orcid, data={}):

        data['message'] = message
        data['orcid'] = orcid
        data['time'] = datetime.utcnow()

        res = self.logs.insert_one(data)

        return res.acknowledged
