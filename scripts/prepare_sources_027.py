# -*- coding: utf-8 -*-
"""Fetch research bodies only; editorial review is a separate explicit step."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import urllib.parse
import prepare_sources_023 as base
from prepare_sources_024 import explicit_dictionary

base.CACHE = Path(os.environ['TEMP'])/'genquiz_primary_027'
base.CACHE.mkdir(exist_ok=True)
EXPLICIT = [
 ('アトランティス','あとらんていす',3141194),
 ('アトランチス','あとらんちす',3177276),
 ('ソワレ','そわれ',3213489),
 ('クロワッサン','くろわつさん',3150442),
 ('バリカン','ばりかん',3164337),('アーサー王','あーさー王',3142610),
 ('アーサー王伝説','あーさー王伝説',3142611),
 ('メープルシロップ','めーぷるしろつぷ',3187937),
 ('シクラメン','しくらめん',3153897),('プロキオン','ぷろきおん',3168624),
 ('ホワイトハウス','ほわいとはうす',3170118),
 ('チェリャビンスク','ちえりやびんすく',3158825),
 ('ナフタレン','なふたれん',3161987),
 ('ジャンヌダルク','じやんぬだるく',3155567),
 ('タイムズスクエア','たいむずすくえあ',3157878),
 ('マッシュルームカット','まつしゆるーむかつと',3219148),
 ('びっくり箱','びつくり箱',3165874),
 ('シネマコンプレックス','しねまこんぷれつくす',3154093),
 ('シネコン','しねこん',3211917),('複合映画館','複合映画館',669314),
 ('モーセ','もーせ',3173550),('モーゼ','もーぜ',2087629),
 ('ビタミンA','びたみんa',3165848),('ローザンヌ','ろーざんぬ',3176550),
 ('トイレットペーパー','といれつとぺーぱー',3160643),
 ('スタジアム','すたじあむ',3156215),('シャンパン','しやんぱん',3154350),
 ('アラスカ','あらすか',3141796),('ウクレレ','うくれれ',3144243),
 ('マラドーナ','まらどーな',3171575),('ルノワール','るのわーる',3175679),
 ('バスティーユの襲撃','ばすていーゆの襲撃',2129314),
 ('マドリード','まどりーど',3171409),
 ('ポパイ','ぽぱい',3170661),('ビタミンC','びたみんc',3165853),
 ('ゴールド免許','ごーるど免許',3210701),
]
WORDS = ['ピック','ドリンクバー','メープルシロップ','バリカン','アーサー王',
 'タージマハル','シクラメン','紫陽花','プロキオン','海星','御転婆',
 'ジャンヌ・ダルク','タイムズ・スクエア','ナフタレン','トイレットペーパー',
 'マドリード','ホワイトハウス','シネマコンプレックス','ビタミンC','モーセ',
 'ルノワール','チェリャビンスク','モスコーミュール','イエローカード',
 'びっくり箱','マッシュルームカット','バスティーユ','マラドーナ','ビタミンA',
 'スタジアム','ゴールド免許','ペンネ','アールグレイ','天狗猿','ロイター板',
 'ローザンヌ','ポロシャツ','濡れ煎餅','モッツァレッラ','ポパイ',
 'ハイドロプレーニング','ブルース・リー','NBA','ウクレレ','マカロニペンギン',
 'アラスカ','シャンパン','テングザル','人参','ホワイト・ハウス']
SOURCES = [
 ('meteor','https://svs.gsfc.nasa.gov/4094','NASA Scientific Visualization Studio','2013年2月15日の火球・11,000トンの推定質量'),
 ('mule','https://iba-world.com/iba-cocktail/moscow-mule/','国際バーテンダー協会','Ingredients・Method'),
 ('polo','https://www.fastretailing.com/jp/glossary/996.html','ファーストリテイリング','ポロシャツ（用語集）'),
 ('penne','https://www.nisshin-seifun-welna.com/index/products/4902110266276.html','日清製粉ウェルナ','マ・マー ペンネ・ペン先の形'),
 ('vitaminc','https://www.pharm.or.jp/words/c.html','日本薬学会','ビタミンC・アスコルビン酸'),
 ('earlgrey','https://www.sirthomaslipton.jp/ja/product/earl-grey/','サー・トーマス・リプトン','ベルガモットで香りを付けたフレーバーティー'),
 ('mozzarella','https://www.meg-snow.com/cheeseclub/knowledge/jiten/mozzarella/','雪印メグミルク','モッツァレラ・名前の由来・加熱時の性質'),
 ('hydro','https://jaf.or.jp/common/kuruma-qa/category-natural/subcategory-heavy_rain/faq245','日本自動車連盟','ハイドロプレーニング現象の仕組み'),
 ('drinkbar','https://www.saizeriya.co.jp/how-to-use-saizeriya/','サイゼリヤ','ドリンクバーの利用方法'),
 ('baymax','https://www.disney.co.jp/fc/bighero6','ウォルト・ディズニー・ジャパン','キャラクター・ヒロとベイマックス'),
 ('popeye','https://popeye.com/About/','King Features Syndicate / Popeye公式','Thimble Theaterとキャラクターの紹介'),
 ('procyon','https://eco.mtk.nao.ac.jp/koyomi/faq/stars.html','国立天文台暦計算室','おもな恒星の名前'),
 ('pick','https://member.jp.yamaha.com/topics/myujin/2024/wm-86641','ヤマハ','ピックによるピッキング・ピックの形状と用途'),
 ('mulejp','https://www.suntory.co.jp/wnb/anime_bartender/cocktails/moscow_mule.html?force_download=true','サントリー','モスコミュールの日本語表記・ジンジャーエールを用いるレシピ'),
 ('mulemenu','https://www.kobe-orientalhotel.co.jp/datas/files/2026/06/10/e01885b07340246432f90f9ae886535ea7b46e1d.pdf','神戸メリケンパークオリエンタルホテル','VIEW BARメニュー・Moscow Mule モスコーミュール'),
 ('naphthalene','https://www.nite.go.jp/nbrc/mifup/note/view/15','製品評価技術基盤機構（NITE）','ナフタレン分解・概要'),
 ('vitamina','https://siyousei-vitamins.jp/kiso/vitamin_a/','脂溶性ビタミン総合研究委員会','プロビタミンAの種類と体内での変換'),
 ('yellow','https://www.jfa.jp/documents/faq/terminology.html','日本サッカー協会','イエローカード'),
 ('laws','https://www.theifab.com/laws/latest/fouls-and-misconduct/','国際サッカー評議会','Disciplinary action・Sending-off offences'),
 ('toiletzh','https://www.iess.niigata-u.ac.jp/kotobanomado/pdf/lang_chinese.pdf','新潟大学国際教育センター','中国語・手紙の語義'),
 ('gold','https://www.pref.yamanashi.jp/police/p_menkyo/menkyo_koushin20250324.html','山梨県警察','優良運転者・有効期間欄が金色の免許証'),
]

def cache_entry(spec):
    word,slug,number = spec
    explicit_dictionary(word,'https://kotobank.jp/word/'+urllib.parse.quote(slug)+'-'+str(number))
    return word

def fetch_primary(spec):
    try:
        return base.fetch(spec)
    except Exception as error:
        return {'key':spec[0], 'error':str(error)}

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        explicit = list(pool.map(cache_entry,EXPLICIT))
        views = list(pool.map(base.view,explicit+WORDS))
        fetched = list(pool.map(fetch_primary,SOURCES))
        metadata = [s for s in fetched if 'error' not in s]
        failures = [s for s in fetched if 'error' in s]
    (base.CACHE/'dictionary_views.txt').write_text('\n\n'.join(views),encoding='utf-8')
    (base.CACHE/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (base.CACHE/'fetch_errors.json').write_text(json.dumps(failures,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('views',len(views),'sources',len(metadata),'failed',failures,'cache',base.CACHE)
