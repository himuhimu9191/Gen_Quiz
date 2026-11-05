"""Remove source labels from quiz display fields while preserving provenance."""
from __future__ import annotations

import collections
import copy
import json
import re
from pathlib import Path

import quiz

ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-11-05"
BATCH = "050"
SOURCE_TERMS = ("AI王", "project-aio", "aio_02", "QA20", "カプリティオ", "キュービック")
SOURCE_SENTENCE = re.compile(
    r"[^。！？]*(?:AI王|project-aio|aio_02|QA20|カプリティオ|キュービック)[^。！？]*[。！？]?",
    re.IGNORECASE,
)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")


def clean_explanation(value: str) -> str:
    cleaned = SOURCE_SENTENCE.sub("", value)
    cleaned = re.sub(r"[ \t\u3000]+", " ", cleaned).strip(" \t\u3000。！？")
    return cleaned + "。" if cleaned else ""


def main() -> None:
    questions = quiz.load(ROOT / "data/questions.jsonl")
    reviews = quiz.load(ROOT / "data/reviews.jsonl")
    review_by_id = {review["ID"]: review for review in reviews}
    changes = []

    for question in questions:
        review = review_by_id[question["ID"]]
        before = copy.deepcopy(question)
        fields = []

        explanation = clean_explanation(question["解説"])
        if explanation != question["解説"]:
            if not explanation:
                raise ValueError(f"Removing source note leaves no explanation: {question['ID']}")
            question["解説"] = explanation
            fields.append("解説")

        if "第1回AI王" in question["タグ"]:
            target_tag = question["サブジャンル"]
            question["タグ"] = [tag for tag in question["タグ"] if tag != "第1回AI王"]
            if target_tag not in question["タグ"]:
                question["タグ"].append(target_tag)
            fields.append("タグ")

        if not fields:
            continue

        review["version"] += 1
        reason = (
            "出題表示から出典照合注記と出典名タグを除去。内容領域タグには既に個別確認済みの "
            "サブジャンルを採用し、出典・作者・ライセンスの来歴は保持。"
        )
        review.setdefault("change_history", []).append(
            {
                "version": review["version"],
                "date": TODAY,
                "fields": fields,
                "reason": reason,
            }
        )
        if "タグ" in fields:
            review["tag_status"] = "reviewed"
            review["tag_review"] = {
                "checked_on": TODAY,
                "method": "出典名タグを除去し、既存の個別確認済みサブジャンルを内容領域タグへ採用。対象種別タグは保持。",
                "tags": question["タグ"],
            }
        changes.append(
            {
                "ID": question["ID"],
                "version": review["version"],
                "fields": fields,
                "reason": reason,
                "before": before,
                "after": copy.deepcopy(question),
            }
        )

    if not changes:
        print("No display source labels found; data is already clean.")
        return

    errors, warnings = quiz.validate(questions, reviews)
    if errors:
        raise ValueError("\n".join(errors[:50]))

    write_jsonl(ROOT / "data/questions.jsonl", questions)
    write_jsonl(ROOT / "data/reviews.jsonl", reviews)
    for status, suffix in (("all", "all"), ("candidate", "candidates"), ("verified", "verified")):
        quiz.export_csv(questions, reviews, status, ROOT / f"data/quiz_{suffix}.csv")

    statuses = collections.Counter(review["status"] for review in reviews)
    audit = {
        "checked_on": TODAY,
        "batch": BATCH,
        "method": "出題表示の出典注記・出典名タグを除去し、既存の審査済みサブジャンルを内容領域タグに採用。来歴台帳は保持。",
        "updated": len(changes),
        "newly_verified": 0,
        "statuses": dict(statuses),
        "tag_statuses": dict(collections.Counter(review["tag_status"] for review in reviews)),
        "warnings": len(warnings),
        "changes": changes,
    }
    with (ROOT / f"data/audits/batch-{BATCH}.json").open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    with (ROOT / f"docs/batch-{BATCH}.md").open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(
            f"# バッチ{BATCH}（出題表示の出典ラベル整理）\n\n"
        f"{len(changes):,}問の解説から出典照合注記を除き、出典名タグを個別確認済みの"
        "サブジャンルへ置き換えました。問題文・代表解答・読み・難易度は変更していません。"
        "事実確認状態を新たにverifiedへ変更していません。再配布条件に必要な出典・作者・"
        "ライセンスの記録は `data/reviews.jsonl`、`data/sources.jsonl`、"
        "`docs/import-licenses.md` とCSVのライセンスファイルに保持しています。\n\n"
        f"[変更前後と理由](../data/audits/batch-{BATCH}.json)。\n",
        )
    print(
        json.dumps(
            {
                "updated": len(changes),
                "statuses": dict(statuses),
                "tag_statuses": dict(collections.Counter(review["tag_status"] for review in reviews)),
                "warnings": len(warnings),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
