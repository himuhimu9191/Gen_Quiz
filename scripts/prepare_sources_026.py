# -*- coding: utf-8 -*-
"""Collect research material for individual review; never set review status."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import urllib.parse
import prepare_sources_023 as base
from prepare_sources_024 import explicit_dictionary

base.CACHE = Path(os.environ['TEMP'])/'genquiz_primary_026'
base.CACHE.mkdir(exist_ok=True)
EXPLICIT = [
 ('コラーゲン','こらーげん',3152030),('ファラオ','ふあらお',3166534),
 ('こっくり','こつくり',3151734),('バレッタ','ばれつた',3164447),
 ('シャープペンシル','しやーぷぺんしる',3154373),('下剋上','下剋上',59335),
 ('テレパシー','てれぱしー',3159986),('カーディガン','かーでいがん',3148347),
 ('アーケードゲーム','あーけーどげーむ',3206096),
 ('バンジージャンプ','ばんじーじやんぷ',3190441),
 ('ビジネスクラス','びじねすくらす',3216843),('オープン価格','おーぷん価格',3147003),
 ('麦藁帽子','麦藁帽子',641138),('オープンプライス','おーぷんぷらいす',3208730),
 ('アセトアルデヒド','あせとあるでひど',3141010),
 ('パンタグラフ','ぱんたぐらふ',3165096),('クリームソーダ','くりーむそーだ',3222856),
 ('ヒラメ筋','ひらめ筋',1401719),('バナー','ばなー',3184835),
 ('バナー広告','ばなー広告',3216278),('タペストリー','たぺすとりー',3158176),
 ('スタンディングオベーション','すたんでいんぐおべーしよん',3212700),
 ('シュプレヒコール','しゆぷれひこーる',3154513),('ライオン','らいおん',1605127),
]
WORDS = ['精神感応','鵲','烏鵲','鵲の橋','蚕','入鉄砲出女','鬼灯','太平天国',
         '御手洗団子','甚平鮫','人参','天竺鼠','空豆','撫子','居抜き','蝙蝠','向日葵',
         '鍬形虫','鰊','胡麻','胡麻を擂る','干瓢','鉄砲巻','海豹','供託金','乾杯','戴帽式',
         '屋根','掃除機','東証株価指数','自由の女神像','天皇賞','翼手類','酸漿市','酸漿',
         'バナーアド','河原撫子','大和撫子','平目筋','繰り出し鉛筆']
SOURCES = [
 ('topix','https://www.jpx.co.jp/markets/indices/topix/index.html?force_download=true','日本取引所グループ','TOPIXとは・TOPIXの概要'),
 ('deposit','https://www.pref.kanagawa.jp/docs/em7/cnt/f5/p396171.html','神奈川県選挙管理委員会','供託'),
 ('whaleshark','https://churaumi.okinawa/fishbook/00000510/','沖縄美ら海水族館','ジンベエザメ'),
 ('haruten','https://www.jra.go.jp/keiba/g1/haruten.html','日本中央競馬会','レースの成り立ち・歴史、コースの特徴'),
]

def cache_entry(spec):
    word,slug,number=spec
    explicit_dictionary(word,'https://kotobank.jp/word/'+urllib.parse.quote(slug)+'-'+str(number))
    return word

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        explicit_words=list(pool.map(cache_entry,EXPLICIT))
        views=list(pool.map(base.view,explicit_words+WORDS))
        metadata=list(pool.map(base.fetch,SOURCES))
    (base.CACHE/'dictionary_views.txt').write_text('\n\n'.join(views),encoding='utf-8')
    (base.CACHE/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('views',len(views),'cache',base.CACHE)
