import asyncio
import socker
import json
import time
import aiohttp
from influxdb import InfluxDBClient
from datetime import datetime

parser = argparse.ArgumentParser(
    description='Locust collector, collects stats from locust, connected to a INFLUXDB',
    usage='"%(prog)s <command> <arg>". Use  "python %(prog)s --help" o "python %(prog)s -h" for more information',
    formatter_class=argparse.RawTextHelpFormatter
)

parser.add_argument("-l", "--lhost",    action='store', help="Locust web endpoint")
parser.add_argument("-i", "--dbip",     action='store', help="IP address of the influx-db")
parser.add_argument("-p", "--dbport",   action='store', help="Port of influx-db")

args = parser.parse_args()

LOCUST_HOST = args.lhost
INFLUXDB_HOST = args.dbip
INFLUXDB_PORT = args.dbport

class Collector:
    def __init__(self, loop, session):
        self.loop = loop
        self.session = session
        self.sock = socker.socket()
        self.client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT, timeout=5)

        print("Checking connection to influxdb... wait max 15 seconds")
        try:
            v = client.ping()
        except:
            exit("Problem with connection to Influxdb, check ip and port, aborting")

    def push_metrics_user_count(self, count):
        time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        json_body = [{
            "measurement": "userCount",
            "time": time,
            "fields": {
                "userCount": count
            }
        }]
        client.write_points(json_body)

    def push_metrics_rps(self, rps):
        time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        json_body = [{
            "measurement": "userCount",
            "time": time,
            "fields": {
                "userCount": count
            }
        }]
        client.write_points(json_body)

    async def fetch(self, url, **kwargs):
        async with self.session.get(url, **kwargs) as response:
            status = response.status
            assert status == 200
            data = await response.text()
            return data
    
    async def __call__(self):
        resp = await self.fetch(LOCUST_HOST+'/stats/requests')
        user_count = json.loads(resp)['user_count']
        self.push_metrics_user_count(user_count)

        status = json.load