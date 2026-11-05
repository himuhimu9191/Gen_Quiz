"""Import a bounded JaQuAD candidate batch without reloading quiz text into context."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import quiz
from pykakasi import kakasi

TODAY = "2026-11-05"
BATCH = "051"
FIRST_ID = 7001
TARGET_ADD = 3500
DATASET = "JaQuAD Japanese Question Answering Dataset"
LICENSE = "CC-BY-SA-3.0"
REPO_URL = "https://github.com/SkelterLabsInc/JaQuAD"
KAKASI = kakasi()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")


def sha256(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def hiragana(text: str) -> str:
    return "".join(part["hira"] for part in KAKASI.convert(text)).replace(" ", "")


def clean_answer(answer: str) -> str:
    answer = unicodedata.normalize("NFKC", answer).strip()
    answer = re.sub(r"\s+", "", answer)
    answer = answer.strip("「」『』")
    # A quiz asking for a title accepts the title itself, not a generic suffix.
    answer = re.sub(r"(?:シリーズ作品|シリーズ)$", "", answer)
    return answer


def normalize_prompt(prompt: str, title: str) -> str:
    prompt = re.sub(r"\s+", " ", prompt).strip()
    prompt = re.sub(r"[。.!?？]+$", "", prompt).strip() + "？"
    if len(prompt) < 35 and quiz.normalize(title) not in quiz.normalize(prompt):
        prompt = f"「{title}」に関する問題で、{prompt.rstrip('？')}？"
    return prompt


def answer_leaks(prompt: str, answer: str) -> bool:
    key = quiz.normalize(answer)
    if not key:
        return False
    return key in quiz.normalize(prompt)


def classify(title: str, prompt: str) -> tuple[str, str]:
    text = title + prompt
    rules = [
        (("アニメ", "漫画", "ゲーム", "任天堂", "ポケモン", "キャラクター"), "アニメ＆ゲーム", "作品"),
        (("スポーツ", "選手", "競技", "オリンピック", "サッカー", "野球", "映画", "音楽", "俳優", "芸能", "テレビ", "歌手"), "エンタメ＆スポーツ", "芸能・競技"),
        (("法律", "裁判", "政治", "首相", "国会", "都道府県", "都市", "国の", "地図", "駅", "鉄道", "経済", "通貨"), "社会", "地理・制度"),
        (("歴史", "文学", "小説", "詩人", "作家", "画家", "美術", "哲学", "神話", "宗教", "戦争"), "文系", "人文"),
        (("動物", "植物", "生物", "元素", "化学", "物理", "医学", "病気", "人体", "宇宙", "星", "数学", "気象", "地層", "科学"), "理系", "科学"),
        (("料理", "食品", "食べ物", "野菜", "果物", "健康", "体", "家計", "暮らし", "衣服", "家庭", "防災", "介護"), "生活", "暮らし"),
    ]
    for needles, genre, subgenre in rules:
        if any(needle in text for needle in needles):
            return genre, subgenre
    return "雑学", "一般知識"


def iter_rows(source_root: Path):
    for split in ("train", "dev"):
        for path in sorted((source_root / "data" / split).glob("*.json")):
            payload = read_json(path)
            for article_index, article in enumerate(payload.get("data", [])):
                title = article.get("title", "").strip()
                for paragraph_index, paragraph in enumerate(article.get("paragraphs", [])):
                    context = paragraph.get("context", "")
                    for qa in paragraph.get("qas", []):
                        answers = [a for a in qa.get("answers", []) if a.get("text", "").strip()]
                        if not title or not context or not answers or qa.get("is_impossible"):
                            continue
                        normalized_answers = {quiz.normalize(a["text"].strip()) for a in answers}
                        if len(normalized_answers) != 1:
                            continue
                        yield path, article_index, title, paragraph_index, context, qa, answers[0]


def make_candidate(path: Path, article_index: int, title: str, paragraph_index: int,
                   context: str, qa: dict, answer_row: dict, repo_url: str) -> dict | None:
    original_question = qa.get("question", "").strip()
    original_answer = answer_row["text"].strip()
    answer_start = answer_row.get("answer_start")
    if type(answer_start) is not int or context[answer_start:answer_start + len(original_answer)] != original_answer:
        return None
    prompt = normalize_prompt(original_question, title)
    answer = clean_answer(original_answer)
    if not answer or not 15 <= len(prompt) <= 100 or len(answer) > 30:
        return None
    reading = hiragana(answer)
    if not re.fullmatch(r"[ぁ-ゖー]+", reading or ""):
        return None
    if answer_leaks(prompt, answer) or answer_leaks(prompt, reading):
        return None
    genre, subgenre = classify(title, prompt)
    source_id = f"{path.parent.name}/{path.name}:{qa.get('id')}"
    answer_type = answer_row.get("answer_type")
    answer_kind = {"Person": "person", "Location": "place", "Object": "term"}.get(answer_type, "term")
    question = {
        "ジャンル": genre,
        "サブジャンル": subgenre,
        "難易度": 3,
        "問": prompt,
        "解説": f"「{title}」の本文中にある回答スパンをもとにした候補です。出典本文との事実照合が必要です。",
        "答えjson": [answer, reading],
        "タグ": [],
    }
    review = {
        "version": 1,
        "status": "candidate",
        "difficulty_status": "provisional",
        "research_entrypoints": [repo_url],
        "claims": [],
        "uniqueness_review": "",
        "reviewer": None,
        "reviewed_on": None,
        "time_sensitive": False,
        "reference_date": None,
        "recheck_on": None,
        "pending": [
            "出典本文との事実照合",
            "ひらがな読みの校正",
            "正解の一意性・許容表記の審査",
            "ジャンル・サブジャンル・難易度の再審査",
            "タグの確認",
            "人による最終審査",
        ],
        "answer_kind": answer_kind,
        "created_on": TODAY,
        "batch": BATCH,
        "import_provenance": {
            "dataset": DATASET,
            "source_id": source_id,
            "creator": "ByungHoon So / Kyuhong Byun / Kyungwon Kang / Seongjin Cho / Skelter Labs Inc. / JaQuAD annotators",
            "url": repo_url,
            "license": LICENSE,
            "original_question_sha256": sha256(original_question + "\n" + original_answer),
            "original_question": original_question,
            "original_answer": original_answer,
            "modifications": [
                "問題文・回答スパンを候補として転記",
                "短い設問に記事名の文脈を追加",
                "答えjsonの2番目にPykakasi 2.3.0による初期ひらがな読みを追加",
                "解説を候補用の出典本文参照文へ置換",
                "シリーズ名の一般分類語を代表解答から除外",
            ],
            "reading_method": "pykakasi_2.3.0",
            "source_file": path.name,
            "article_title": title,
            "article_index": article_index,
            "paragraph_index": paragraph_index,
            "context_sha256": sha256(context),
            "qas_id": qa.get("id"),
            "answer_start": answer_start,
            "answer_type": answer_type,
            "question_type": qa.get("question_type"),
        },
        "reading_status": "needs_review",
        "classification_status": "provisional",
        "tag_status": "pending",
    }
    return {"question": question, "review": review}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=Path(os.environ.get("TEMP", ".")) / "genquiz-jaquad-20261105")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--replace-batch", action="store_true", help="replace only the existing unreviewed batch 051")
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    if not source_root.exists():
        raise SystemExit(f"source root not found: {source_root}")
    commit = subprocess.check_output(["git", "-C", str(source_root), "rev-parse", "HEAD"], text=True).strip()
    repo_url = f"{REPO_URL}/tree/{commit}"

    questions = quiz.load(ROOT / "data/questions.jsonl")
    reviews = quiz.load(ROOT / "data/reviews.jsonl")
    batch_ids = {review["ID"] for review in reviews if review.get("batch") == BATCH}
    if batch_ids and not args.replace_batch:
        raise SystemExit("batch 051 already exists; use --replace-batch only while every row remains an untouched candidate")
    if batch_ids:
        if any(review.get("status") != "candidate" for review in reviews if review["ID"] in batch_ids):
            raise SystemExit("batch 051 contains reviewed rows and cannot be replaced")
        questions = [question for question in questions if question["ID"] not in batch_ids]
        reviews = [review for review in reviews if review["ID"] not in batch_ids]
    existing_prompts = {quiz.normalize(q["問"]) for q in questions}
    existing_source_ids = {
        (r.get("import_provenance") or {}).get("source_id")
        for r in reviews
        if (r.get("import_provenance") or {}).get("source_id")
    }
    pools: dict[str, list[dict]] = collections.defaultdict(list)
    rejects = {"duplicate_prompt": 0, "duplicate_source": 0, "invalid_candidate": 0}
    source_files: dict[str, str] = {}
    for path, article_index, title, paragraph_index, context, qa, answer_row in iter_rows(source_root):
        if path.name not in source_files:
            source_files[path.name] = sha256(path.read_bytes())
        item = make_candidate(path, article_index, title, paragraph_index, context, qa, answer_row, repo_url)
        if item is None:
            rejects["invalid_candidate"] += 1
            continue
        prompt_key = quiz.normalize(item["question"]["問"])
        source_id = item["review"]["import_provenance"]["source_id"]
        if source_id in existing_source_ids:
            rejects["duplicate_source"] += 1
            continue
        if prompt_key in existing_prompts:
            rejects["duplicate_prompt"] += 1
            continue
        pools[item["question"]["ジャンル"]].append(item)
        existing_prompts.add(prompt_key)
        existing_source_ids.add(source_id)

    genre_order = ("アニメ＆ゲーム", "文系", "理系", "生活", "雑学", "エンタメ＆スポーツ", "社会")
    quota = TARGET_ADD // len(genre_order)
    selected: list[dict] = []
    remaining: list[dict] = []
    for genre in genre_order:
        ordered = sorted(
            pools.get(genre, []),
            key=lambda item: sha256(item["review"]["import_provenance"]["source_id"]),
        )
        selected.extend(ordered[:quota])
        remaining.extend(ordered[quota:])
    if len(selected) < TARGET_ADD:
        remaining.sort(key=lambda item: sha256(item["review"]["import_provenance"]["source_id"]))
        selected.extend(remaining[:TARGET_ADD - len(selected)])
    selected = selected[:TARGET_ADD]

    summary = {
        "existing": len(questions),
        "selected": len(selected),
        "target_add": TARGET_ADD,
        "target_total": len(questions) + len(selected),
        "source": DATASET,
        "source_commit": commit,
        "source_files_seen": len(source_files),
        "eligible_pool_by_genre": {genre: len(pools.get(genre, [])) for genre in genre_order},
        "selected_by_genre": dict(collections.Counter(item["question"]["ジャンル"] for item in selected)),
        "eligible_pool_size": sum(len(items) for items in pools.values()),
        "rejects": rejects,
        "apply": args.apply,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if len(selected) != TARGET_ADD:
        raise SystemExit(f"Expected {TARGET_ADD} candidates, found {len(selected)}; no files changed.")
    if not args.apply:
        return

    for index, item in enumerate(selected, start=FIRST_ID):
        item["question"] = {"ID": f"Q{index:06d}", **item["question"]}
        item["review"]["ID"] = f"Q{index:06d}"
    questions.extend(item["question"] for item in selected)
    reviews.extend(item["review"] for item in selected)
    errors, warnings = quiz.validate(questions, reviews)
    if errors:
        raise SystemExit("validation failed:\n" + "\n".join(errors[:50]))
    write_jsonl(ROOT / "data/questions.jsonl", questions)
    write_jsonl(ROOT / "data/reviews.jsonl", reviews)
    write_jsonl(ROOT / "data/imports/batch-051.jsonl", [
        {"ID": item["question"]["ID"], **item["review"]["import_provenance"]} for item in selected
    ])
    for status, suffix in (("all", "all"), ("candidate", "candidates"), ("verified", "verified")):
        quiz.export_csv(questions, reviews, status, ROOT / f"data/quiz_{suffix}.csv")

    source_records = quiz.load(ROOT / "data/sources.jsonl")
    source_record = next((record for record in source_records if record.get("url") == repo_url), None)
    if source_record is None:
        source_record = {}
        source_records.append(source_record)
    source_record.update({
            "url": repo_url,
            "publisher": "ByungHoon So / Kyuhong Byun / Kyungwon Kang / Seongjin Cho / Skelter Labs Inc. / JaQuAD annotators",
            "section": "JaQuAD train and dev JSON files",
            "source_type": "repository",
            "repository_commit": commit,
            "sha256": sha256("".join(source_files.values())),
            "checked_on": TODAY,
            "license": LICENSE,
            "method": "公式リポジトリの固定コミットとCC BY-SA 3.0表示を確認。回答スパン、読み、回答範囲、分類、難易度、タグは候補として登録し、個別照合は未完了。",
            "read_sections": ["README / Data", "README / LICENSE", "data/train", "data/dev"],
            "dataset_file_sha256": source_files,
        })
    write_jsonl(ROOT / "data/sources.jsonl", source_records)
    manifest = {
        **summary,
        "added": TARGET_ADD,
        "batch": BATCH,
        "created_on": TODAY,
        "ids": {"first": f"Q{FIRST_ID:06d}", "last": f"Q{FIRST_ID + TARGET_ADD - 1:06d}"},
        "statuses": {"candidate": TARGET_ADD, "verified": 0, "approved": 0},
        "selection": {
            "prompt_characters": "15-100; add article-title context only when the title is not already in the prompt",
            "answer_max_characters": 30,
            "hiragana_reading": "Pykakasi 2.3.0 initial conversion; needs review",
            "duplicate_prompts_removed": True,
            "duplicate_source_ids_removed": True,
            "answer_leaks_in_prompt_removed": True,
            "series_suffix_removed": True,
        },
        "difficulty_distribution": {str(level): sum(item["question"]["難易度"] == level for item in selected) for level in range(1, 6)},
        "pending_review": ["source fact matching", "answer scope and aliases", "hiragana reading", "genre and subgenre", "difficulty", "tags", "human approval"],
        "source_url": repo_url,
        "source_file_sha256": source_files,
        "warnings": len(warnings),
    }
    (ROOT / "data/imports/batch-051-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audit = {
        "checked_on": TODAY,
        "batch": BATCH,
        "method": "JaQuAD固定コミットから回答スパンを候補として取り込み、構造・ID・正規化設問重複・読み形式を機械検査。事実照合は未完了。",
        "added": TARGET_ADD,
        "newly_verified": 0,
        "statuses": {"candidate": TARGET_ADD},
        "warnings": len(warnings),
        "rejects": rejects,
        "source_commit": commit,
        "source_files": source_files,
    }
    (ROOT / "data/audits/batch-051.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs/batch-051.md").write_text(
        f"# バッチ{BATCH}（JaQuAD候補3,500問）\n\n"
        f"JaQuADの固定コミットから **{TARGET_ADD:,}問** を候補として追加しました。IDは"
        f" `Q{FIRST_ID:06d}`〜`Q{FIRST_ID + TARGET_ADD - 1:06d}` です。問題文の短い行には記事名の文脈を補い、"
        "代表解答から「シリーズ」などの一般分類語を除き、Pykakasiで初期ひらがな読みを作りました。"
        "既存設問の正規化ハッシュとsource IDを照合し、衝突は取り込んでいません。\n\n"
        "3,500問はすべて `candidate` で、出典本文との個別照合、正解範囲、表記ゆれ、読み、"
        "ジャンル・サブジャンル、難易度、タグ、人による承認は未完了です。公開用のverified CSVには含めません。"
        "元ファイルを再配布せず、固定コミット・ファイルハッシュ・回答位置をレビュー台帳に保存しています。\n\n"
        "[マニフェスト](../data/imports/batch-051-manifest.json)／[監査記録](../data/audits/batch-051.json)\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
