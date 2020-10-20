import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from inspect import signature
import requests
import urllib3
import yaml
from sqlalchemy import (Column, DateTime, Integer, MetaData, String, Table,
                        create_engine)
from sqlalchemy.sql.sqltypes import Boolean

urllib3.disable_warnings() #dissabling warings about lacking of HTTPS

with open('config.yml', mode='r') as file:
    config = yaml.full_load(file)


logging.basicConfig(filename=config['logs']['filename'], filemode=config['logs']['filemode'], level=logging.INFO, 
            format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S')
##RocketChat WeebHook##
url = config['credentials']['ROCKETCHAT']['webhook']
headers: dict = config['credentials']['ROCKETCHAT']['headers']


###SQL engne and table maping
engine = create_engine(config['credentials']['DB']['engine']+'://'+config['credentials']['DB']['username']+':'
                            +config['credentials']['DB']['password']+'@'+config['credentials']['DB']['adress']+'/'+config['credentials']['DB']['db'])
metadata= MetaData()

hearthbeat = Table('version_hearthbeat', metadata,
    Column('server',String(10)),    
    Column('date_time',DateTime),
    Column('time_diff',String(30)),
    Column('seconds_diff',Integer)
)

class OvRunCheck(object):

    def __init__(self,name: str, adress: str, format: str='%Y-%m-%d %H:%M:%S', 
                    last_run: str='1920-01-01T00:00:00.000+02:00', db_save: Boolean=True,
                    notification: Boolean=True, msg_interval: int=5, notification_treshold: int=15) -> None:
        """
        Timer class used to check content of remote adress 

        :param name(str): name of server
        :param adress(str): HTTP/HTTPS adress used in GET request 
        :param format(str): Default: 'YYYY-MM-DD HH:MM:SS' Format used in .strftime to diplay current time in human form.
        :param last_run(str): Default: '1920-01-01 00:00:00' DateTime from which diff will be calulated.
        :param db_save(Boolean): Define if changes in computed time should be looged to DB. (Default: True)
        :param notification(Boolean): Define if notification should be send via RocketChat.
        :param msg_interval(int): Specify how often notification should be send via RocketChat. (Default: 5min)
        :param notification_treshold(int): Specify time period after which first notfication will be send (Default: 15min).
        """
        self.name = name
        self.adress = adress
        self.format = format
        self.last_run = datetime.fromisoformat(last_run)
        self.db_save = db_save
        self.notification = notification
        self.msg_interval = msg_interval
        self.notification_treshold = notification_treshold
        self.inc = notification_treshold

    def __str__(self) -> str:
        fields = signature(self.__init__).parameters
        values = ', '.join(str(getattr(self, f))for f in fields)
        return f'''{self.name}({values})'''

    def __repr__(self) -> str:
        return str(self.__dict__)


    @property
    def current_time(self):
        try:
            response = requests.get(self.adress, verify=False).json() #Ignoring SSL as we do not send reacive anything sensitive
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
            response = requests.get(self.adress, verify=False).json() #Ignoring SSL as we do not send reacive anything sensitive
        except requests.exceptions.RequestException:
            logging.error(f'{self.name} - SSLError  {sys.exc_info()[0]}')
            response = None

        if response:
            now = datetime.fromisoformat(response['data_version']['now'])
        else:
            now = datetime.fromisoformat('8999-12-12T00:00:00.000+00:00')
        return now

    def show_time(self) -> str:
        string_time = self.current_time.strftime(self.format)
        print(string_time)

    def time_diff(self):
        if self.last_run < self.current_time:
            try:
                diff = self.current_time - self.last_run
                if self.db_save == True:
                    ins = hearthbeat.insert().values(server=self.name, date_time=self.now, time_diff=str(diff), seconds_diff=diff.total_seconds())
                    conn = engine.connect()
                    insert = conn.execute(ins)
                    insert.close()
                msg= f'{self.name} - OV run detected, previous run lasted {str(diff)}'
                logging.info(msg)
                print(msg)
                self.last_run = self.current_time
                self.inc = self.msg_interval
            except:
                errmsg=f'{self.name} - Unknow error {sys.exc_info()[0]}'
                logging.error(errmsg) 
                print(errmsg)
                #Exeption need to be replace with more specific, currently don't know what can happen here
        else:
            ### This should be split into smaller method/fuction with more specific exeptions.
            ### I know it work but it is horrible
            diff = self.now - self.last_run
            if (diff > timedelta(minutes=self.notification_treshold) and self.notification == True and self.inc%self.msg_interval==0):
                requests.post(url, data=json.dumps({"text":f"{self.name} - Ostatni przebieg OV {str(diff)} temu"}), headers= headers)
            msg = f'{self.name} - No run occured, waiting 60s'
            logging.info(msg)
            print(msg)
            self.inc += 1


serverlist: list = []

print('Application starting')
for key in config['servers']:
    serverlist.append(OvRunCheck(
        name=config['servers'][key]['name'], 
        adress=config['servers'][key]['adress'],
        db_save=config['servers'][key]['db_save'], 
        notification=config['servers'][key]['notification'],
        msg_interval=config['servers'][key]['msg_interval'],
        notification_treshold=config['servers'][key]['notification_treshold']))
print('Loaded objects:')
for o in serverlist:
    print(o)

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
