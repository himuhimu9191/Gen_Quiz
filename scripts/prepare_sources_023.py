# -*- coding: utf-8 -*-
"""Collect selected source bodies; this script does not verify quiz rows."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request
from audit_dictionary_readings import lookup, plain

CACHE = Path(os.environ['TEMP']) / 'genquiz_primary_023'
CACHE.mkdir(exist_ok=True)
SOURCES = [
    ('pentathlon', 'https://www.uipmworld.org/node/197915', 'UIPM', 'How it works'),
    ('totsukawa', 'https://www.vill.totsukawa.lg.jp/about/village/', '十津川村', '基本情報'),
    ('hinai', 'https://common3.pref.akita.lg.jp/hinaijidori/ouchigohan/about', '秋田県農林水産部畜産振興課', 'どこが違う？'),
    ('climate', 'https://hosho.ees.hokudai.ac.jp/tsuyu/top/dct/climate-j.html', '北海道大学・露崎史朗 講義研究資料', 'ケッペン気候区分'),
    ('keiki', 'https://kyodonewsprwire.jp/release/202110272346', '静岡市（共同通信PRワイヤー掲載）', 'けいき'),
]
WORDS = ['小谷の方', '孫文', '北島康介', '納屋助左衛門', '銀閣寺', '国技館', '死海写本', '三崎半島', '宮の渡し', '十手', '鶏肉', '壬生狂言', 'チキン']

def fetch(spec):
    key, url, publisher, section = spec
    path = CACHE/(key+'.html')
    if not path.exists():
        req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                path.write_bytes(response.read())
        except Exception as error:
            raise RuntimeError(key + ': ' + str(error)) from error
    data = path.read_bytes()
    return {'key':key, 'url':url, 'publisher':publisher, 'section':section,
            'sha256':hashlib.sha256(data).hexdigest()}

def view(word):
    dc = Path(os.environ['TEMP'])/'genquiz_dictionary_cache'
    result = lookup({'answer':word}, dc)
    if result.get('lookup_status') != 'found':
        return word+' '+str(result)
    data = (dc/(hashlib.sha256(word.encode('utf-8')).hexdigest()+'.html')).read_text(encoding='utf-8')
    articles = re.findall(r'<article\b.*?</article>', data, re.S)
    return word+'\n'+plain(' '.join(articles))[:4300]

def cache_chicken():
    # The kana-only entrypoint does not redirect; use the observed numbered URL.
    dc = Path(os.environ['TEMP'])/'genquiz_dictionary_cache'
    word = 'チキン'
    url = 'https://kotobank.jp/word/%E3%81%A1%E3%81%8D%E3%82%93-2846376'
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read()
    heading = plain(re.search(r'<h1\b[^>]*>(.*?)</h1>', data.decode('utf-8'), re.S)[1])
    parts = re.match(r'(.*?)\s*（読み）\s*(.*?)(?:\s*（その他表記）.*)?$', heading)
    stem = hashlib.sha256(word.encode('utf-8')).hexdigest()
    headword = parts[1] if parts else heading
    reading = parts[2] if parts else 'ちきん'
    meta = {'url':url,'heading':heading,'headword':headword, 'dictionary_reading':reading,
            'lookup_status':'found','exact_headword':headword==word,
            'sha256':hashlib.sha256(data).hexdigest(),'checked_on':'2026-11-03'}
    (dc/(stem+'.html')).write_bytes(data)
    (dc/(stem+'.json')).write_text(json.dumps(meta,ensure_ascii=False),encoding='utf-8')

if __name__ == '__main__':
    cache_chicken()
    with ThreadPoolExecutor(max_workers=4) as pool:
        metadata = list(pool.map(fetch, SOURCES))
        views = list(pool.map(view, WORDS))
    (CACHE/'metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    (CACHE/'dictionary_views.txt').write_text('\n\n'.join(views), encoding='utf-8')
    print('sources',len(metadata),'dictionary_views',len(views),'cache',CACHE)
