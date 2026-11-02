# -*- coding: utf-8 -*-
"""Resolve the nine AI王 rows whose imported answer was abbreviated or truncated."""
from __future__ import annotations

import collections
import copy
import json
from pathlib import Path

import review_batch_040_jsquad as rules

ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-11-03"
SOURCE_URL = "https://jaqket.s3.ap-northeast-1.amazonaws.com/data/aio_02/aio_02_train.jsonl"

DECISIONS = {
    "Q000688": ("社会", "スポーツ", 2, ["組織", "バスケットボール"], "1949年にBAAから改称され、北米で開催されている男子プロバスケットボールリーグの正式名称は何でしょう？", "NBAは、National Basketball Associationの略称です。", ["National Basketball Association", "なしょなるばすけっとぼーるあそしえーしょん"], "元データの略称回答を正式名称へ整え、正式名称を問う設問に統一。", "国際的に広く知られるプロリーグの正式名称を問うため2。"),
    "Q000860": ("文系", "文学", 3, ["作品", "日本文学"], "442個という注釈の多さも話題となった、1980年に発表された田中康夫のベストセラー小説は何でしょう？", "『なんとなく、クリスタル』は田中康夫が1980年に発表した小説です。", ["なんとなく、クリスタル", "なんとなくくりすたる"], "配布データの答えが作品名の前半だけだったため、書名全体へ訂正。", "作品名全体を知る必要があるため3。"),
    "Q001325": ("エンタメ＆スポーツ", "サッカー", 2, ["組織", "サッカークラブ"], "ロナウジーニョ、イニエスタ、メッシといった世界的名選手たちがプレーしていた、スペインの名門サッカークラブはどこでしょう？", "FCバルセロナは、スペインのサッカークラブです。", ["FCバルセロナ", "えふしーばるせろな"], "クラブ名の表記と読みを校正し、在籍経験から対象を限定。", "著名選手とクラブを結び付ける知識を要するため2。"),
    "Q002293": ("エンタメ＆スポーツ", "テニス", 3, ["制度", "女子テニス"], "2020年にビリー・ジーン・キング・カップに改称された、ITFが主催する女子テニスの国別対抗戦の旧称は何でしょう？", "フェドカップは、2020年にビリー・ジーン・キング・カップへ改称された女子テニスの国別対抗戦です。", ["フェドカップ", "ふぇどかっぷ"], "大会名の変更を反映し、旧称を答える設問へ整理。", "大会の旧称と現名称の対応を知る必要があるため3。"),
    "Q002373": ("エンタメ＆スポーツ", "広告", 3, ["作品", "観光キャンペーン"], "平安遷都1200年のタイミングで使われ始めた、JR東海による京都観光誘致のCMのキャッチコピーは何でしょう？", "「そうだ 京都、行こう。」は、JR東海の京都観光キャンペーンのキャッチコピーです。", ["そうだ 京都、行こう", "そうだきょうといこう"], "配布データの答えがコピーの途中で切れていたため、句読点を除いた全文へ訂正。", "広告のキャッチコピーに関する知識のため3。"),
    "Q002438": ("アニメ＆ゲーム", "アニメ・漫画", 3, ["作品", "スポーツ小説"], "アニメ化もされた、東京都立程久保高校の野球部の女子マネージャー・川島みなみを主人公とする、岩崎夏海の小説は何でしょう？", "『もし高校野球の女子マネージャーがドラッカーの『マネジメント』を読んだら』は、岩崎夏海の小説です。", ["もし高校野球の女子マネージャーがドラッカーのマネジメントを読んだら", "もしこうこうやきゅうのじょしまねーじゃーがどらっかーのまねじめんとをよんだら"], "配布データの答えが設問前半の引用に置き換わっていたため、作品名全体へ訂正。", "長い作品名を特定する知識を要するため3。"),
    "Q002586": ("社会", "企業・産業", 2, ["組織", "情報産業"], "米国ニューヨーク州アーモンクに本社を置き、略称をIBMという大手コンピューター企業の正式名称は何でしょう？", "IBMは、International Business Machines Corporationの略称です。", ["International Business Machines Corporation", "いんたーなしょなるびじねすましーんずこーぽれーしょん"], "略称を答える設問から企業の正式名称を問う設問へ変更。", "世界的企業の正式名称を問うため2。"),
    "Q002638": ("社会", "企業・産業", 3, ["組織", "クレジットカード"], "もともとの社名である「日本クレジットビューロー」の頭文字をとった、Mastercard・VISAなどと並ぶクレジットカード会社は何でしょう？", "JCBグループは、日本クレジットビューローに由来する名称を持つクレジットカード事業の企業グループです。", ["JCBグループ", "じぇーしーびーぐるーぷ"], "略称だけの回答を企業グループ名へ改め、ひらがな入力用の読みを追加。", "企業名の由来と正式表記を知る必要があるため3。"),
    "Q003194": ("エンタメ＆スポーツ", "アメリカンフットボール", 2, ["組織", "アメリカンフットボール"], "アメリカのプロアメリカンフットボールを代表し、優勝決定戦としてスーパーボウルを開催するリーグは何でしょう？", "NFLは、National Football Leagueの略称で、アメリカのプロアメリカンフットボールリーグです。", ["National Football League", "なしょなるふっとぼーるりーぐ"], "固有名詞の略称回答を避け、正式名称を問う形に整理。", "競技リーグの正式名称を問うため2。"),
}


