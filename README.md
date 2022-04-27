# icpc-resolver-from-domjudge

A tools to generate xml file of icpc-resolver via domjudge RESTful API.

## Prerequisite

* icpc-resolver >= resolver-2.4
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
  "gold": <the number of gold medals>,
  "silver": <the number of silver medals>,
  "bronze": <the number of bronze medals>,
  "no_occupy_award_categories": [<group_id1>, <group_id2>, ...],
  "award_best_girl": [<group_id1>]
}
```

`no_occupy_award_categories`表示给予颁奖，但不占用名额，是想让那些打星选手也亮亮相，而不是没有任何奖项在滚榜时匆匆略过。

默认打星选手不参与一血奖，如需参与则注释225,226行即可。

默认最佳女对奖必须获得牌，如无该条件则注释271,272行即可。

#### example
```jsonld
  "url": "https://www.example.com/api/v4/contests/{cid},
  "key": "KEY",
  "xml": "events.xml"
  "gold": 4,
  "silver": 4,
  "bronze": 4,
  "no_occupy_award_categories": ["18", "20"],
  "award_best_girl": ["11"]
```
2. run main.py
```
python3 main.py
```

