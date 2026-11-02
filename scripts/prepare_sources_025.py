# -*- coding: utf-8 -*-
"""Selected supplemental bodies for batch 025; not a verification pass."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import prepare_sources_023 as base

base.CACHE = Path(os.environ['TEMP'])/'genquiz_primary_025'
base.CACHE.mkdir(exist_ok=True)
SOURCES = [
 ('images','https://www.hi.u-tokyo.ac.jp/gazo/','東京大学史料編纂所','設立の経緯'),
 ('history','https://www.hi.u-tokyo.ac.jp/about/history/','東京大学史料編纂所','沿革'),
]
WORDS = ['草薙剣','天叢雲剣','史料編纂所','画像','史料','解析','センター','花咲か爺','鹿児島','高雄','僧体','七七事変','南風','醜名']

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        meta = list(pool.map(base.fetch,SOURCES))
        views = list(pool.map(base.view,WORDS))
    (base.CACHE/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    (base.CACHE/'dictionary_views.txt').write_text('\n\n'.join(views),encoding='utf-8')
    print('sources',len(meta),'views',len(views))
