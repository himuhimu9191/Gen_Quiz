"""Import licensed quiz and QA candidates for batch 016; never marks them verified."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TEMP = Path(os.environ["TEMP"]) / "genquiz_sources"
sys.path.insert(0, str(ROOT / "scripts"))
import quiz
from pykakasi import kakasi

TODAY = "2026-11-03"
FIRST_ID = 3509
TARGET_ADD = 3492
JGLUE_COMMIT = subprocess.check_output(["git", "-C", str(TEMP / "jglue"), "rev-parse", "HEAD"], text=True).strip()
JGLUE_JSQUAD_URL = f"https://github.com/yahoojapan/JGLUE/tree/{JGLUE_COMMIT}/datasets/jsquad-v1.3"
JSQUAD_FILES = ("train-v1.3.json", "valid-v1.3.json", "test-v1.3.json")
GENRE_MAP = {
    "学問": ("文系", "学問"),
    "技術": ("理系", "技術"),
    "自然": ("理系", "自然科学"),
    "社会": ("社会", "社会"),
    "地理": ("社会", "地理"),
    "人間": ("雑学", "人間"),
    "文化": ("文系", "文化"),
    "歴史": ("文系", "歴史"),
    "徳島大学シラバス": ("文系", "大学"),
}
LOOK_MAP = {
    "color": ("理系", "色彩", 2),
    "spot": ("雑学", "観察", 2),
    "kanji": ("文系", "漢字", 2),
    "brain": ("雑学", "パズル", 2),
    "memory": ("雑学", "記憶", 2),
    "fruit": ("生活", "食品", 1),
    "flower-kanji": ("文系", "漢字", 2),
    "animal-kanji": ("文系", "漢字", 2),
    "food-kanji": ("文系", "漢字", 2),
    "weather-kanji": ("文系", "漢字", 2),
    "idioms": ("文系", "言葉", 2),
    "proverbs": ("文系", "言葉", 2),
    "keigo": ("文系", "言葉", 2),
    "old-months": ("文系", "日本文化", 2),
    "prefectures": ("社会", "地理", 2),
    "world-capitals": ("社会", "地理", 2),
    "world-landmarks": ("社会", "地理", 2),
    "japan-landmarks": ("社会", "地理", 2),
    "solar-system": ("理系", "天文学", 2),
    "stars": ("理系", "天文学", 2),
    "weather-science": ("理系", "気象", 2),
    "ocean": ("理系", "地学", 2),
    "mountains": ("理系", "地理", 2),
    "animal-facts": ("理系", "動物", 2),
    "birds": ("理系", "動物", 2),
    "insects": ("理系", "動物", 2),
    "plants": ("理系", "植物", 2),
    "vegetables": ("生活", "食品", 1),
    "sushi": ("生活", "料理", 1),
    "noodles": ("生活", "料理", 1),
    "tea": ("生活", "食品", 1),
    "coffee": ("生活", "食品", 1),
    "baking": ("生活", "料理", 1),
    "kitchen-science": ("生活", "料理", 2),
    "nutrition": ("生活", "健康", 2),
    "body": ("理系", "人体", 2),
    "dental": ("生活", "健康", 2),
    "sleep-science": ("生活", "健康", 2),
    "exercise": ("生活", "健康", 2),
    "hygiene": ("生活", "健康", 1),
    "currency": ("社会", "経済", 2),
    "budget": ("生活", "家計", 2),
    "interest": ("生活", "家計", 2),
    "shopping-math": ("生活", "家計", 2),
    "insurance": ("生活", "制度", 2),
    "credit": ("生活", "家計", 2),
    "fraud": ("社会", "防犯", 2),
    "recycling": ("生活", "環境", 2),
    "energy": ("理系", "エネルギー", 2),
    "safety": ("生活", "防災", 2),
    "internet": ("生活", "情報", 2),
    "passwords": ("生活", "情報", 2),
    "photography": ("エンタメ＆スポーツ", "写真", 2),
    "music": ("エンタメ＆スポーツ", "音楽", 2),
    "art-history": ("文系", "美術", 2),
    "literature": ("文系", "文学", 2),
    "history": ("文系", "歴史", 2),
    "sports": ("エンタメ＆スポーツ", "スポーツ", 2),
    "board-games": ("アニメ＆ゲーム", "ゲーム", 2),
    "number-patterns": ("理系", "数学", 2),
    "logic": ("理系", "数学", 2),
    "fractions": ("理系", "数学", 2),
    "time-math": ("理系", "数学", 2),
    "shapes": ("理系", "数学", 2),
    "english": ("文系", "英語", 2),
    "flags": ("社会", "地理", 2),
    "flowers": ("理系", "植物", 2),
    "gardening": ("生活", "園芸", 1),
    "senior-home": ("生活", "福祉", 2),
    "care-words": ("生活", "福祉", 2),
}

KAKASI = kakasi()


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git_file_bytes(relative_path):
    return subprocess.check_output([
        "git", "-C", str(TEMP / "jglue"), "show", f"{JGLUE_COMMIT}:{relative_path}"
    ])


def hiragana(text):
    return "".join(part["hira"] for part in KAKASI.convert(text)).replace(" ", "")


def has_answer_leak(question, answer):
    key = quiz.normalize(answer)
    if len(key) < 3:
        return False
    checked = question
    for token in re.findall(r"[ァ-ヺー]+", question):
        normalized = quiz.normalize(token)
        if key != normalized and key in normalized:
            checked = checked.replace(token, "")
    return key in quiz.normalize(checked)


def heuristic_category(question, answer):
    text = question + " " + answer
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


def make_item(source, qid, prompt, answer, explanation, genre, subgenre, difficulty,
              source_url, license_id, creator, dataset, source_id, extra=None):
    prompt = re.sub(r"\s+", " ", prompt).strip()
    answer = re.sub(r"\s+", " ", answer).strip()
    if not prompt or not answer or any(p in answer for p in ("・", "･")):
        return None, "empty_or_punctuated_answer"
    if not 35 <= len(prompt) <= 100 or len(answer) > 30:
        return None, "length_out_of_range"
    reading = hiragana(answer)
    if not reading or not re.fullmatch(r"[ぁ-ゖー]+", reading):
        return None, "reading_not_hiragana"
    if has_answer_leak(prompt, answer) or has_answer_leak(prompt, reading):
        return None, "answer_in_prompt"
    item = {
        "source": source,
        "source_id": source_id,
        "question": {
            "ジャンル": genre,
            "サブジャンル": subgenre,
            "難易度": difficulty,
            "問": prompt,
            "解説": explanation.strip(),
            "答えjson": [answer, reading],
            "タグ": [],
        },
        "review": {
            "version": 1,
            "status": "candidate",
            "difficulty_status": "provisional",
            "research_entrypoints": [source_url],
            "claims": [],
            "uniqueness_review": "",
            "reviewer": None,
            "reviewed_on": None,
            "time_sensitive": False,
            "reference_date": None,
            "recheck_on": None,
            "pending": ["出典本文との照合", "ひらがな読みの校正", "正解の一意性・許容表記の審査", "ジャンル・サブジャンル・難易度の再審査", "タグの確認", "人による最終審査"],
            "answer_kind": "term",
            "created_on": TODAY,
            "batch": "016",
            "import_provenance": {
                "dataset": dataset,
                "source_id": source_id,
                "creator": creator,
                "url": source_url,
                "license": license_id,
                "original_question_sha256": sha256(prompt + "\n" + answer),
                "modifications": ["問題文・代表解答を原資料から転記", "答えjsonの2番目にPykakasi 2.3.0による初期ひらがな読みを追加", "解説を付加または原資料から転記"],
                "reading_method": "pykakasi_2.3.0",
            },
            "reading_status": "needs_review",
            "classification_status": "provisional",
            "tag_status": "pending",
        },
    }
    if extra:
        item["review"]["import_provenance"].update(extra)
    return item, None


def load_aio(existing_ids):
    path = Path(os.environ["TEMP"]) / "aio_02_train.jsonl"
    used_source_ids = set(existing_ids)
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if not row["qid"].startswith(("QA20CAPR-", "QA20QBIK-")) or row["qid"] in used_source_ids:
            continue
        prompt, answer = row["question"], row["answers"][0]
        genre, subgenre = heuristic_category(prompt, answer)
        extra = {"source_question_date": row.get("timestamp"), "source_section": row.get("section")}
        item, _ = make_item("aio", row["qid"], prompt, answer,
                            f"この問題は、出典データで「{answer}」を正解としています。", genre,
                            subgenre, 3, "https://sites.google.com/view/project-aio/dataset",
                            "CC-BY-SA-4.0", "株式会社キュービック / クイズ法人カプリティオ",
                            "AI王公式配布データセット Version 2.0", row["qid"], extra)
        if item:
            item["review"]["import_provenance"]["source_question_sha256"] = sha256(json.dumps(row, ensure_ascii=False, sort_keys=True))
            result.append(item)
    return result


def load_jqac():
    result = []
    folder = TEMP / "jqac" / "jqac"
    for path in sorted(folder.glob("*.csv")):
        if path.name.startswith("._"):
            continue
        with path.open(encoding="utf-8", newline="") as stream:
            for index, row in enumerate(csv.DictReader(stream), start=1):
                category = row["Theme (Category)"].strip()
                genre, subgenre = GENRE_MAP.get(category, ("雑学", "一般知識"))
                prompt, answer = row["Question (What, Who, Where, Whose, How, Yes/No)"], row["Answer"]
                ref = row["URL (Original Content)"].strip()
                source_id = f"{path.stem}:{index}"
                item, _ = make_item("jqac", source_id, prompt, answer,
                                    f"「{row['Topic (Title)'].strip()}」に関する問題です。", genre,
                                    subgenre, int(row["Difficulty (by Author)"] or 3),
                                    "https://taniokah.github.io/jqac/", "CC-BY-SA-4.0",
                                    "JQAC contributors", "Japanese Question-Answering Corpus (JQAC)",
                                    source_id, {"reference_url": ref, "topic": row["Topic (Title)"].strip(), "source_category": category})
                if item:
                    result.append(item)
    return result


def load_lookquiz():
    data = read_json(TEMP / "lookquiz.json")
    result = []
    for row in data["questions"]:
        genre, subgenre, difficulty = LOOK_MAP[row["quiz_id"]]
        prompt = row["question"]
        answer = row["correct_answer"]
        item, _ = make_item("lookquiz", f"{row['quiz_id']}:{row['question_number']}", prompt, answer,
                            row["explanation"], genre, subgenre, difficulty,
                            "https://lookquiz.net/open-quiz-dataset/", "CC-BY-4.0", "LookQuiz",
                            "LookQuiz 日本語4択クイズ・オープンデータセット", f"{row['quiz_id']}:{row['question_number']}",
                            {"quiz_url": row["quiz_url"], "reference_urls": row["reference_urls"], "last_reviewed": row["last_reviewed"], "options": row["options"]})
        if item:
            result.append(item)
    return result


def load_jglue():
    folder = TEMP / "jglue" / "datasets" / "jcommonsenseqa-v1.3"
    result = []
    for name in ("train-v1.3.json", "valid-v1.3.json", "test-v1.3.json"):
        path = folder / name
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            answer = row[f"choice{row['label']}"]
            genre, subgenre = heuristic_category(row["question"], answer)
            if genre == "雑学":
                genre, subgenre = "生活", "一般常識"
            source_id = f"{name}:{row['q_id']}"
            item, _ = make_item("jglue", source_id, row["question"], answer,
                                "日常的な知識をもとに答える問題です。選択肢から答えを選びます。",
                                genre, subgenre, 1, "https://github.com/yahoojapan/JGLUE",
                                "CC-BY-SA-4.0", "Yahoo Japan Corporation / Waseda University Kawahara Lab",
                                "JGLUE JCommonsenseQA v1.3", source_id,
                                {"split": name, "q_id": row["q_id"], "choices": [row[f"choice{i}"] for i in range(5)]})
            if item:
                result.append(item)
    return result


def load_jsquad():
    folder = TEMP / "jglue" / "datasets" / "jsquad-v1.3"
    result = []
    for name in ("train-v1.3.json", "valid-v1.3.json", "test-v1.3.json"):
        data = read_json(folder / name)
        for article in data["data"]:
            title = article["title"]
            for paragraph_index, paragraph in enumerate(article["paragraphs"]):
                context = paragraph["context"].split("[SEP]", 1)[-1].strip()
                for qa in paragraph["qas"]:
                    if qa.get("is_impossible") or not qa.get("answers"):
                        continue
                    answers = {quiz.normalize(a["text"].strip()) for a in qa["answers"] if a.get("text", "").strip()}
                    if len(answers) != 1:
                        continue
                    answer = qa["answers"][0]["text"].strip()
                    prompt = qa["question"].strip()
                    genre, subgenre = heuristic_category(title + " " + prompt, answer)
                    source_id = f"{name}:{qa['id']}"
                    item, _ = make_item("jsquad", source_id, prompt, answer,
                                        f"「{title}」の本文にある記述をもとにした問題です。",
                                        genre, subgenre, 3, JGLUE_JSQUAD_URL,
                                        "CC-BY-SA-4.0", "Yahoo Japan Corporation / Waseda University Kawahara Lab",
                                        "JGLUE JSQuAD v1.3", source_id,
                                        {"split": name, "article_title": title, "paragraph_index": paragraph_index,
                                         "context_sha256": sha256(context), "qas_id": qa["id"]})
                    if item:
                        result.append(item)
    return result


def load_existing():
    questions = read_jsonl(ROOT / "data/questions.jsonl")
    reviews = read_jsonl(ROOT / "data/reviews.jsonl")
    imported_ids = {r["ID"] for r in reviews if r.get("batch") == "016"}
    questions = [q for q in questions if q["ID"] not in imported_ids]
    reviews = [r for r in reviews if r.get("batch") != "016"]
    return questions, reviews


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write the selected candidate records")
    args = parser.parse_args()
    questions, reviews = load_existing()
    existing_prompts = {quiz.normalize(q["問"]) for q in questions}
    existing_source_ids = {r.get("import_provenance", {}).get("source_id") for r in reviews}
    existing_source_ids.update(r.get("import_provenance", {}).get("qid") for r in reviews)
    pools = {"aio": load_aio(existing_source_ids), "jqac": load_jqac(), "lookquiz": load_lookquiz(), "jsquad": load_jsquad(), "jglue": load_jglue()}
    selected = []
    rejected = {name: {"duplicate_prompt": 0, "duplicate_source": 0} for name in pools}
    for name in ("aio", "jqac", "lookquiz", "jsquad", "jglue"):
        for item in pools[name]:
            prompt_key = quiz.normalize(item["question"]["問"])
            source_id = item["review"]["import_provenance"]["source_id"]
            if source_id in existing_source_ids:
                rejected[name]["duplicate_source"] += 1
                continue
            if prompt_key in existing_prompts:
                rejected[name]["duplicate_prompt"] += 1
                continue
            if len(selected) < TARGET_ADD:
                selected.append(item)
                existing_prompts.add(prompt_key)
                existing_source_ids.add(source_id)
        if len(selected) >= TARGET_ADD:
            break
    print(json.dumps({"existing": len(questions), "pool_counts": {k: len(v) for k, v in pools.items()},
                      "rejected": rejected, "selected": len(selected),
                      "source_counts": {k: sum(x['source'] == k for x in selected) for k in pools},
                      "target_total": len(questions) + len(selected), "apply": args.apply}, ensure_ascii=True, indent=2))
    if len(selected) != TARGET_ADD:
        raise SystemExit(f"Expected {TARGET_ADD} candidates, found {len(selected)}; no files changed.")
    if not args.apply:
        return
    for index, item in enumerate(selected, start=FIRST_ID):
        item["question"] = {"ID": f"Q{index:06d}", **item["question"]}
        item["review"]["ID"] = f"Q{index:06d}"
    questions.extend(item["question"] for item in selected)
    reviews.extend(item["review"] for item in selected)
    def write_jsonl(path, rows):
        Path(path).write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    write_jsonl(ROOT / "data/questions.jsonl", questions)
    write_jsonl(ROOT / "data/reviews.jsonl", reviews)
    write_jsonl(ROOT / "data/imports/batch-016.jsonl", [
        {"ID": item["question"]["ID"], **item["review"]["import_provenance"]} for item in selected
    ])
    sources = read_jsonl(ROOT / "data/sources.jsonl")
    jsquad_bytes = {name: git_file_bytes(f"datasets/jsquad-v1.3/{name}") for name in JSQUAD_FILES}
    source_records = [
        {
            "url": "https://jaqket.s3.ap-northeast-1.amazonaws.com/data/aio_02/aio_02_train.jsonl",
            "landing_page": "https://sites.google.com/view/project-aio/dataset",
            "publisher": "AI王公式配布データセット Version 2.0",
            "section": "Version 2.0 training data / QA20CAPR・QA20QBIK",
            "source_type": "dataset",
            "sha256": file_sha(Path(os.environ["TEMP"]) / "aio_02_train.jsonl"),
            "checked_on": TODAY,
            "license": "CC-BY-SA-4.0",
            "method": "公式ページで分割データとライセンスを確認し、配布ファイルの取得版を固定。各問題の事実・読み・分類・タグは未審査の候補として登録。",
            "read_sections": ["Version 2.0 / training data", "license and acknowledgments"],
        },
        {
            "url": "https://taniokah.github.io/jqac/jqac20180625.tgz",
            "landing_page": "https://taniokah.github.io/jqac/",
            "publisher": "Japanese Question-Answering Corpus contributors",
            "section": "jqac20180625.tgz",
            "source_type": "dataset",
            "sha256": file_sha(TEMP / "jqac.tgz"),
            "checked_on": TODAY,
            "license": "CC-BY-SA-4.0",
            "method": "配布ページでライセンスと形式を確認し、配布アーカイブの取得版を固定。問題文・答え・原資料URL・読み・分類・タグは未審査の候補として登録。",
            "read_sections": ["What's JQAC?", "Categories", "Format", "Download"],
        },
        {
            "url": JGLUE_JSQUAD_URL,
            "publisher": "Yahoo Japan Corporation / Waseda University Kawahara Lab",
            "section": "JGLUE JSQuAD v1.3; Japanese Wikipedia snapshot dated 2021-11-01",
            "source_type": "repository",
            "repository_commit": JGLUE_COMMIT,
            "sha256": hashlib.sha256(b"".join(jsquad_bytes[name] for name in JSQUAD_FILES)).hexdigest(),
            "checked_on": TODAY,
            "license": "CC-BY-SA-4.0",
            "method": "JGLUE READMEのデータ仕様とライセンス、固定コミットのJSQuAD配布ファイルを取得。問題と答えの事実・読み・一意性・分類は未審査の候補として登録。",
            "read_sections": ["README / JSQuAD", "README / License", "datasets/jsquad-v1.3"],
            "dataset_file_sha256": {name: hashlib.sha256(jsquad_bytes[name]).hexdigest() for name in JSQUAD_FILES},
        },
    ]
    replaced_publishers = {source["publisher"] for source in source_records}
    sources = [source for source in sources if source.get("publisher") not in replaced_publishers]
    known_urls = {source["url"] for source in sources}
    sources.extend(source for source in source_records if source["url"] not in known_urls)
    write_jsonl(ROOT / "data/sources.jsonl", sources)
    manifest = {
        "batch": "016",
        "created_on": TODAY,
        "ids": {"first": "Q003509", "last": "Q007000"},
        "added": len(selected),
        "total": len(questions),
        "statuses": {"candidate": len(selected), "verified": 0, "approved": 0},
        "source_counts": {name: sum(item["source"] == name for item in selected) for name in pools},
        "source_ids": {"first_aio": "QA20CAPR-0022", "aio_eligible_ids": 1532},
        "selection": {"prompt_characters": "35-100", "answer_max_characters": 30, "hiragana_reading": "Pykakasi 2.3.0 initial conversion; needs review", "duplicate_prompts_removed": True, "answer_leaks_in_prompt_removed": True},
        "difficulty_distribution": {str(level): sum(item["question"]["難易度"] == level for item in selected) for level in range(1, 6)},
        "pending_review": ["source fact matching", "answer uniqueness and aliases", "hiragana reading", "genre and subgenre", "difficulty", "tags", "human approval"],
        "sources": [source["url"] for source in source_records],
        "unit_tests": None,
        "structural_errors": None,
    }
    (ROOT / "data/imports/batch-016-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
