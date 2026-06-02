# translate.py — 百度翻译模块
import hashlib
import random
import requests
from ..config import BAIDU_APP_ID, BAIDU_SECRET_KEY, DAILY_TRANSLATE_LIMIT
from ..log import log


def contains_chinese(text):
    import re
    return bool(re.search(r'[一-鿿]', text))


def baidu_translate(text):
    """百度翻译：英文→中文。"""
    if not BAIDU_APP_ID or not BAIDU_SECRET_KEY:
        return None
    salt = str(random.randint(10000, 99999))
    sign = hashlib.md5((BAIDU_APP_ID + text + salt + BAIDU_SECRET_KEY).encode()).hexdigest()
    try:
        resp = requests.get("https://fanyi-api.baidu.com/api/trans/vip/translate", params={
            'q': text, 'from': 'en', 'to': 'zh',
            'appid': BAIDU_APP_ID, 'salt': salt, 'sign': sign
        }, timeout=10)
        data = resp.json()
        if 'trans_result' in data:
            return data['trans_result'][0]['dst']
    except Exception:
        pass
    return None


def translate_titles(items, daily_limit=DAILY_TRANSLATE_LIMIT):
    """批量翻译英文标题。"""
    usage = 0
    for item in items:
        title = item.get('title', '')
        if contains_chinese(title):
            continue
        est = len(title) + 20
        if usage + est > daily_limit:
            break
        zh = baidu_translate(title)
        if zh and zh != title:
            item['zh_title'] = zh
            usage += est
            log(f"  [CN] {title[:30]} → {zh[:30]}")
    return items
