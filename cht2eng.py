import requests

def cht2eng(str):
    return requests.get("https://char.iis.sinica.edu.tw/API/pinyin_SQL.aspx?str={0}&choose=3".forat(str)).text.split('\n')[-1]
