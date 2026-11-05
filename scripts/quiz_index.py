"""Build a local compact index and report only conflicts in one review batch."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import quiz

DB_PATH = ROOT / "work" / "quiz-index.sqlite"


def rows(path: Path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def open_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY,
            prompt_key TEXT NOT NULL,
            answer_key TEXT NOT NULL,
            source_id TEXT,
            genre TEXT NOT NULL,
            subgenre TEXT NOT NULL,
            difficulty INTEGER NOT NULL,
            status TEXT NOT NULL
        )
    """)
    connection.execute("CREATE INDEX IF NOT EXISTS item_prompt_key ON items(prompt_key)")
    connection.execute("CREATE INDEX IF NOT EXISTS item_source_id ON items(source_id)")
    connection.execute("CREATE INDEX IF NOT EXISTS item_answer_key ON items(answer_key)")
    connection.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    return connection


def rebuild(connection: sqlite3.Connection) -> tuple[int, str]:
    questions_path = ROOT / "data/questions.jsonl"
    reviews_path = ROOT / "data/reviews.jsonl"
    reviews = {review["ID"]: review for review in rows(reviews_path)}
    connection.execute("DELETE FROM items")
    count = 0
    with connection:
        for question in rows(questions_path):
            review = reviews.get(question["ID"], {})
            provenance = review.get("import_provenance") or {}
            answers = question.get("答えjson") or []
            answer_key = json.dumps([quiz.normalize(answer) for answer in answers], ensure_ascii=False)
            connection.execute(
                "INSERT INTO items VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    question["ID"],
                    quiz.normalize(question["問"]),
                    answer_key,
                    provenance.get("source_id") or provenance.get("qid"),
                    question["ジャンル"],
                    question["サブジャンル"],
                    question["難易度"],
                    review.get("status", "unknown"),
                ),
            )
            count += 1
        digest = file_sha(questions_path)
        connection.execute("INSERT OR REPLACE INTO meta VALUES ('questions_sha256', ?)", (digest,))
        connection.execute("INSERT OR REPLACE INTO meta VALUES ('questions_count', ?)", (str(count),))
    return count, digest


def ensure_current(connection: sqlite3.Connection) -> tuple[int, str, bool]:
    current = file_sha(ROOT / "data/questions.jsonl")
    indexed = connection.execute("SELECT value FROM meta WHERE key='questions_sha256'").fetchone()
    if not indexed or indexed[0] != current:
        count, current = rebuild(connection)
        return count, current, True
    count = int(connection.execute("SELECT value FROM meta WHERE key='questions_count'").fetchone()[0])
    return count, current, False


def check_batch(connection: sqlite3.Connection, batch: str) -> dict:
    import_path = ROOT / f"data/imports/batch-{batch}.jsonl"
    if not import_path.exists():
        raise SystemExit(f"missing import ledger: {import_path}")
    ids = {row["ID"] for row in rows(import_path)}
    if not ids:
        raise SystemExit(f"empty import ledger: {import_path}")
    connection.execute("DROP TABLE IF EXISTS selected_batch")
    connection.execute("CREATE TEMP TABLE selected_batch (id TEXT PRIMARY KEY)")
    connection.executemany("INSERT INTO selected_batch VALUES (?)", ((item_id,) for item_id in ids))
    new_rows = []
    for question in rows(ROOT / "data/questions.jsonl"):
        if question["ID"] in ids:
            answers = question.get("答えjson") or []
            answer_key = json.dumps([quiz.normalize(answer) for answer in answers], ensure_ascii=False)
            new_rows.append((question["ID"], quiz.normalize(question["問"]), answer_key))
    if len(new_rows) != len(ids):
        return {"batch": batch, "ledger_ids": len(ids), "question_rows": len(new_rows), "missing_ids": len(ids) - len(new_rows)}
    connection.executemany(
        "UPDATE items SET prompt_key=?, answer_key=? WHERE id=?",
        ((prompt, answer, item_id) for item_id, prompt, answer in new_rows),
    )
    prompt_collisions = connection.execute("""
        SELECT COUNT(*) FROM items i
        WHERE i.id IN (SELECT id FROM selected_batch)
          AND EXISTS (SELECT 1 FROM items old WHERE old.prompt_key=i.prompt_key
                      AND old.id NOT IN (SELECT id FROM selected_batch))
    """).fetchone()[0]
    source_collisions = connection.execute("""
        SELECT COUNT(*) FROM items i
        WHERE i.id IN (SELECT id FROM selected_batch) AND i.source_id IS NOT NULL
          AND EXISTS (SELECT 1 FROM items old WHERE old.source_id=i.source_id
                      AND old.id NOT IN (SELECT id FROM selected_batch))
    """).fetchone()[0]
    within_batch_duplicates = connection.execute("""
        SELECT COUNT(*) FROM (
            SELECT prompt_key FROM items WHERE id IN (SELECT id FROM selected_batch)
            GROUP BY prompt_key HAVING COUNT(*) > 1
        )
    """).fetchone()[0]
    shared_answers = connection.execute("""
        SELECT COUNT(*) FROM (
            SELECT answer_key FROM items WHERE id IN (SELECT id FROM selected_batch)
            GROUP BY answer_key HAVING COUNT(*) > 1
        )
    """).fetchone()[0]
    status_counts = dict(connection.execute(
        "SELECT status, COUNT(*) FROM items WHERE id IN (SELECT id FROM selected_batch) GROUP BY status"
    ).fetchall())
    return {
        "batch": batch,
        "rows": len(new_rows),
        "statuses": status_counts,
        "prompt_collisions_with_existing": prompt_collisions,
        "source_id_collisions_with_existing": source_collisions,
        "duplicate_prompt_groups_within_batch": within_batch_duplicates,
        "shared_answer_groups_review_manually": shared_answers,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("rebuild", help="rebuild the local compact index")
    check = sub.add_parser("check", help="check a batch and print counts only")
    check.add_argument("batch", help="three-digit batch number, e.g. 051")
    args = parser.parse_args()
    connection = open_db()
    try:
        if args.command == "rebuild":
            count, digest = rebuild(connection)
            rebuilt = True
        else:
            count, digest, rebuilt = ensure_current(connection)
        if args.command == "check":
            report = check_batch(connection, args.batch)
            report.update({"indexed_questions": count, "questions_sha256": digest, "index_rebuilt": rebuilt})
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"indexed_questions": count, "questions_sha256": digest, "index": str(DB_PATH)}, ensure_ascii=False, indent=2))
    finally:
        connection.close()


if __name__ == "__main__":
    main()
