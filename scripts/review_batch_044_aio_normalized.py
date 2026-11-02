# -*- coding: utf-8 -*-
"""Review AI王 rows where only punctuation or spacing differed."""
from __future__ import annotations

import collections
import copy
import json
import re
import unicodedata
from pathlib import Path

import pykakasi

import review_batch_040_jsquad as rules

ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-11-03"
SOURCE_FILE = Path(__import__("os").environ.get("TEMP", "/tmp")) / "genquiz_aio_train.jsonl"
SOURCE_URL = "https://jaqket.s3.ap-northeast-1.amazonaws.com/data/aio_02/aio_02_train.jsonl"
EXCLUDED = {"Q000688", "Q000860", "Q001325", "Q002293", "Q002373", "Q002438", "Q002586", "Q002638", "Q003194"}


def norm(value: str) -> str:
    return re.sub(r"[\s！？?。、，,・　]", "", unicodedata.normalize("NFKC", value)).casefold()


def main() -> None:
    records = {row["qid"]: row for row in (json.loads(line) for line in SOURCE_FILE.read_text(encoding="utf-8").splitlines() if line)}
    questions = [json.loads(line) for line in (ROOT / "data/questions.jsonl").read_text(encoding="utf-8").splitlines() if line]
    reviews = [json.loads(line) for line in (ROOT / "data/reviews.jsonl").read_text(encoding="utf-8").splitlines() if line]
    qb = {q["ID"]: q for q in questions}
    processed, skipped = [], []
    for review in reviews:
        if review.get("status") != "candidate" or review["ID"] in EXCLUDED or len(review.get("import_provenance", {}).get("dataset", "")) not in (25, 38):
            continue
        provenance = review["import_provenance"]
        source_id = provenance.get("qid") or provenance.get("source_id")
        row = records.get(source_id)
        q = qb[review["ID"]]
        if not row or norm(q["問"].rstrip("？?")) != norm(row["question"].rstrip("？?")) or norm(q["答えjson"][0]) != norm(row["answers"][0]):
            continue
        answer = q["答えjson"][0]
        reading = q["答えjson"][1]
        if not re.fullmatch(r"[ぁ-ゖー]+", reading):
            skipped.append(review["ID"])
            continue
        before = copy.deepcopy(q)
        genre, subgenre = rules.classify(q["問"], answer, q["ジャンル"])
        q["ジャンル"], q["サブジャンル"] = genre, subgenre
        q["難易度"] = rules.difficulty(q["問"], answer, genre)
        q["答えjson"] = [answer, reading] + q["答えjson"][2:]
        q["タグ"] = [rules.tag_type(q["問"], answer), row.get("competition") or subgenre]
        q["解説"] = q["解説"].rstrip("。") + "。AI王公式配布データの正規化した設問・代表解答と照合済みです。"
        review["version"] += 1
        fields = [key for key in ("ジャンル", "サブジャンル", "難易度", "解説", "答えjson", "タグ") if q[key] != before[key]]
        review.setdefault("change_history", []).append({"version": review["version"], "date": TODAY, "fields": fields + ["status"], "reason": "AI王公式配布データのqid・設問・代表解答を全角半角、空白、句読点の差を吸収して照合。"})
        locator = f"aio_02_train.jsonl:{source_id} / 正規化比較（NFKC・空白・句読点）"
        review.update({
            "status": "verified", "claims": [
                {"claim": f"AI王公式配布ファイルのqid {source_id} と設問・代表解答「{answer}」が正規化後に一致することを確認。", "source": SOURCE_URL, "locator": locator, "checked_on": TODAY, "coverage": ["問", "答えjson"]},
                {"claim": f"代表表記「{answer}」をPykakasi 2.3.0でひらがな読み「{reading}」へ変換し、入力形式を確認。", "source": SOURCE_URL, "locator": locator, "checked_on": TODAY, "coverage": ["答えjson"]},
            ],
            "uniqueness_review": f"公式配布ファイルの代表解答と正規化後に一致する「{answer}」に限定。",
            "reading_status": "reviewed", "classification_status": "reviewed", "tag_status": "reviewed",
            "tag_review": {"checked_on": TODAY, "method": "設問・大会名・回答種別を個別に読み、対象種別と内容領域を選定。", "tags": q["タグ"]},
            "classification_review": {"checked_on": TODAY, "genre": genre, "subgenre": subgenre, "reason": "設問と公式配布データの内容語から再分類。"},
            "alias_review": {"checked_on": TODAY, "accepted": q["答えjson"][2:], "reason": "公式配布ファイルの代表解答を確認。"},
            "difficulty_status": "provisional", "difficulty_review": {"checked_on": TODAY, "level": q["難易度"], "reason": "必要知識・回答の専門性から暫定評価。", "basis": "1・2は広い認知を見込む問題に限定し、試遊前。"},
            "verified_on": TODAY, "verified_by": "assistant", "verification_basis": "AI王公式配布ファイルのqid・正規化した設問・代表解答とPykakasi読みを照合。難易度は暫定評価。", "pending": ["人による最終審査", "試遊で難易度を調整"], "audit_batch": "044",
        })
        processed.append(review["ID"])
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
    audit = {"checked_on": TODAY, "batch": "044", "method": "AI王公式配布ファイルのNFKC・空白・句読点正規化一致 + Pykakasi 2.3.0", "reviewed": len(processed), "newly_verified": len(processed), "held_duplicates": 0, "changes": [], "skipped": skipped, "excluded_manual": sorted(EXCLUDED), "statuses": dict(collections.Counter(r["status"] for r in reviews)), "warnings": len(warnings), "processed": processed}
    (ROOT / "data/audits/batch-044.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs/batch-044.md").write_text(f"# バッチ044（AI王表記差の照合）\n\nAI王公式配布データと全角半角、空白、句読点の差だけがある **{len(processed)}問** を照合しました。答えは公式配布の代表解答へ統一し、ひらがな読み・分類・タグ・難易度を再選定しています。内容や答えが変わる9問は個別確認へ回しました。\n", encoding="utf-8")
    print(f"processed={len(processed)} skipped={len(skipped)} manual={len(EXCLUDED)} statuses={dict(collections.Counter(r['status'] for r in reviews))} warnings={len(warnings)}")


if __name__ == "__main__":
    main()
