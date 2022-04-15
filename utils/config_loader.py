import json

def config_loader(filename):
    with open(filename, 'r') as f:
        return json.load(f)
