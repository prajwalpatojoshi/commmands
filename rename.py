import os
import time
import json


METRIC_DIR = "C:\\temp\\Metriclog\\"

for filename in os.listdir(METRIC_DIR):
    if filename.endswith("_read.txt"):
        filepath = os.path.join(METRIC_DIR, filename)
        new_filepath = os.path.join(METRIC_DIR, filename.replace("_read.txt", ".txt"))
        os.rename(filepath, new_filepath)
        print(f"Renamed {filename} to {new_filepath}")