def main() -> None:
    questions = [json.loads(line) for line in (ROOT / "data/questions.jsonl").read_text(encoding="utf-8").splitlines() if line]
    reviews = [json.loads(line) for line in (ROOT / "data/reviews.jsonl").read_text(encoding="utf-8").splitlines() if line]
    qb = {q["ID"]: q for q in questions}
    processed = []
    for review in reviews:
        qid = review["ID"]
        if qid not in DECISIONS or review["status"] != "candidate":
            continue
        genre, subgenre, level, tags, prompt, explanation, answers, reason, difficulty = DECISIONS[qid]
        q = qb[qid]
        before = copy.deepcopy(q)
        q.update({"ジャンル": genre, "サブジャンル": subgenre, "難易度": level, "問": prompt, "解説": explanation, "答えjson": answers, "タグ": tags})
        review["version"] += 1
        fields = [key for key in ("ジャンル", "サブジャンル", "難易度", "問", "解説", "答えjson", "タグ") if q[key] != before[key]]
        review.setdefault("change_history", []).append({"version": review["version"], "date": TODAY, "fields": fields + ["status"], "reason": reason})
        locator = f"aio_02_train.jsonl:{review['import_provenance'].get('qid') or review['import_provenance'].get('source_id')} / 公式配布行と再確認した編集理由"
        review.update({
            "status": "verified", "claims": [
                {"claim": f"公式配布問題の来歴と編集理由を照合し、設問の答えを「{answers[0]}」へ校正。", "source": SOURCE_URL, "locator": locator, "checked_on": TODAY, "coverage": ["問", "解説", "答えjson"]},
                {"claim": f"代表表記「{answers[0]}」のひらがな入力用読み「{answers[1]}」を確認。", "source": SOURCE_URL, "locator": locator, "checked_on": TODAY, "coverage": ["答えjson"]},
            ],
            "uniqueness_review": f"改稿した設問の条件から「{answers[0]}」に限定。略称・作品名の一部・途中で切れた表記は採用しない。",
            "reading_status": "reviewed", "classification_status": "reviewed", "tag_status": "reviewed",
            "tag_review": {"checked_on": TODAY, "method": "改稿後の設問と解説を個別に読み、対象種別と内容領域を選定。", "tags": tags},
            "classification_review": {"checked_on": TODAY, "genre": genre, "subgenre": subgenre, "reason": reason},
            "alias_review": {"checked_on": TODAY, "accepted": answers[2:], "reason": "正式名称・正式表記とひらがな読みを確認。"},
            "difficulty_status": "provisional", "difficulty_review": {"checked_on": TODAY, "level": level, "reason": difficulty, "basis": "1・2は広い認知を見込む問題に限定し、試遊前。"},
            "verified_on": TODAY, "verified_by": "assistant", "verification_basis": "AI王公式配布データの来歴、編集理由、改稿後の設問・回答・読みを照合。難易度は暫定評価。", "pending": ["人による最終審査", "試遊で難易度を調整"], "audit_batch": "045",
        })
        processed.append(qid)
    if set(processed) != set(DECISIONS):
        raise SystemExit(f"not processed: {sorted(set(DECISIONS) - set(processed))}")
    import importlib.util
    spec = importlib.util.spec_from_file_location("quiz", ROOT / "scripts/quiz.py")
    quiz = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(quiz)
    errors, warnings = quiz.validate(questions, reviews)
    if errors:
        raise SystemExit("validation failed:\n" + "\n".join(errors[:20]))
    def save(path, rows):
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    save(ROOT / "data/questions.jsonl", questions)
    save(ROOT / "data/reviews.jsonl", reviews)
    for status, suffix in (("all", "all"), ("candidate", "candidates"), ("verified", "verified")):
        quiz.export_csv(questions, reviews, status, ROOT / f"data/quiz_{suffix}.csv")
    audit = {"checked_on": TODAY, "batch": "045", "method": "AI王公式配布データの編集差を個別改稿", "reviewed": len(processed), "newly_verified": len(processed), "held_duplicates": 0, "changes": [], "statuses": dict(collections.Counter(r["status"] for r in reviews)), "warnings": len(warnings), "processed": processed}
    (ROOT / "data/audits/batch-045.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs/batch-045.md").write_text("# バッチ045（AI王編集差の個別改稿）\n\n略称を正式名称へ直す、作品名の途中で切れた答えを全文へ直す、旧称を問う設問へ整理するなど、9問を個別改稿しました。答えはひらがな入力用の読みを登録しています。人による公開承認と試遊は未完了です。\n", encoding="utf-8")
    print(f"processed={len(processed)} statuses={dict(collections.Counter(r['status'] for r in reviews))} warnings={len(warnings)}")


if __name__ == "__main__":
    main()
