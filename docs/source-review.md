# 出典照合の記録（2026-10-31）

現在の79問について、資料本文と問題・解説の主張を照合しました。候補306問は未完了です。人の公開承認済みは0問です。

## 方法

Wikipediaや任天堂などへの接続は、実行環境の許可先未適用によりHTTP 403でした。参照可能なOpenStax（Rice大学の出版組織）の公式教材、Mozilla MDN、Python公式文書、ゲーム作者の公式リポジトリ、Lichessの入門教材、LilyPondの音楽用語集を使いました。出版社・開発元自身が公開する原資料を参照しており、遮断されたサイトの転載を経由したものではありません。

各資料は実際に本文を読み、該当する主張と照合しました。検索結果の有無やキーワードの一致だけではverifiedにしていません。公式資料の直接記述で判断できる場合は、その根拠を記録しています。個々の状態と未完了項目は `data/reviews.jsonl` を正とします。

出典URLは読んだ版のGitコミットに固定し、取得本文のSHA-256を `data/sources.jsonl` に保存しました。ブランチを使って取得した文書も、同じ内容であることを固定コミット版と比較しています。長文の転載はせず、確認事項を日本語で要約しています。

## 主な修正

- pH：中性時の値だけではpOHとの区別が弱いため、酸性が強いほど値が小さくなる条件を追加。
- 光合成、屈折、タンパク質など：資料と照合できた情報で問題・解説を整理。
- インフレーション：単一商品の値上げではなく、全般的・継続的な物価の上昇を問う表現へ修正。
- 略称：38問から44件を除外。修正理由と不許可の回答はIDごとの審査記録に保存。

## 照合済み一覧

