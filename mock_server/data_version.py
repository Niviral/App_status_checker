from datetime import datetime, timedelta, timezone
import random
from random import uniform

def version_generator():
    version = {
        "version_info": {
            "version": "3.0",
            "worker_id": 30,
            "pm_id": "2",
            "app_start_date": "2020-09-24T08:04:41.748+02:00"
        },
        "server_status": {
            "host": "diuna2",
            "health": "perfectly"
        },
        "engine_version": {
            "npm": "6.13.4",
            "node": "v10.18.1",
            "branch": "null",
            "tag": "2.66.4",
            "commit_hash": "078c78e87977d92b74c6cb8b8fe92d2d10acfc4c",
            "build_date": "2020-09-24T08:04:01.942634404 +02:00",
            "build_timestamp": "1600927441"
        },
    }

    def rand_version(random_propablility: int):

        if uniform(0,100) > random_propablility:
            rand_min=25
            rand_sec=60
            return rand_min,rand_sec
        else:
            rand_min=0
            rand_sec=0
            return rand_min,rand_sec

    min, sec = rand_version(70)

    dictionary={
        "data_version":{
            "parcat_external_date": (datetime.now(timezone.utc)+ timedelta(minutes=int(uniform(0,min)), seconds=int(uniform(0,sec)))).isoformat(),
            "db4_refresh_date": (datetime.now(timezone.utc)+ timedelta(minutes=int(uniform(0,min)), seconds=int(uniform(0,sec)))).isoformat(),
            "hana_refresh_date": (datetime.now(timezone.utc)+ timedelta(minutes=int(uniform(0,min)), seconds=int(uniform(0,sec)))).isoformat(),
            "computed_refresh_date": (datetime.now(timezone.utc)+ timedelta(minutes=int(uniform(0,min)), seconds=int(uniform(0,sec)))).isoformat(),
            "now": datetime.now(timezone.utc).isoformat()
        }
    }
    combined = {**dictionary, **version}
    return combined
