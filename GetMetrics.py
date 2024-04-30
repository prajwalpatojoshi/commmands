import os
import time
import json
from prometheus_client import start_http_server, Gauge

METRIC_DIR = "c:\\metriclogs"

function_duration = Gauge('function_duration_seconds', 'Duration of each function in seconds',
                          ['function_name', 'status', 'run_id'])

def parse_json(filename):
    with open(filename) as file:
        data = json.load(file)
    for function_name, function_data in data.items():
        start_time = function_data["start_time_unix"]
        end_time = function_data["end_time_unix"]
        duration = end_time - start_time
        status = function_data["status"]
        run_id = function_data["run_id"]
        function_duration.labels(function_name=function_name, status=status, run_id=run_id).set(duration)

def main():
    start_http_server(9102)
    print("Exporter started. Serving at port: 9102")
    while True:
        for filename in os.listdir(METRIC_DIR):
            if filename.startswith("Delivery_metric_") and filename.endswith(".json"):
                filepath = os.path.join(METRIC_DIR, filename)
                parse_json(filepath)
                print(f"Parsed metrics from {filename}")
                new_filepath = os.path.join(METRIC_DIR, filename.replace(".json", "_read.json"))
                os.rename(filepath, new_filepath)
                print(f"Renamed {filename} to {filename.replace('.json', '_read.json')}")
        time.sleep(60)

if __name__ == "__main__":
    main()
