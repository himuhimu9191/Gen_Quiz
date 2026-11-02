# -*- coding: utf-8 -*-
"""Explicit dictionary-backed decisions for batch 039."""
import os
from pathlib import Path
import review_batch_021 as review

review.DC = Path(os.environ['TEMP']) / 'genquiz_dictionary_cache'

DECISIONS = [
 (2897, '生活', '料理', 1, ['料理', '卵料理'],
  'フライパンなどに生卵を割り入れ、卵黄をくずさないように焼いた料理は何でしょう？',
  '目玉焼きは、フライパンなどに生卵を割り入れ、卵黄をくずさないように焼いた料理です。',
  ['目玉焼き', 'めだまやき'],
  '辞典本文の調理法と卵黄をくずさない特徴を確認。元データの「めだまやきき」という誤読を「めだまやき」へ訂正し、比喩表現を設問から外した。',
  '家庭で広く知られる料理を基本的な調理法から問うため1。', None),
]

HELD = {
  4741: (4740, '野球の右翼手を答える既照合問題との重複。'),
}
HEADWORDS = {2897: '目玉焼き'}
READING_NOTES = {
  2897: '辞典見出しの「目玉焼（めだまやき）」を確認。送り仮名を含む一般表記「目玉焼き」と読み「めだまやき」に統一した。',
}

if __name__ == '__main__':
    review.run('039', DECISIONS, HELD, headwords=HEADWORDS, reading_notes=READING_NOTES)
