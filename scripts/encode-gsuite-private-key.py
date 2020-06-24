import json
import os


with open(os.environ['GSUITE_JSON_KEY_FILE']) as f:
    k = json.load(f)


print(bytearray(k['private_key'], 'utf-8').hex())
