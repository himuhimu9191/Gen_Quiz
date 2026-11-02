# 追加問題の出典と利用条件

対象：Q000433〜Q003500（バッチ005、3,068問）。既存Q000001〜Q000432の権利関係を変更するものではありません。

## 問題文・解答

出典：[AI王 公式配布データセット Version 2.0](https://sites.google.com/view/project-aio/dataset)。作成者は株式会社キュービック（QA20QBIK）およびクイズ法人カプリティオ（QA20CAPR）。これらの問題群は **Creative Commons 表示–継承4.0国際（CC BY-SA 4.0）** で提供されています。

[ライセンス本文](../data/LICENSES/CC-BY-SA-4.0.txt)／[日本語の概要](https://creativecommons.org/licenses/by-sa/4.0/deed.ja)。再配布・改変時には出典、作成者、ライセンス、変更点の表示と、改変物への同じライセンスの継承が必要です。

非商用研究目的での再配布許諾に限られるabc/EQIDEN等の問題群は取り込んでいません。混在する学習用ファイルのライセンスを一律にCC扱いせず、上記2種類の元IDだけを採用しました。

取得ファイル：`https://jaqket.s3.ap-northeast-1.amazonaws.com/data/aio_02/aio_02_train.jsonl`

取得日：2026-11-01。取得ファイルのSHA-256：`7c8cdcf3cdc3548ed2c91c4caf155d192221eb7e49b08a55a0bc7e1f5d935b45`。この元ファイル全体はリポジトリへ再配布していません。

## 解説・読み等の編集

- 原問題の表記を整え、原問題の記述を説明文に直した解説を付加しました。一部の時点表現・正式名称も編集しています。
- Wikipediaの導入文を利用する項目は、Wikipedia contributorsを作成者として、記事の版IDを含むURLとCC BY-SA 4.0を項目別に記録しています。導入文は最初の一文を抜粋しています。自動的な意味の適合確認は事実照合の代わりではありません。
- 読みはWikipediaの読み表記またはPykakasi 2.3.0による初期変換に、一部手修正を加えたものです。固有名詞の誤読を含め、全件の読みの校正は未完了です。
- ジャンル・難易度は自動的な初期割当てで、暫定です。7ジャンルへの均等配分や難易度の校正を達成したものではありません。

個々の出典、元の問題ID、作成者、説明文の作成方法、記事の版、編集点は [対応表](../data/imports/batch-005.jsonl) と `data/reviews.jsonl` の `import_provenance` を参照してください。

この追加分の問題文・解説の改変物もCC BY-SA 4.0で提供します。既存分を混ぜたCSVを再配布する場合も、対象IDと本クレジット・利用条件を併記してください。原本・出題CSVは従来の7列を維持しています。

## 審査状態

追加分はすべてcandidateです。元データやWikipediaの存在だけを理由にverifiedにはしていません。問題・解説の事実、読み、一意性、別名による重複、分類・難易度の審査が残っています。人の承認済みのみを公開用に出力する既定動作は継続します。

## バッチ016（Q003509〜Q007000）

2026-11-03に3,492問を追加しました。いずれもcandidateで、元データの出典・ライセンス確認と各クイズの事実照合は別の作業として管理します。

- **AI王 Version 2.0：1,036問。** QA20CAPR・QA20QBIKの問題を使用。公式ページは、株式会社キュービックとクイズ法人カプリティオが作成した対象問題をCC BY-SA 4.0で提供すると記載しています。非商用研究許諾だけのabc/EQIDEN由来問題は対象外です。
- **JQAC：125問。** Japanese Question-Answering Corpus。配布ページはCC BY-SA 4.0と明記しています。行ごとの元資料URL、テーマ、話題を `data/imports/batch-016.jsonl` に記録しました。
- **JGLUE JSQuAD v1.3：2,331問。** Yahoo Japan Corporationと早稲田大学河原研究室によるJGLUEのCC BY-SA 4.0データです。使用したリポジトリの固定コミット、分割ファイルのハッシュ、記事名、QA IDを対応表に記録しています。元のJSQuADは2021-11-01時点の日本語Wikipedia本文に基づく読解QAです。文脈なしでも成立する早押し問題とは限らないため、独立性と一意性の再審査が必要です。

改変・再配布時は各元データのライセンス、作成者、出典、変更点を維持してください。AI王の配布元は[ライセンス謝辞](https://sites.google.com/view/project-aio/dataset)、JQACは[配布ページ](https://taniokah.github.io/jqac/)、JGLUEは[公式リポジトリの説明・ライセンス](https://github.com/yahoojapan/JGLUE/blob/6f071c09316baae89c3d083a90985b4b1cb9968c/README.md)を参照してください。

取り込み時は設問長、同一設問、答え漏れ、仮のひらがな読みを機械処理しました。AI王とJSQuADの難易度3は暫定値です。JQACは作問者設定の値を保持していますが、いずれもこのリポジトリの難易度基準に照らした確認・試遊は未実施です。分類は自動初期割当て、タグは未審査の空欄です。対応表は [batch-016.jsonl](../data/imports/batch-016.jsonl)、件数・取得版・ハッシュは [manifest](../data/imports/batch-016-manifest.json) に記録しています。