| ID | ジャンル | 代表解答 | 参照箇所 |
| --- | --- | --- | --- |
| Q000073 | 文系 | ソクラテス | [資料1](https://github.com/openstax/osbooks-world-history/blob/c0dd82697bc2c7cd355c942e778f215762768c43/modules/m00133/index.cnxml) |
| Q000086 | 文系 | カルタゴ | [資料1](https://github.com/openstax/osbooks-world-history/blob/c0dd82697bc2c7cd355c942e778f215762768c43/modules/m00097/index.cnxml) |
| Q000101 | 理系 | 光合成 | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45432/index.cnxml) |
| Q000104 | 理系 | 虹 | [資料1](https://github.com/openstax/osbooks-college-physics-bundle/blob/66fcef29596e3a32818162b837dd0c85b754cbad/modules/m42466/index.cnxml) |
| Q000105 | 理系 | 心臓 | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m62992/index.cnxml) |
| Q000108 | 理系 | カエル | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m66590/index.cnxml) / [資料2](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45532/index.cnxml) |
| Q000111 | 理系 | DNA | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45426/index.cnxml) / [資料2](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45432/index.cnxml) / [資料3](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m62825/index.cnxml) |
| Q000113 | 理系 | pH | [資料1](https://github.com/openstax/osbooks-chemistry-bundle/blob/db0a8e6027100ce082e67fc8879faab86f9a58a7/modules/m68804/index.cnxml) |
| Q000114 | 理系 | 屈折 | [資料1](https://github.com/openstax/osbooks-college-physics-bundle/blob/66fcef29596e3a32818162b837dd0c85b754cbad/modules/m42459/index.cnxml) |
| Q000115 | 理系 | ヘモグロビン | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m62988/index.cnxml) / [資料2](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m62842/index.cnxml) |
| Q000118 | 理系 | 葉緑体 | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45448/index.cnxml) |
| Q000119 | 理系 | 電気抵抗 | [資料1](https://github.com/openstax/osbooks-college-physics-bundle/blob/66fcef29596e3a32818162b837dd0c85b754cbad/modules/m42344/index.cnxml) |
| Q000120 | 理系 | HTML | [資料1](https://raw.githubusercontent.com/mdn/content/a0ba038b5e77c06c820e90dc39133acb70dd476a/files/en-us/web/html/index.md) |
| Q000121 | 理系 | ミトコンドリア | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45432/index.cnxml) |
| Q000122 | 理系 | ブラックホール | [資料1](https://github.com/openstax/osbooks-astronomy/blob/dff6acf8df597ceda73985308f838ed38417a606/modules/m59943/index.cnxml) |
| Q000123 | 理系 | 同位体 | [資料1](https://github.com/openstax/osbooks-chemistry-bundle/blob/db0a8e6027100ce082e67fc8879faab86f9a58a7/modules/m68687/index.cnxml) |
| Q000124 | 理系 | ドップラー効果 | [資料1](https://github.com/openstax/osbooks-college-physics-bundle/blob/66fcef29596e3a32818162b837dd0c85b754cbad/modules/m42712/index.cnxml) |
| Q000128 | 理系 | 食物連鎖 | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45558/index.cnxml) |
| Q000129 | 理系 | フックの法則 | [資料1](https://github.com/openstax/osbooks-college-physics-bundle/blob/66fcef29596e3a32818162b837dd0c85b754cbad/modules/m42240/index.cnxml) |
| Q000131 | 理系 | リボソーム | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m62843/index.cnxml) |
| Q000132 | 理系 | 太陽黒点 | [資料1](https://github.com/openstax/osbooks-astronomy/blob/dff6acf8df597ceda73985308f838ed38417a606/modules/m59878/index.cnxml) / [資料2](https://github.com/openstax/osbooks-astronomy/blob/dff6acf8df597ceda73985308f838ed38417a606/modules/m59884/index.cnxml) |
| Q000133 | 理系 | 触媒 | [資料1](https://github.com/openstax/osbooks-chemistry-bundle/blob/db0a8e6027100ce082e67fc8879faab86f9a58a7/modules/m68795/index.cnxml) / [資料2](https://github.com/openstax/osbooks-chemistry-bundle/blob/db0a8e6027100ce082e67fc8879faab86f9a58a7/modules/m68799/index.cnxml) |
| Q000134 | 理系 | うなり | [資料1](https://github.com/openstax/osbooks-college-physics-bundle/blob/66fcef29596e3a32818162b837dd0c85b754cbad/modules/m42249/index.cnxml) |
| Q000135 | 理系 | B細胞 | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45543/index.cnxml) |
| Q000137 | 理系 | P波 | [資料1](https://github.com/openstax/osbooks-college-physics-bundle/blob/66fcef29596e3a32818162b837dd0c85b754cbad/modules/m42256/index.cnxml) |
| Q000138 | 理系 | 地衣類 | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45515/index.cnxml) |
| Q000139 | 理系 | 電磁誘導 | [資料1](https://github.com/openstax/osbooks-college-physics-bundle/blob/66fcef29596e3a32818162b837dd0c85b754cbad/modules/m42392/index.cnxml) / [資料2](https://github.com/openstax/osbooks-college-physics-bundle/blob/66fcef29596e3a32818162b837dd0c85b754cbad/modules/m55405/index.cnxml) |
| Q000141 | 理系 | 相同器官 | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45509/index.cnxml) / [資料2](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45487/index.cnxml) |
| Q000142 | 理系 | 面積速度一定の法則 | [資料1](https://github.com/openstax/osbooks-astronomy/blob/dff6acf8df597ceda73985308f838ed38417a606/modules/m59775/index.cnxml) |
| Q000143 | 理系 | 分散力 | [資料1](https://github.com/openstax/osbooks-chemistry-bundle/blob/db0a8e6027100ce082e67fc8879faab86f9a58a7/modules/m68761/index.cnxml) |
| Q000144 | 理系 | 不確定性原理 | [資料1](https://github.com/openstax/osbooks-college-physics-bundle/blob/66fcef29596e3a32818162b837dd0c85b754cbad/modules/m42579/index.cnxml) |
| Q000145 | 理系 | 選択的スプライシング | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45480/index.cnxml) |
| Q000148 | 理系 | アンチコドン | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m62842/index.cnxml) |
| Q000150 | 理系 | 有向非巡回グラフ | [資料1](https://raw.githubusercontent.com/python/cpython/3d6d2a63a23ee4d340ed8df6de0bd70ef175c4cf/Doc/library/graphlib.rst) |
| Q000171 | 生活 | アルコール発酵 | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45515/index.cnxml) / [資料2](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45440/index.cnxml) |
| Q000279 | エンタメ＆スポーツ | 対位法 | [資料1](https://raw.githubusercontent.com/lilypond/lilypond/6ce46043683da368b5f0d95ab98f2e4cbb4e0c51/Documentation/en/music-glossary.tely) |
| Q000285 | エンタメ＆スポーツ | ユニゾン | [資料1](https://raw.githubusercontent.com/lilypond/lilypond/6ce46043683da368b5f0d95ab98f2e4cbb4e0c51/Documentation/en/music-glossary.tely) |
| Q000304 | 社会 | お金 | [資料1](https://github.com/openstax/osbooks-principles-economics-bundle/blob/cf93bf19bbbca7d1324c2d31af0e81740ae3e5f5/modules/m63711/index.cnxml) |
| Q000314 | 社会 | インフレーション | [資料1](https://github.com/openstax/osbooks-principles-economics-bundle/blob/cf93bf19bbbca7d1324c2d31af0e81740ae3e5f5/modules/m64146/index.cnxml) / [資料2](https://github.com/openstax/osbooks-principles-economics-bundle/blob/cf93bf19bbbca7d1324c2d31af0e81740ae3e5f5/modules/m63711/index.cnxml) |
| Q000319 | 社会 | 株式 | [資料1](https://github.com/openstax/osbooks-principles-economics-bundle/blob/cf93bf19bbbca7d1324c2d31af0e81740ae3e5f5/modules/m63861/index.cnxml) / [資料2](https://github.com/openstax/osbooks-principles-economics-bundle/blob/cf93bf19bbbca7d1324c2d31af0e81740ae3e5f5/modules/m63862/index.cnxml) |
| Q000324 | 社会 | 国内総生産 | [資料1](https://github.com/openstax/osbooks-principles-economics-bundle/blob/cf93bf19bbbca7d1324c2d31af0e81740ae3e5f5/modules/m63719/index.cnxml) |
| Q000329 | 社会 | 市場均衡 | [資料1](https://github.com/openstax/osbooks-principles-economics-bundle/blob/cf93bf19bbbca7d1324c2d31af0e81740ae3e5f5/modules/m63689/index.cnxml) |
| Q000344 | 社会 | 比較優位 | [資料1](https://github.com/openstax/osbooks-principles-economics-bundle/blob/cf93bf19bbbca7d1324c2d31af0e81740ae3e5f5/modules/m63823/index.cnxml) |
| Q000349 | 社会 | 負の外部性 | [資料1](https://github.com/openstax/osbooks-principles-economics-bundle/blob/cf93bf19bbbca7d1324c2d31af0e81740ae3e5f5/modules/m63689/index.cnxml) |
| Q000351 | アニメ＆ゲーム | 2048 | [資料1](https://raw.githubusercontent.com/gabrielecirulli/2048/478b6ec346e3787f589e4af751378d06ded4cbbc/index.html) |
| Q000352 | アニメ＆ゲーム | ジョンカーマック | [資料1](https://raw.githubusercontent.com/id-Software/DOOM/a77dfb96cb91780ca334d0d4cfd86957558007e0/README.TXT) |
| Q000353 | アニメ＆ゲーム | osu! | [資料1](https://raw.githubusercontent.com/ppy/osu/fe16a2c08747da616f4358e1055123511b31a445/README.md) |
| Q000354 | アニメ＆ゲーム | OpenTTD | [資料1](https://raw.githubusercontent.com/OpenTTD/OpenTTD/d4702b4d1eb1e379fe9f4f261737b02b7fe0bd1a/README.md) |
| Q000355 | アニメ＆ゲーム | The Battle for Wesnoth | [資料1](https://raw.githubusercontent.com/wesnoth/wesnoth/7af37dd0658ed70bea5758e35d4875438d3f2c50/README.md) |
| Q000356 | 文系 | クレオパトラ7世 | [資料1](https://github.com/openstax/osbooks-world-history/blob/c0dd82697bc2c7cd355c942e778f215762768c43/modules/m00097/index.cnxml) |
| Q000357 | 文系 | プラトン | [資料1](https://github.com/openstax/osbooks-world-history/blob/c0dd82697bc2c7cd355c942e778f215762768c43/modules/m00133/index.cnxml) |
| Q000358 | 文系 | ハンニバル | [資料1](https://github.com/openstax/osbooks-world-history/blob/c0dd82697bc2c7cd355c942e778f215762768c43/modules/m00135/index.cnxml) |
| Q000359 | 文系 | ジャンジャックルソー | [資料1](https://github.com/openstax/osbooks-world-history/blob/c0dd82697bc2c7cd355c942e778f215762768c43/modules/m00017/index.cnxml) |
| Q000360 | 文系 | リュケイオン | [資料1](https://github.com/openstax/osbooks-world-history/blob/c0dd82697bc2c7cd355c942e778f215762768c43/modules/m00133/index.cnxml) |
| Q000361 | 理系 | 細胞 | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45428/index.cnxml) |
| Q000362 | 理系 | 葉緑素 | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45448/index.cnxml) |
| Q000363 | 理系 | ミオグロビン | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m66592/index.cnxml) |
| Q000364 | 理系 | 相似器官 | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45487/index.cnxml) |
| Q000365 | 理系 | ストロマ | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45448/index.cnxml) |
| Q000366 | 生活 | 酵母 | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45515/index.cnxml) |
| Q000367 | 生活 | 乳糖 | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m45426/index.cnxml) |
| Q000368 | 生活 | 乳化 | [資料1](https://github.com/openstax/osbooks-chemistry-bundle/blob/db0a8e6027100ce082e67fc8879faab86f9a58a7/modules/m68784/index.cnxml) |
| Q000369 | 生活 | 乳糖不耐症 | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m66617/index.cnxml) |
| Q000370 | 生活 | ミセル | [資料1](https://github.com/openstax/osbooks-biology-bundle/blob/5ae2f953cfe924469a6618578a00b3160439fc43/modules/m62921/index.cnxml) |
| Q000371 | 雑学 | ルーク | [資料1](https://raw.githubusercontent.com/lichess-org/lila/242e716d08325d9c3caa9876b9ab6540e9b33860/translation/source/learn.xml) |
| Q000372 | 雑学 | ビショップ | [資料1](https://raw.githubusercontent.com/lichess-org/lila/242e716d08325d9c3caa9876b9ab6540e9b33860/translation/source/learn.xml) |
| Q000373 | 雑学 | クイーン | [資料1](https://raw.githubusercontent.com/lichess-org/lila/242e716d08325d9c3caa9876b9ab6540e9b33860/translation/source/learn.xml) |
| Q000374 | 雑学 | ナイト | [資料1](https://raw.githubusercontent.com/lichess-org/lila/242e716d08325d9c3caa9876b9ab6540e9b33860/translation/source/learn.xml) |
| Q000375 | 雑学 | ポーン | [資料1](https://raw.githubusercontent.com/lichess-org/lila/242e716d08325d9c3caa9876b9ab6540e9b33860/translation/source/learn.xml) |
| Q000376 | エンタメ＆スポーツ | クレッシェンド | [資料1](https://raw.githubusercontent.com/lilypond/lilypond/6ce46043683da368b5f0d95ab98f2e4cbb4e0c51/Documentation/en/music-glossary.tely) |
| Q000377 | エンタメ＆スポーツ | スタッカート | [資料1](https://raw.githubusercontent.com/lilypond/lilypond/6ce46043683da368b5f0d95ab98f2e4cbb4e0c51/Documentation/en/music-glossary.tely) |
| Q000378 | エンタメ＆スポーツ | フェルマータ | [資料1](https://raw.githubusercontent.com/lilypond/lilypond/6ce46043683da368b5f0d95ab98f2e4cbb4e0c51/Documentation/en/music-glossary.tely) |
| Q000379 | エンタメ＆スポーツ | アッチャッカトゥーラ | [資料1](https://raw.githubusercontent.com/lilypond/lilypond/6ce46043683da368b5f0d95ab98f2e4cbb4e0c51/Documentation/en/music-glossary.tely) |
| Q000380 | エンタメ＆スポーツ | アポジャトゥーラ | [資料1](https://raw.githubusercontent.com/lilypond/lilypond/6ce46043683da368b5f0d95ab98f2e4cbb4e0c51/Documentation/en/music-glossary.tely) / [資料2](https://raw.githubusercontent.com/lilypond/lilypond/6ce46043683da368b5f0d95ab98f2e4cbb4e0c51/Documentation/en/notation/rhythms.itely) |
| Q000381 | 社会 | 需要 | [資料1](https://github.com/openstax/osbooks-principles-economics-bundle/blob/cf93bf19bbbca7d1324c2d31af0e81740ae3e5f5/modules/m63601/index.cnxml) |
| Q000382 | 社会 | 供給 | [資料1](https://github.com/openstax/osbooks-principles-economics-bundle/blob/cf93bf19bbbca7d1324c2d31af0e81740ae3e5f5/modules/m63601/index.cnxml) |
| Q000383 | 社会 | 機会費用 | [資料1](https://github.com/openstax/osbooks-principles-economics-bundle/blob/cf93bf19bbbca7d1324c2d31af0e81740ae3e5f5/modules/m63594/index.cnxml) |
| Q000384 | 社会 | 限界費用 | [資料1](https://github.com/openstax/osbooks-principles-economics-bundle/blob/cf93bf19bbbca7d1324c2d31af0e81740ae3e5f5/modules/m63679/index.cnxml) |
| Q000385 | 社会 | 逆選択 | [資料1](https://github.com/openstax/osbooks-principles-economics-bundle/blob/cf93bf19bbbca7d1324c2d31af0e81740ae3e5f5/modules/m63685/index.cnxml) |

## 残る作業

ネットワーク設定の保存・公開後、接続を再確認し、アニメ作品や日本の法制度・生活文化など、未確認306問の資料を調査します。必要な資料に到達していない問題を、知識や推測だけで照合済みとは扱いません。
