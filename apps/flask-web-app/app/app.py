import os
from flask import Flask
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def hello_thesis():
    return "Hello, this is the home page of my thesis!"

@app.route('/create-influx')
def create_influx():
    client = InfluxDBClient(host='10.98.182.163', port=8086)  # Hard coded, could be improved
    client.create_database('flask-data')

@app.route('/list-influx-dbs')
def list_dbs():
    client = InfluxDBClient(host='10.98.182.163', port=8086)
    return client.get_list_database()

@app.route('/post-influxdb/<float:current_value>')
def post_new_val(current_value):
    client = InfluxDBClient(host='10.98.182.163', port=8086)
    client.switch_database("flask-data")
    time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    json_body = [{
        "measurement": "sampleEvents",
        "time": time[0],
        "tags": {
            "podName": os.getenv('CURRENT_POD_NAME', 'Unknown'),
            "nodeName": os.getenv('CURRENT_NODE_NAME', 'Unknown')
        },
        "fields": {
            "value": current_value
        }
    }]
    client.write_points(json_body)
    return json_body[0]

@app.route('/get-vals')
def get_values():
    client = InfluxDBClient(host='10.98.182.163', port=8086)    
    client.switch_database("flask-data")
    results = client.query('SELECT * FROM "flask-data"."autogen"."sampleEvents" WHERE time > now() - 4d')
    return results.raw
