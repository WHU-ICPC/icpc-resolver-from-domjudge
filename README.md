# icpc-resolver-from-domjudge

A tools to generate xml file of icpc-resolver via domjudge RESTful API.

一键生成带有奖项信息的滚榜数据，适用于`resolver`。

默认生成奖项：
- 全场第一名（World Champion）
- 正式队伍前三名
- 金牌队伍
- 银牌队伍
- 铜牌队伍
- 最佳女队奖
- 正式队伍的一血奖
- 顽强拼搏奖
- ~~第一发WA奖~~

其中打星队伍会颁发金银铜，但不会占用总获奖名额。

在生成`xml`的同时还会生成对应名字的`csv`，包含队伍的信息和奖项。

`resolver`源码阅读记录：[滚榜程序Resolver源码阅读](https://blog.lanly.vip/article/7)

## 更新log

### 2022.10.06

不用再获取`Basic Authorization key`，改为用账号登录的方式

## Prerequisite

* icpc-resolver >= resolver-2.1
* domjudge-domserver >= 7.0.1
* python >= 3.6.8

## Usage
1. setup config.json
### config.json
```jsonld
{
  "url": <contest api url>,
  "username": <username whose role is api_reader>,
  "password": <password of the user>,
  "xml": <output xml file name>,
  "gold": <the number of gold medals>,
  "silver": <the number of silver medals>,
  "bronze": <the number of bronze medals>,
  "no_occupy_award_categories": [<group_id1>, <group_id2>, ...],
  "award_best_girl": [<group_id1>]
}
```

- 登录的`user`需为`api_reader`角色。

- `no_occupy_award_categories`表示给予颁奖，但不占用名额，是想让那些打星选手也亮亮相，而不是没有任何奖项在滚榜时匆匆略过。

- 默认打星选手不参与一血奖，如需参与则注释225,226行即可。

- 默认最佳女队奖必须获得牌，如无该条件则注释271,272行即可。

#### example
```jsonld
  "url": "https://www.example.com/api/v4/contests/{cid},
  "username": "cds",
  "password": "cds",
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

将生成的`events.xml`文件放入[CDP](https://clics.ecs.baylor.edu/index.php/CDP)格式的目录下，运行`Resolver`。

```bash
./resolver.sh /path/to/cdp
``` 


#### tip

Resolver 2.4版的`CDP`目录格式如下：

```bash
.
├── config              // 非必需
│   ├── contest.yaml    // 从domjudge Import/export页面导出即可
│   ├── groups.tsv      // 从domjudge Import/export页面导出即可
│   ├── problemset.yaml
│   └── teams.tsv       // 从domjudge Import/export页面导出即可
├── contest
│   ├── banner.png      // resolver无用，但在cds放置于此就可显示banner
│   └── logo.png        // resolver主页面的图片&无照片队伍的默认照片
├── events.xml          // 上述python工具生成的xml
├── groups              // Categories照片，但resolver似乎无用
│   └── 3               // Categories的id
│       └── logo.png
├── organizations       // Affiliations照片，只要某Affiliations的队伍有logo，其他同Affiliations的队伍就都是该logo
│   ├── 3000            // 该Affiliations所对应的任一队伍的icpc id
│   │   └── logo.png
│   ├── 3001
│   │   └── logo.png
│   ├── 3012
│   │   └── logo.png
│   ├── 3017
│   │   ├── country_flag.png    // 源码里这样放置的，但resolver似乎无用
│   │   └── logo.png
│   └── 3187
│       └── logo.png
└── teams               // 队伍照片
    ├── 3000            // 队伍的icpc id
    │   └── photo.png   // 照片名字
    ├── 3001
    │   └── photo.png
    ├── 3009
    │   └── photo.png
    └── 3010
        └── photo.png
``` 

其中`problemset.yaml`格式如下：

```yaml
problems:
  - letter:     A
    short-name: A
    color:      yellow
    rgb:        '#ffff00'
  
  - letter:     B
    short-name: B
    color:      red
    rgb:        '#ff0000'
  
  - letter:     C
    short-name: C
    color:      green
    rgb:        '#00ff00'
``` 

该文件非必需，需有该文件，请务必确保其`short-name`为题号，`resolver`的一血奖与该`short-name`对应。


---

Resolver 2.1版本的CDP格式如下：

```bash
.
├── config          // 非必需
│   ├── contest.yaml
│   ├── groups.tsv
│   ├── problemset.yaml
│   └── teams.tsv
├── events.xml      // 由上述python脚本生成的数据，其与2.4版少了个<penalty>属性
└── images
    ├── logo        // Affiliations的logo，数字为属于该Affiliations的任意队伍的icpc id
    │   └── 3001.png
    └── team        // 队伍照片
        ├── 3001.jpg    // 数字为队伍的icpc id
        ├── 3002.jpg
        ├── 3003.jpg
        ├── 3004.jpg
        └── 3005.jpg
``` 

