from datetime import datetime

class Logger(object):

    def __init__(self, client, dbname='ccpnc'):

        self.client = client
        logdb = client[dbname]

        self.logs = logdb.databaseLogs

    def log(self, message, orcid, data={}):

        data['message'] = message
        data['orcid'] = orcid
        data['time'] = datetime.utcnow()

        res = self.logs.insert_one(data)

        return res.acknowledged
