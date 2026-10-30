# 進捗

- 2026-10-30：ユーザー提供の会話履歴から仕様を復元。既存コードなし。
- 350問の試作候補を作成。7ジャンル×5難易度×10問。問題文は36〜65文字程度、難易度は暫定。
- データは `data/questions.jsonl`、利用者向け出力は `data/quiz_candidates.csv`。列は履歴の最終仕様どおり。
- 判定は中黒・空白・全半角・ひらがな／カタカナを正規化し、登録した回答との完全一致で行う。任意の部分一致は使わない。
- 350問とも `candidate`。出典照合済み0問、人の公開承認済み0問。構造の検証と内容の事実確認を区別する。
- `python scripts/quiz.py validate` とユニットテストで、件数・配分・ID・表記揺れ・CSV往復・公開状態の除外を確認。
- 出典確認や人の審査が終わっていない問題を公開済みとして扱わない。

## 外部ブロッカー

2026-10-30、既存プロキシ経由の `https://ja.wikipedia.org/wiki/光合成` への接続はHTTP 403で拒否された。環境ステータスは `restricted / enforced`、カスタム許可先は空だった。TLSの検証やプロキシを無効にして回避していない。

環境設定の下書きに、Wikipediaと公式資料を調査するための21ホストを追加済み。保存は成功したが、実行環境へは未適用。ユーザーが環境設定で確認・保存し、環境を公開した後に接続を再確認する。秘密情報の追加は不要。

許可先：ja.wikipedia.org、www.nintendo.com、www.pokemon.co.jp、www.shonenjump.com、www.ghibli.jp、www.aozora.gr.jp、www.ndl.go.jp、www.kahaku.go.jp、www.nao.ac.jp、www.jma.go.jp、www.mext.go.jp、www.maff.go.jp、www.mhlw.go.jp、www.boj.or.jp、www.stat.go.jp、www.gsi.go.jp、elaws.e-gov.go.jp、laws.e-gov.go.jp、www.joc.or.jp、www.jfa.jp、www.npb.or.jp。

これらだけで全問の調査先が網羅されるとは限らない。実際の資料の所在を確認して、必要なホストだけを追加する。

## 次の作業

1. 実行環境の接続可否を再確認する。下書きの保存を接続成功とみなさない。
2. Q000001から順に、問題と解説に含まれる事実を資料で照合する。`research_entrypoints` は未参照の検索入口であり、引用元ではない。
3. `claims` に主張、`source` に実際に参照したURLまたは書誌、`locator` に該当箇所、`checked_on` に確認日を残す。
4. 別の正解対象がないこと、許容表記が過剰でないことを確認し、`uniqueness_review` に理由を記録する。修正時は同じIDの版を上げる。
5. 事実照合を完了したら `verified` にし、人の審査後に審査者と日付を付けて `approved` にする。AIだけで人の承認を代行しない。
6. 試遊で難易度を調整してから、次の500問へ進む。

## 保存方針

成果物は `himuhimu9191/Gen_Quiz` の `main` にコミット・プッシュする。一区切りごとにリモートのSHAとの一致を確認し、ローカルだけに置かない。ユーザーの会話履歴の原文や秘密情報はプッシュしない。
