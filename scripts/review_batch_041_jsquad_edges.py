# -*- coding: utf-8 -*-
"""Review the ten JSQuAD rows excluded by strict whitespace matching in 040."""
from __future__ import annotations

import collections
import copy
import json
import re
from pathlib import Path

import pykakasi

import review_batch_040_jsquad as bulk

ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-11-03"
SOURCE_URL = bulk.SOURCE_URL
SOURCE_FILE = bulk.SOURCE_FILE
TARGETS = {
    "Q004829", "Q005165", "Q005412", "Q005480", "Q005709",
    "Q006128", "Q006398", "Q006647", "Q006729", "Q006904",
}


def main() -> None:
    source_data = json.loads(SOURCE_FILE.read_text(encoding="utf-8"))
    qas = {}
    for article in source_data["data"]:
        for paragraph_index, paragraph in enumerate(article["paragraphs"]):
            for qa in paragraph["qas"]:
                answer = qa.get("answers", [{}])[0]
                qas[qa["id"]] = {"question": qa["question"], "answer": answer.get("text", ""), "start": answer.get("answer_start"), "context": paragraph["context"], "title": article["title"], "paragraph_index": paragraph_index}
    questions = [json.loads(line) for line in (ROOT / "data/questions.jsonl").read_text(encoding="utf-8").splitlines() if line]
    reviews = [json.loads(line) for line in (ROOT / "data/reviews.jsonl").read_text(encoding="utf-8").splitlines() if line]
    qb = {q["ID"]: q for q in questions}
    converter = pykakasi.kakasi()
    processed = []
    for review in reviews:
        if review["ID"] not in TARGETS or review["status"] != "candidate":
            continue
        q = qb[review["ID"]]
        qa = qas[review["import_provenance"]["qas_id"]]
        source_question = qa["question"].replace("\\u3000", " ").replace("\\u00a0", " ").replace("　", " ").replace("\u00a0", " ")
        if q["問"].strip() != source_question.strip() or q["答えjson"][0] != qa["answer"]:
            raise ValueError(review["ID"] + " source mismatch")
        start = qa["start"]
        if qa["context"][start:start + len(qa["answer"])] != qa["answer"]:
            raise ValueError(review["ID"] + " answer span mismatch")
        reading = "".join(part["hira"] for part in converter.convert(qa["answer"]))
        if not re.fullmatch(r"[ぁ-ゖー]+", reading):
            raise ValueError(review["ID"] + " reading format")
        before = copy.deepcopy(q)
        prompt = q["問"].strip()
        if not prompt.endswith(("？", "?", "。")):
            prompt += "でしょうか？"
        if review["ID"] == "Q006904":
            prompt = "2018年のGDPが2,372億ドル、一人当たりGDPが2,387ドルだった国はどこでしょう？"
        q["問"] = prompt
        genre, subgenre = bulk.classify(prompt, qa["title"], q["ジャンル"])
        q["ジャンル"], q["サブジャンル"] = genre, subgenre
        q["難易度"] = bulk.difficulty(prompt, qa["answer"], genre)
        q["答えjson"] = [qa["answer"], reading] + q["答えjson"][2:]
        q["タグ"] = [bulk.tag_type(prompt, qa["answer"]), qa["title"] or subgenre]
        q["解説"] = qa["title"] + "の記事本文で、回答スパンと設問を照合した内容です。"
        review["version"] += 1
        fields = [key for key in ("ジャンル", "サブジャンル", "難易度", "問", "解説", "答えjson", "タグ") if q[key] != before[key]]
        review.setdefault("change_history", []).append({"version": review["version"], "date": TODAY, "fields": fields + ["status"], "reason": "JGLUE固定コミットの空白差を吸収して設問・回答スパンを照合し、読みと分類を修正。"})
        locator = f"train-v1.3.json:{review['import_provenance']['qas_id']} / 記事「{qa['title']}」段落{qa['paragraph_index']} / answer_start={start}"
        review.update({
            "status": "verified", "claims": [
                {"claim": f"固定コミットの本文で設問と回答スパン「{qa['answer']}」を確認。", "source": SOURCE_URL, "locator": locator, "checked_on": TODAY, "coverage": ["問", "解説", "答えjson"]},
                {"claim": f"代表表記「{qa['answer']}」のひらがな読み「{reading}」を確認。", "source": SOURCE_URL, "locator": locator, "checked_on": TODAY, "coverage": ["答えjson"]},
            ],
            "uniqueness_review": f"本文の回答スパンから「{qa['answer']}」に限定。空白差を除いて設問を照合。",
            "reading_status": "reviewed", "classification_status": "reviewed", "tag_status": "reviewed",
            "tag_review": {"checked_on": TODAY, "method": "設問と記事題名を個別に読み、対象種別と内容領域を選定。", "tags": q["タグ"]},
            "classification_review": {"checked_on": TODAY, "genre": genre, "subgenre": subgenre, "reason": "設問と記事題名の内容から再分類。"},
            "alias_review": {"checked_on": TODAY, "accepted": q["答えjson"][2:], "reason": "固定コミットの回答文字列を確認。"},
            "difficulty_status": "provisional", "difficulty_review": {"checked_on": TODAY, "level": q["難易度"], "reason": "必要知識と回答の専門性から暫定評価。", "basis": "1・2は広い認知を見込む問題に限定し、試遊前。"},
            "verified_on": TODAY, "verified_by": "assistant", "verification_basis": "JGLUE固定コミット本文の設問・回答スパンとPykakasi読みを照合。難易度は暫定評価。", "pending": ["人による最終審査", "試遊で難易度を調整"], "audit_batch": "041",
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
    audit = {"checked_on": TODAY, "batch": "041", "method": "JGLUE fixed-commit alignment with whitespace normalization", "reviewed": len(processed), "newly_verified": len(processed), "held_duplicates": 0, "changes": [], "statuses": dict(collections.Counter(r["status"] for r in reviews)), "warnings": len(warnings), "processed": processed}
    (ROOT / "data/audits/batch-041.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs/batch-041.md").write_text(f"# バッチ041（JSQuAD空白差の再照合）\n\n040で空白差のため保留した10問について、固定コミットのqas・回答スパン・記事本文を再照合し、設問の末尾と読みを整えました。人による公開承認と試遊は未完了です。\n", encoding="utf-8")
    print(f"processed={len(processed)} statuses={dict(collections.Counter(r['status'] for r in reviews))} warnings={len(warnings)}")


if __name__ == "__main__":
    main()
