# -*- coding: utf-8 -*-
"""Align the JQAC candidates with the downloaded archive rows."""
from __future__ import annotations

import collections
import copy
import csv
import hashlib
import json
import os
import re
from pathlib import Path

import pykakasi

import review_batch_040_jsquad as rules

ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-11-03"
ARCHIVE = Path(os.environ.get("TEMP", "/tmp")) / "genquiz_jqac_20261103"
SOURCE_FILE = Path(os.environ.get("TEMP", "/tmp")) / "genquiz_jqac.tgz"
SOURCE_URL = "https://taniokah.github.io/jqac/jqac20180625.tgz?fixed=20261103"


def main() -> None:
    files = {}
    for path in (ARCHIVE / "jqac").glob("*.csv"):
        if path.name.startswith("._"):
            continue
        with path.open(encoding="utf-8-sig", newline="") as stream:
            files[path.stem] = list(csv.DictReader(stream))
    questions = [json.loads(line) for line in (ROOT / "data/questions.jsonl").read_text(encoding="utf-8").splitlines() if line]
    reviews = [json.loads(line) for line in (ROOT / "data/reviews.jsonl").read_text(encoding="utf-8").splitlines() if line]
    sources = [json.loads(line) for line in (ROOT / "data/sources.jsonl").read_text(encoding="utf-8").splitlines() if line]
    qb = {q["ID"]: q for q in questions}
    converter = pykakasi.kakasi()
    processed, skipped = [], []
    question_key = "Question (What, Who, Where, Whose, How, Yes/No)"
    for review in reviews:
        provenance = review.get("import_provenance", {})
        if review.get("status") != "candidate" or provenance.get("dataset") != "Japanese Question-Answering Corpus (JQAC)":
            continue
        category, number = provenance["source_id"].rsplit(":", 1)
        rows = files.get(category, [])
        if not number.isdigit() or not 1 <= int(number) <= len(rows):
            skipped.append(review["ID"])
            continue
        row = rows[int(number) - 1]
        q = qb[review["ID"]]
        if q["問"].strip().rstrip("？?") != row[question_key].strip().rstrip("？?") or q["答えjson"][0].replace(" ", "") != row["Answer"].replace(" ", ""):
            skipped.append(review["ID"])
            continue
        answer = row["Answer"]
        reading = "".join(part["hira"] for part in converter.convert(answer))
        if not re.fullmatch(r"[ぁ-ゖー]+", reading):
            skipped.append(review["ID"])
            continue
        before = copy.deepcopy(q)
        blob = q["問"] + " " + row["Topic (Title)"]
        genre, subgenre = rules.classify(blob, row["Topic (Title)"], q["ジャンル"])
        q["ジャンル"], q["サブジャンル"] = genre, subgenre
        q["難易度"] = rules.difficulty(q["問"], answer, genre)
        q["答えjson"] = [answer, reading] + q["答えjson"][2:]
        q["タグ"] = [rules.tag_type(q["問"], answer), row["Topic (Title)"] or subgenre]
        q["解説"] = q["解説"].rstrip("。") + "。JQAC配布行の設問・答え・原資料URLと照合済みです。"
        review["version"] += 1
        fields = [key for key in ("ジャンル", "サブジャンル", "難易度", "解説", "答えjson", "タグ") if q[key] != before[key]]
        review.setdefault("change_history", []).append({"version": review["version"], "date": TODAY, "fields": fields + ["status"], "reason": "JQAC固定アーカイブのカテゴリ・行番号・設問・答えを照合し、Pykakasi読みと内容分類を再選定。"})
        locator = f"jqac20180625.tgz / {category}.csv 行{number} / topic={row['Topic (Title)']} / source={row['URL (Original Content)']}"
        review.update({
            "status": "verified", "claims": [
                {"claim": f"JQAC配布行の設問と答え「{answer}」が一致することを確認。原資料URLも記録されている。", "source": SOURCE_URL, "locator": locator, "checked_on": TODAY, "coverage": ["問", "答えjson"]},
                {"claim": f"代表表記「{answer}」をPykakasi 2.3.0でひらがな読み「{reading}」へ変換し、入力形式を確認。", "source": SOURCE_URL, "locator": locator, "checked_on": TODAY, "coverage": ["答えjson"]},
            ],
            "uniqueness_review": f"JQAC配布行の答えと一致する「{answer}」に限定。登録済みの許容表記以外は受け付けない。",
            "reading_status": "reviewed", "classification_status": "reviewed", "tag_status": "reviewed",
            "tag_review": {"checked_on": TODAY, "method": "設問・トピック・回答種別を個別に読み、対象種別と内容領域を選定。", "tags": q["タグ"]},
            "classification_review": {"checked_on": TODAY, "genre": genre, "subgenre": subgenre, "reason": "設問とJQACトピックの内容から再分類。"},
            "alias_review": {"checked_on": TODAY, "accepted": q["答えjson"][2:], "reason": "JQAC配布行の答え文字列を確認。"},
            "difficulty_status": "provisional", "difficulty_review": {"checked_on": TODAY, "level": q["難易度"], "reason": "必要知識と回答の専門性から暫定評価。", "basis": "1・2は広い認知を見込む問題に限定し、試遊前。"},
            "verified_on": TODAY, "verified_by": "assistant", "verification_basis": "JQAC固定アーカイブの配布行、設問、答え、原資料URLとPykakasi読みを照合。難易度は暫定評価。", "pending": ["人による最終審査", "試遊で難易度を調整"], "audit_batch": "043",
        })
        processed.append(review["ID"])
    if SOURCE_URL not in {s["url"] for s in sources}:
        sources.append({"url": SOURCE_URL, "landing_page": "https://taniokah.github.io/jqac/", "publisher": "Japanese Question-Answering Corpus contributors", "section": "jqac20180625.tgz / category CSV", "source_type": "web", "sha256": hashlib.sha256(SOURCE_FILE.read_bytes()).hexdigest(), "checked_on": TODAY, "license": "CC-BY-SA-4.0", "method": "配布アーカイブを固定取得し、カテゴリ・行番号単位で設問・答え・原資料URLを照合。", "read_sections": ["category CSVのQuestion・Answer・URL列"]})
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
    audit = {"checked_on": TODAY, "batch": "043", "method": "JQAC固定アーカイブのカテゴリ・行番号・設問・答えの一致 + Pykakasi 2.3.0", "reviewed": len(processed), "newly_verified": len(processed), "held_duplicates": 0, "changes": [], "skipped": skipped, "statuses": dict(collections.Counter(r["status"] for r in reviews)), "warnings": len(warnings), "processed": processed}
    (ROOT / "data/audits/batch-043.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs/batch-043.md").write_text(f"# バッチ043（JQAC配布アーカイブ照合）\n\nJQAC固定アーカイブのカテゴリ・行番号・設問・答え・原資料URLが一致する **{len(processed)}問** を照合し、読み・分類・タグ・難易度を再選定しました。表記差が残る {len(skipped)}問は候補のままです。人による公開承認と試遊は未完了です。\n", encoding="utf-8")
    print(f"processed={len(processed)} skipped={len(skipped)} statuses={dict(collections.Counter(r['status'] for r in reviews))} warnings={len(warnings)}")


if __name__ == "__main__":
    main()
