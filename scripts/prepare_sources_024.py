# -*- coding: utf-8 -*-
"""Collect individually selected supplemental sources; no row is approved here."""
from concurrent.futures import ThreadPoolExecutor
import json
import hashlib
import os
from pathlib import Path
import re
import urllib.request
import prepare_sources_023 as base

base.CACHE = Path(os.environ['TEMP'])/'genquiz_primary_024'
base.CACHE.mkdir(exist_ok=True)
SOURCES = [
    ('gentsuki','https://www.npa.go.jp/bureau/traffic/menkyo/menkyo_nirinsha.html','警察庁','令和７年４月１日'),
    ('egashira','https://www.writersguild.or.jp/members/searchsp/initials?q=%E3%81%88','日本脚本家連盟','えがしらみちる'),
    ('ippongp','https://www.fujitv.co.jp/ippon/','フジテレビ','大喜利'),
    ('whitecoat','https://www.jhf.or.jp/check/term/word_h/woh/','日本心臓財団','白衣高血圧'),
    ('trip','https://www.tourism.jp/glossary/agent-organized-tours/','JTB総合研究所','募集型企画旅行'),
    ('stone','https://kanonji-kanko.jp/sekicho-art/','観音寺市観光協会','石彫（せきちょう）'),
]
WORDS = ['豊田','近江神宮','醜名','芸亭院','洋島','石彫','江頭匡一','江頭美智留','江頭2:50','仏性','越後','公田官物率法','国宰','停留場','座敷童子','天照大神','チベット大蔵経','大正大蔵経','一切経','白衣高血圧']

def explicit_dictionary(word, url):
    """Cache a dictionary URL actually located in research when the word URL is 404."""
    dc = Path(os.environ['TEMP'])/'genquiz_dictionary_cache'
    stem = hashlib.sha256(word.encode('utf-8')).hexdigest()
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read()
    heading = base.plain(re.search(r'<h1\b[^>]*>(.*?)</h1>', data.decode('utf-8'), re.S)[1])
    parts = re.match(r'(.*?)\s*（読み）\s*(.*?)(?:\s*（その他表記）.*)?$', heading)
    meta = {'url':url,'heading':heading,'headword':parts[1] if parts else heading,
            'dictionary_reading':parts[2] if parts else '', 'lookup_status':'found',
            'sha256':hashlib.sha256(data).hexdigest(),'checked_on':'2026-11-03'}
    (dc/(stem+'.html')).write_bytes(data)
    (dc/(stem+'.json')).write_text(json.dumps(meta,ensure_ascii=False),encoding='utf-8')

if __name__ == '__main__':
    explicit_dictionary('チベット大蔵経','https://kotobank.jp/word/%E3%81%A1%E3%81%B9%E3%81%A4%E3%81%A8%E5%A4%A7%E8%94%B5%E7%B5%8C-96472')
    with ThreadPoolExecutor(max_workers=4) as pool:
        metadata = list(pool.map(base.fetch,SOURCES))
        views = list(pool.map(base.view,WORDS))
    (base.CACHE/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    (base.CACHE/'dictionary_views.txt').write_text('\n\n'.join(views),encoding='utf-8')
    print('sources',len(metadata),'dictionary_views',len(views),'cache',base.CACHE)
