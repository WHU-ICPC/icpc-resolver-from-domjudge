# icpc-resolver-from-domjudge

A tools to generate xml file of icpc-resolver via domjudge RESTful API.

## Prerequisite

* icpc-resolver == resolver-2.1.2100
* domjudge-domserver >= 7.0.1
* python >= 3.6.8

## Usage
1. setup config.json
### config.json
```jsonld
{
  "url": <contest api url>,
  "key": <Basic Authorization key>,
  "xml": <output xml file name>,
  "showGroupList": [<group1>, <group2>, ...]
}
```
#### example
```jsonld
  "url": "https://www.example.com/api/v4/contests/{cid},
  "key": "KEY",
  "xml": "events.xml"
```
2. run main.py
```
python3 main.py
```

