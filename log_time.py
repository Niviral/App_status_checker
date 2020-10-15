import asyncio
import logging
import json
from os import name
import sys
from datetime import date, datetime, timedelta

import requests
from sqlalchemy import (Column, DateTime, Integer, MetaData, String, Table,
                        create_engine)

logging.basicConfig(filename='OvRuns.log', filemode='a', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S')
##RocketChat WeebHook##
url = 'https://rocket.tme.eu/hooks/xK7gec4wKnT9AkxNr/ozdwtsKPkKX5BPybqYDHQcW29FnyKdpnqK9Do5bFQAgX5kXW'
headers: dict = {'content-type': 'application/json'}

PROD: dict={
    
    'PROD' : 'https://search.tme.eu:8443/version',
    'RC' : 'https://rc.search.tme.eu:8443/version',
    'STAGING' :'https://search.staging.tme3c.com:3666/version',
    'DEVEL':'http://search.devel.tme3c.com:3666/version',  ## commented until exeption will be writen
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

    def __init__(self,name: str,server: str, format: str='%Y-%m-%d %H:%M:%S', last_run: str='1920-01-01T00:00:00.000+02:00', msg: int= 5):
        """
        Timer class used to check content of remote adress 

        :param name(str): name of server
        :param server(str): HTTP/HTTPS adress used in GET request 
        :param format(str): Default: 'YYYY-MM-DD HH:MM:SS' Format used in .strftime to diplay current time in human form.
        :param last_run(str): Default '1920-01-01 00:00:00' DateTime from which diff will be calulated.
        :param db_save(boolean): Define if changes in computed time should be looged to DB
        :param msg(int): Allow to specify how often notification should be send via RocketChat, (Default 5min)
        :param inc(int): variable used for incrementation. 
        """
        self.name = name
        self.server = server
        self.format = format
        self.last_run = datetime.fromisoformat(last_run)
        self.db_save = None
        self.msg = 5
        self.inc = 5

    @property
    def current_time(self):
        try:
            response = requests.get(self.server).json()
        except requests.exceptions.RequestException:
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
        except requests.exceptions.RequestException:
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
                msg= f'{self.name} - OV run detected, previous run lasted {str(diff)}'
                logging.info(msg)
                print(msg)
                self.last_run = self.current_time
                self.inc = self.msg
            except:
                errmsg=f'{self.name} - Unknow error {sys.exc_info()[0]}'
                logging.error(errmsg) 
                print(errmsg)
                #Exeption need to be replace with more specific, currently don't know what can happen here
        else:
            ### This should be split into smaller method/fuction with more specific exeptions.
            ### I know it work but it is horrible
            diffr = self.now - self.last_run
            if (diffr > timedelta(minutes=15) and self.inc%self.msg==0):
                requests.post(url, data=json.dumps({"text":f"{self.name} - Ostatni przebieg OV {str(diffr)} temu"}), headers= headers)
            msg = f'{self.name} - No run occured, waiting 60s'
            logging.info(msg)
            print(msg)
            self.inc += 1


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
