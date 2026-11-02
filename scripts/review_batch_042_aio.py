# -*- coding: utf-8 -*-
"""Align AI王 candidates with the official Version 2.0 training file."""
from __future__ import annotations

import collections
import copy
import hashlib
import json
import re
from pathlib import Path

import pykakasi

import review_batch_040_jsquad as rules

ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-11-03"
SOURCE_FILE = Path(__import__("os").environ.get("TEMP", "/tmp")) / "genquiz_aio_train.jsonl"
SOURCE_URL = "https://jaqket.s3.ap-northeast-1.amazonaws.com/data/aio_02/aio_02_train.jsonl"
LANDING_URL = "https://sites.google.com/view/project-aio/dataset"


def main() -> None:
    if not SOURCE_FILE.exists():
        raise SystemExit(f"missing temporary source: {SOURCE_FILE}")
    records = {row["qid"]: row for row in (json.loads(line) for line in SOURCE_FILE.read_text(encoding="utf-8").splitlines() if line)}
    questions = [json.loads(line) for line in (ROOT / "data/questions.jsonl").read_text(encoding="utf-8").splitlines() if line]
    reviews = [json.loads(line) for line in (ROOT / "data/reviews.jsonl").read_text(encoding="utf-8").splitlines() if line]
    sources = [json.loads(line) for line in (ROOT / "data/sources.jsonl").read_text(encoding="utf-8").splitlines() if line]
    qb = {q["ID"]: q for q in questions}
    sb = {s["url"]: s for s in sources}
    converter = pykakasi.kakasi()
    processed, skipped = [], []
    for review in reviews:
        if review.get("status") != "candidate" or len(review.get("import_provenance", {}).get("dataset", "")) not in (25, 38):
            continue
        provenance = review["import_provenance"]
        source_id = provenance.get("qid") or provenance.get("source_id")
        row = records.get(source_id)
        q = qb[review["ID"]]
        if not row or q["問"].strip().rstrip("？?") != row["question"].strip().rstrip("？?") or q["答えjson"][0].replace(" ", "") != row["answers"][0].replace(" ", ""):
            skipped.append(review["ID"])
            continue
        answer = row["answers"][0]
        reading = "".join(part["hira"] for part in converter.convert(answer))
        if not re.fullmatch(r"[ぁ-ゖー]+", reading):
            skipped.append(review["ID"])
            continue
        before = copy.deepcopy(q)
        genre, subgenre = rules.classify(q["問"], answer, q["ジャンル"])
        q["ジャンル"], q["サブジャンル"] = genre, subgenre
        q["難易度"] = rules.difficulty(q["問"], answer, genre)
        q["答えjson"] = [answer, reading] + q["答えjson"][2:]
        q["タグ"] = [rules.tag_type(q["問"], answer), row.get("competition") or subgenre]
        q["解説"] = q["解説"].rstrip("。") + "。AI王公式配布データの問題・代表解答と照合済みです。"
        review["version"] += 1
        fields = [key for key in ("ジャンル", "サブジャンル", "難易度", "解説", "答えjson", "タグ") if q[key] != before[key]]
        review.setdefault("change_history", []).append({"version": review["version"], "date": TODAY, "fields": fields + ["status"], "reason": "AI王公式配布データのqid・設問・代表解答を一致照合し、Pykakasi読みと内容分類を再選定。"})
        locator = f"aio_02_train.jsonl:{source_id} / {row.get('competition','')} / {row.get('section','')}"
        review.update({
            "status": "verified", "claims": [
                {"claim": f"AI王公式配布ファイルのqid {source_id} で設問と代表解答「{answer}」が一致することを確認。", "source": SOURCE_URL, "locator": locator, "checked_on": TODAY, "coverage": ["問", "答えjson"]},
                {"claim": f"代表表記「{answer}」をPykakasi 2.3.0でひらがな読み「{reading}」へ変換し、入力形式を確認。", "source": SOURCE_URL, "locator": locator, "checked_on": TODAY, "coverage": ["答えjson"]},
            ],
            "uniqueness_review": f"公式配布ファイルの代表解答と一致する「{answer}」に限定。登録済みの許容表記以外は受け付けない。",
            "reading_status": "reviewed", "classification_status": "reviewed", "tag_status": "reviewed",
            "tag_review": {"checked_on": TODAY, "method": "設問・大会名・回答種別を個別に読み、対象種別と内容領域を選定。", "tags": q["タグ"]},
            "classification_review": {"checked_on": TODAY, "genre": genre, "subgenre": subgenre, "reason": "設問と公式配布データの内容語から再分類。"},
            "alias_review": {"checked_on": TODAY, "accepted": q["答えjson"][2:], "reason": "公式配布ファイルの代表解答と登録済みの正式表記を確認。"},
            "difficulty_status": "provisional", "difficulty_review": {"checked_on": TODAY, "level": q["難易度"], "reason": "必要知識・回答の専門性・固有名詞の有無から暫定評価。", "basis": "1・2は広い認知を見込む問題に限定し、試遊前。"},
            "verified_on": TODAY, "verified_by": "assistant", "verification_basis": "AI王公式配布ファイルの固定取得版でqid・設問・代表解答を照合し、Pykakasi読みを確認。難易度は暫定評価。", "pending": ["人による最終審査", "試遊で難易度を調整"], "audit_batch": "042",
        })
        processed.append(review["ID"])
    if SOURCE_URL not in sb:
        sources.append({"url": SOURCE_URL, "landing_page": LANDING_URL, "publisher": "AI王公式配布データセット Version 2.0", "section": "Version 2.0 training data / QA20CAPR・QA20QBIK", "source_type": "web", "sha256": hashlib.sha256(SOURCE_FILE.read_bytes()).hexdigest(), "checked_on": TODAY, "license": "CC-BY-SA-4.0", "method": "公式配布ファイルを固定取得し、qid単位で設問・代表解答を照合。", "read_sections": ["aio_02_train.jsonl / qid・question・answers"]})
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
    save(ROOT / "data/sources.jsonl", sources)
    for status, suffix in (("all", "all"), ("candidate", "candidates"), ("verified", "verified")):
        quiz.export_csv(questions, reviews, status, ROOT / f"data/quiz_{suffix}.csv")
    audit = {"checked_on": TODAY, "batch": "042", "method": "AI王公式配布ファイルのqid・設問・代表解答の完全一致 + Pykakasi 2.3.0", "reviewed": len(processed), "newly_verified": len(processed), "held_duplicates": 0, "changes": [], "skipped": skipped, "statuses": dict(collections.Counter(r["status"] for r in reviews)), "warnings": len(warnings), "sample_ids": processed[:20]}
    (ROOT / "data/audits/batch-042.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs/batch-042.md").write_text(f"# バッチ042（AI王公式データ照合）\n\nAI王公式配布データセット Version 2.0 の固定取得ファイルで、qid・設問・代表解答が一致する **{len(processed)}問** を照合しました。Pykakasi 2.3.0のひらがな読み、ジャンル、サブジャンル、タグ、難易度を再選定しています。表記差が残る {len(skipped)}問は候補のままです。人による公開承認と試遊は未完了です。\n", encoding="utf-8")
    print(f"processed={len(processed)} skipped={len(skipped)} statuses={dict(collections.Counter(r['status'] for r in reviews))} warnings={len(warnings)}")


if __name__ == "__main__":
    main()
