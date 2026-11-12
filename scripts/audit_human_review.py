"""Extract difficult prompts and questionable answers for human review.

The report is intentionally a queue, not an automatic correction pass.  A
short fragment of a name is never added as an answer variant: only a reviewer
can approve a separately used name or notation.
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import quiz

TODAY = "2026-11-12"
QUESTION_FIELDS = (
    "ID", "ジャンル", "サブジャンル", "難易度", "問", "解説", "答えjson", "タグ"
)
GENERIC_OPENERS = (
    "に関する問題で",
    "についての問題で",
    "ある人物",
    "ある作品",
    "ある場所",
    "ある用語",
)
SUSPICIOUS_ANSWER_WORDS = re.compile(r"(?:など|もの|これ|それ|不明|未詳|？|\?)")
BRACKET_PAIRS = (
    ("（", "）"), ("「", "」"), ("『", "』"), ("【", "】"),
    ("〈", "〉"), ("［", "］"), ("《", "》"),
)


def normalized_answer(answer: str) -> str:
    return quiz.normalize(answer)


def first_clause(prompt: str) -> str:
    return re.split(r"[、，。！？!?]", prompt, maxsplit=1)[0].strip()


def answer_leaks(prompt: str, answers: list[str]) -> bool:
    normalized_prompt = quiz.normalize(prompt)
    for answer in answers:
        key = normalized_answer(answer)
        if len(key) < 3:
            continue
        remaining = normalized_prompt
        for token in re.findall(r"[ァ-ヺー]+", prompt):
            token_key = normalized_answer(token)
            if token_key != key and key in token_key:
                remaining = remaining.replace(token_key, "")
        if key in remaining:
            return True
    return False


def unbalanced_prompt(prompt: str) -> bool:
    return any(prompt.count(left) != prompt.count(right) for left, right in BRACKET_PAIRS)


def source_anchor(question: dict, review: dict) -> str | None:
    provenance = review.get("import_provenance") or {}
    title = str(provenance.get("article_title") or "").strip()
    if not title:
        return None
    prompt_key = quiz.normalize(question["問"])
    answer_key = quiz.normalize(question["答えjson"][0])
    title_key = quiz.normalize(title)
    if len(title_key) < 2 or title_key in prompt_key or title_key == answer_key:
        return None
    return title


def build_rows(questions: list[dict], reviews: list[dict]) -> list[dict]:
    review_by_id = {review["ID"]: review for review in reviews}
    answer_groups = collections.defaultdict(list)
    for question in questions:
        answer_groups[normalized_answer(question["答えjson"][0])].append(question["ID"])

    rows = []
    for question in questions:
        qid = question["ID"]
        review = review_by_id[qid]
        answers = question.get("答えjson") or []
        main = answers[0] if answers else ""
        reading = answers[1] if len(answers) > 1 else ""
        reasons = []
        hard_reasons = []
        prompt_length = len(question.get("問", ""))
        first = first_clause(question.get("問", ""))

        if prompt_length < 35:
            reasons.append("問題文が短く、途中で止めたときの手がかりが不足する可能性")
            hard_reasons.append("short_prompt")
        elif prompt_length > 100:
            reasons.append("問題文が長く、読み上げにくい")
            hard_reasons.append("long_prompt")
        if not question.get("問", "").rstrip().endswith(("？", "?")):
            reasons.append("問題文の終端が疑問形ではない")
            hard_reasons.append("prompt_ending")
        if unbalanced_prompt(question.get("問", "")):
            reasons.append("括弧または引用符の対応が不自然")
            hard_reasons.append("unbalanced_brackets")
        if re.search(r"[！？!?]{2,}|[、，。]{2,}|[ 　]{2,}", question.get("問", "")):
            reasons.append("句読点または空白が連続")
            hard_reasons.append("punctuation")
        if first and (len(first) < 12 or any(first.startswith(opener) for opener in GENERIC_OPENERS)):
            reasons.append("問題前半に答えを絞る識別語が不足する可能性")
            hard_reasons.append("weak_early_clue")

        if len(normalized_answer(main)) < 3:
            reasons.append("答えが短く、単独で使われる名称か確認が必要")
            hard_reasons.append("short_answer")
        if len(normalized_answer(reading)) < 3:
            reasons.append("読みが短く、表記・読みの一意性を確認する必要")
            hard_reasons.append("short_reading")
        if not re.fullmatch(r"[ぁ-ゖー]+", reading or ""):
            reasons.append("読みがひらがな入力の仕様に合わない")
            hard_reasons.append("reading_format")
        if SUSPICIOUS_ANSWER_WORDS.search(main):
            reasons.append("答えに一般語・未確定語が含まれる可能性")
            hard_reasons.append("suspicious_answer_word")
        if answer_leaks(question.get("問", ""), answers):
            reasons.append("問題文に答えまたは答えの語が露出")
            hard_reasons.append("answer_leak")
        if len(answer_groups[normalized_answer(main)]) > 1:
            reasons.append("同じ代表解答を持つ問題が複数あり、設問の一意性を確認")
        provenance = review.get("import_provenance") or {}
        if provenance.get("original_answer") and normalized_answer(provenance["original_answer"]) != normalized_answer(main):
            reasons.append("元資料の回答から表記または範囲を編集済み")
            hard_reasons.append("answer_edit")
        if review.get("status") == "candidate":
            reasons.append("出典・読み・回答範囲・分類・タグの審査が未完了")
        anchor = source_anchor(question, review)
        if anchor:
            reasons.append("前半に追加できる出典記事名候補あり")

        if not reasons:
            continue
        priority = "high" if hard_reasons else "review"
        rows.append({
            "ID": qid,
            "priority": priority,
            "reasons": reasons,
            "flags": hard_reasons,
            "genre": question.get("ジャンル"),
            "subgenre": question.get("サブジャンル"),
            "difficulty": question.get("難易度"),
            "status": review.get("status"),
            "question": question.get("問"),
            "answer": main,
            "reading": reading,
            "accepted_variants": answers[2:],
            "suggested_anchor": anchor,
            "suggested_action": (
                f"前半に「{anchor}」を自然な識別語として追加し、答えが一意になるか人手確認する。"
                if anchor else
                "実際に使われる正式な別名・表記差だけを出典で確認し、断片的な語は答えに追加しない。"
            ),
            "source_id": provenance.get("source_id") or provenance.get("qid"),
        })
    return rows


def write_outputs(rows: list[dict], output_dir: Path, date: str) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"human-review-{date}"
    jsonl_path = output_dir / f"{stem}.jsonl"
    csv_path = output_dir / f"{stem}.csv"
    summary_path = output_dir / f"{stem}-summary.json"
    with jsonl_path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    fields = [
        "ID", "priority", "flags", "reasons", "ジャンル", "サブジャンル", "難易度",
        "status", "問", "答え", "読み", "許容表記", "追加候補語", "人手確認案", "source_id",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "ID": row["ID"],
                "priority": row["priority"],
                "flags": json.dumps(row["flags"], ensure_ascii=False),
                "reasons": " / ".join(row["reasons"]),
                "ジャンル": row["genre"],
                "サブジャンル": row["subgenre"],
                "難易度": row["difficulty"],
                "status": row["status"],
                "問": row["question"],
                "答え": row["answer"],
                "読み": row["reading"],
                "許容表記": json.dumps(row["accepted_variants"], ensure_ascii=False),
                "追加候補語": row["suggested_anchor"] or "",
                "人手確認案": row["suggested_action"],
                "source_id": row["source_id"] or "",
            })
    summary = {
        "checked_on": date,
        "questions": len(quiz.load(ROOT / "data/questions.jsonl")),
        "queued": len(rows),
        "priority": dict(collections.Counter(row["priority"] for row in rows)),
        "flags": dict(collections.Counter(flag for row in rows for flag in row["flags"])),
        "candidate_rows": sum(row["status"] == "candidate" for row in rows),
        "policy": "意味のない断片・未使用名称は許容表記に自動追加しない。正式名称、実在する別名、確認済みの表記差のみ人手で登録する。",
        "files": {"jsonl": jsonl_path.name, "csv": csv_path.name},
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=TODAY)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/audits")
    args = parser.parse_args()
    questions = quiz.load(ROOT / "data/questions.jsonl")
    reviews = quiz.load(ROOT / "data/reviews.jsonl")
    summary = write_outputs(build_rows(questions, reviews), args.output_dir, args.date)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
