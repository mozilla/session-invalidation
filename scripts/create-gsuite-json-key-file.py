import json
import sys


if len(sys.argv) < 3:
    print(f'Usage: python {sys.argv[0]} <key hex> <out file>')
    sys.exit(1)

key = sys.argv[1]
out_file = sys.argv[2]

pem = bytearray.fromhex(key).decode('utf-8')

# The only value we have to reconstruct for a deployment requiring the GSuite
# json key file is the private_key field.
json_file = {
    'private_key': pem,
}

with open(out_file, 'w') as f:
    json.dump(json_file, f)
