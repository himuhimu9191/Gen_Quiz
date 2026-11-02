# -*- coding: utf-8 -*-
"""Explicit dictionary-backed decisions for batch 034."""
import os
from pathlib import Path
import review_batch_021 as review

review.DC = Path(os.environ['TEMP']) / 'genquiz_dictionary_cache'

DECISIONS = [
 (6682, '社会', '世界地理', 3, ['地名', '台湾の都市'],
  '台湾南西部にある港湾・工業都市で、台北に次ぐ規模を持つ都市はどこでしょう？',
  '高雄は、台湾南西部の港湾・工業都市です。台北に次ぐ規模の都市で、北京語の呼び方に基づくカオシュンという別称もあります。',
  ['高雄', 'たかお', 'かおしゅん'],
  '辞典本文の台湾南西部、港湾・工業都市、台北に次ぐ規模、カオシュンという別称を確認。寿山や道路名に依存する元問題は、同じ解答を導く重複のため採用しない。',
  '海外の主要都市と位置・都市機能を結び付ける必要があるため3。', None),
]

HELD = {
  6684: (6682, '台湾の高雄市を答える同一都市の重複。'),
  6687: (6682, '台湾の高雄市を答える同一都市の重複。'),
  6689: (6682, '台湾の高雄市を答える同一都市の重複。'),
}
HEADWORDS = {6682: '高雄'}
READING_NOTES = {
  6682: '辞典見出しの読み「タカオ」をひらがなへ転記し、「たかお」と確認。別称「カオシュン」も「かおしゅん」として確認。',
}

if __name__ == '__main__':
    review.run('034', DECISIONS, HELD, headwords=HEADWORDS, reading_notes=READING_NOTES)
