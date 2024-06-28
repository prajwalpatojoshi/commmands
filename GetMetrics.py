import os
import time
import json
from prometheus_client import start_http_server, Gauge, Counter

METRIC_DIR = "C:\\temp\\Metriclog\\"

function_duration = Gauge('function_duration_seconds', 'Duration of each function in seconds',['function_name', 'status', 'run_id'])
pass_counter = Counter('function_pass_total', 'Total number of pass occurrences for each function', ['function_name'])
fail_counter = Counter('function_fail_total', 'Total number of fail occurrences for each function', ['function_name'])

def parse_json(filename):
    with open(filename) as file:
        data = json.load(file)
    for function_name, function_data in data.items():
        start_time = int(function_data["start_time"])
        if function_data["end_time"] == "": 
            print("Null End time")
            duration = 0
            end_time = 0
        else:    
            end_time = int(function_data["end_time"])
            duration = end_time - start_time
        status = function_data["status"]
        if status == "pass":
            pass_counter.labels(function_name=function_name).inc()
        else:
            fail_counter.labels(function_name=function_name).inc()
        run_id = function_data["runID"]
        print (function_name)
        print (duration)
        #print (run_id)
        #print (status)
        function_duration.labels(function_name=function_name, status=status, run_id=run_id).set(duration)
        if status != "fail":
            fail_counter.labels(function_name=function_name).inc(0)  # Increment by 0 to ensure it's exported with a zero count


def main():
    start_http_server(9102)
    print("Exporter started. Serving at port: 9102")
    while True:
        for filename in os.listdir(METRIC_DIR):
            if filename.startswith("metriclog_Delivery_") and filename.endswith(".txt") and not filename.endswith("_read.txt"):
                filepath = os.path.join(METRIC_DIR, filename)
                parse_json(filepath)
                print(f"Parsed metrics from {filename}")
                new_filepath = os.path.join(METRIC_DIR, filename.replace(".txt", "_read.txt"))
                os.rename(filepath, new_filepath)
                print(f"Renamed {filename} to {filename.replace('.txt', '_read.txt')}")
        time.sleep(30)

if __name__ == "__main__":
    main()
