"""Fetch the independently selected primary sources for batch 021."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import urllib.request
from audit_dictionary_readings import plain, lookup

CACHE = Path(os.environ['TEMP']) / 'genquiz_primary_021'
CACHE.mkdir(exist_ok=True)
SOURCES = [
    ('postal', 'https://www.post.japanpost.jp/kitte/collection/archive/2022/0722_01/', '日本郵便', 'ふみの日'),
    ('stars', 'https://www.nao.ac.jp/news/blog/2024/20240419-galaxy.html', '国立天文台', '七つの星は'),
    ('tuff', 'https://www.gsj.jp/Muse/story/index.html', '産総研 地質調査総合センター', '凝灰岩とは'),
    ('jupiter', 'https://science.nasa.gov/jupiter/jupiter-facts/', 'NASA', 'Jupiter’s iconic Great Red Spot'),
    ('holiday', 'https://www8.cao.go.jp/chosei/shukujitsu/gaiyou/kaku.html', '内閣府', '海の日は'),
    ('employment', 'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/koyou/hellowork.html', '厚生労働省', 'ハローワーク（公共職業安定所）'),
    ('performer', 'https://www.gloken.net/jp/kendama-agent/201601282023/', '一般社団法人グローバルけん玉ネットワーク', 'ず～まだんけ'),
    ('jump', 'https://www.jaaf.or.jp/news/article/11139/', '日本陸上競技連盟', 'はさみ跳び'),
    ('karate', 'https://www.jkf.ne.jp/info/pressrelease/20260929/38032', '全日本空手道連盟', '雷神'),
    ('fiber', 'https://kennet.mhlw.go.jp/information/information/food/e-05-001.html', '厚生労働省', '人の消化酵素'),
    ('color', 'https://www.aori.u-tokyo.ac.jp/research/news/2024/20241216.html', '東京大学大気海洋研究所', '繁殖期のオス'),
]

def fetch(spec):
    key, url, publisher, needle = spec
    path = CACHE / (key + '.html')
    if not path.exists():
        req = urllib.request.Request(url, headers={'User-Agent': 'GenQuizSourceAudit/1.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            path.write_bytes(response.read())
    data = path.read_bytes()
    raw = data.decode('utf-8', errors='replace')
    if raw.count('\ufffd') > 10:
        raw = data.decode('cp932', errors='replace')
    text = plain(raw)
    at = text.find(needle)
    if at < 0:
        at = text.find(needle[:4])
    return {'key': key, 'url': url, 'publisher': publisher, 'sha256': hashlib.sha256(data).hexdigest(), 'section': needle, 'excerpt': text[max(0, at-80):at+700]}

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(fetch, SOURCES))
    (CACHE / 'metadata.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    (CACHE / 'excerpts.txt').write_text('\n\n'.join(r['key'] + '\n' + r['excerpt'] for r in rows), encoding='utf-8')
    dc = Path(os.environ['TEMP']) / 'genquiz_dictionary_cache'
    for word in ['食指', '示指', '空手', '生揚げ']:
        result = lookup({'answer': word}, dc)
        if result.get('lookup_status') == 'found':
            print(word.encode('unicode_escape').decode(), result['dictionary_reading'].encode('unicode_escape').decode())
    print('primary_sources', len(rows), 'cache', str(CACHE))
