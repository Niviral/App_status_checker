import asyncio
import logging
import sys
from datetime import date, datetime

import requests
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, create_engine


###   Requirements.txt   ###
## asyncio                ##
## requests               ##
## sqlalchemy             ##
## mysql-connector-python ##
############################

logging.basicConfig(filename='OvRuns.log', filemode='a', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S')


PROD: dict={
    
    'PROD' : 'https://search.tme.eu:8443/version',
    'RC' : 'https://rc.search.tme.eu:8443/version',
    'STAGING' :'https://search.staging.tme3c.com:3666/version',
    'DEVEL':'https://search.devel.tme3c.com:3666/version',  ## commented until exeption will be writen
    'TEST':'https://search.test.tme3c.com:3666/version'
}

###SQL engne and table maping
engine = create_engine('mysql+mysqlconnector://hearthbeat:45XEJgQ7@172.16.3.107:3306/Bienias_test')
metadata= MetaData()

hearthbeat = Table('version_hearthbeat', metadata,
    Column('server',String(10)),    
    Column('date_time',DateTime),
    Column('time_diff',String(30)),
    Column('seconds_diff',Integer)
)

class OvRunCheck(object):

    def __init__(self,name: str,server: str, format: str='%Y-%m-%d %H:%M:%S', last_run: str='1920-01-01T00:00:00.000+02:00'):
        """
        Timer class used to check content of remote adress 

        :param name(str): name of server
        :param server(str): HTTP/HTTPS adress used in GET request 
        :param format(str): Default: 'YYYY-MM-DD HH:MM:SS' Format used in .strftime to diplay current time in human form.
        :param last_run(str): Default '1920-01-01 00:00:00' DateTime from which diff will be calulated.
        """
        self.name = name
        self.server = server
        self.format = format
        self.last_run = datetime.fromisoformat(last_run)

    @property
    def current_time(self):
        try:
            response = requests.get(self.server).json()
        except requests.exceptions.SSLError:
            logging.error(f'{self.name} - SSLError  {sys.exc_info()[0]}')
            response = None

        if response:
            current_time = datetime.fromisoformat(response['data_version']['computed_refresh_date'])
        else:
            current_time=datetime.fromisoformat('9999-12-12T00:00:00.000+00:00')
        return current_time

    @property
    def now(self):
        try:
            response = requests.get(self.server).json()
        except requests.exceptions.SSLError:
            logging.error(f'{self.name} - SSLError  {sys.exc_info()[0]}')
            response = None

        if response:
            now = datetime.fromisoformat(response['data_version']['now'])
        else:
            now = datetime.fromisoformat('8999-12-12T00:00:00.000+00:00')
        return now

    def show_time(self):
        string_time = self.current_time.strftime(self.format)
        print(string_time)

    def time_diff(self):
        if self.last_run < self.current_time:
            try:
                diff = self.current_time - self.last_run
                ins = hearthbeat.insert().values(server=self.name, date_time=self.now, time_diff=str(diff), seconds_diff=diff.total_seconds())
                conn = engine.connect()
                insert = conn.execute(ins)
                insert.close()
                logging.info(f'{self.name} - {self.now} - OV run detected, previous run lasted {str(diff)}')
                self.last_run = self.current_time
            except:
                logging.error(f'{self.name} - Unknow error {sys.exc_info()[0]}') 
                #Exeption need to be replace with more specific, currently don't know what can happen here
        else:
            logging.info(f'{self.name} - {self.now} - No run occured, waiting 60s')


serverlist: list = []

print('Application starting')
for server, addr in PROD.items():
    serverlist.append(OvRunCheck(server, addr))

loop = asyncio.get_event_loop()

async def while_loop():
    while True: 
        start = datetime.now()
        for server in serverlist:
            server.time_diff()
        end = datetime.now()
        elaps = end - start
        await asyncio.sleep(60-elaps.total_seconds())

loop.create_task(while_loop())
loop.run_forever()