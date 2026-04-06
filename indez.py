import os
import argparse
import logging
from typing import List, Dict, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import mysql.connector


DEFAULT_DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "pte_questions",
}


API_MAP = {
    "MCQSingleAnswer": "https://backend22.languageacademy.com.au/api/v2/question/14",
    "MCQMultipleAnswer": "https://backend22.languageacademy.com.au/api/v2/question/15",
    "MultipleTypeSingleAnswer": "https://backend22.languageacademy.com.au/api/v2/question/8",
    "MultipleTypeMultipleAnswer": "https://backend22.languageacademy.com.au/api/v2/question/9",
    "HighlightCorrectSummary": "https://backend22.languageacademy.com.au/api/v2/question/17",
    "SelectMissingWord": "https://backend22.languageacademy.com.au/api/v2/question/18",
}


def make_session(retries: int = 3, backoff: float = 0.3) -> requests.Session:
    s = requests.Session()
    retry = Retry(total=retries, backoff_factor=backoff, status_forcelist=(500, 502, 503, 504))
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


def get_db_connection(db_config: Dict[str, str]):
    return mysql.connector.connect(**db_config)


def fetch_questions(cursor) -> List[Dict[str, Any]]:
    query = """
    SELECT id, question_type
    FROM questions
    WHERE question_type IN (
        'MCQSingleAnswer',
        'MCQMultipleAnswer',
        'MultipleTypeSingleAnswer',
        'MultipleTypeMultipleAnswer',
        'HighlightCorrectSummary',
        'SelectMissingWord'
    )
    ORDER BY id DESC
    """
    cursor.execute(query)
    return cursor.fetchall()


def process_question(sess: requests.Session, headers: Dict[str, str], q: Dict[str, Any], cursor, conn) -> None:
    qid = q["id"]
    qtype = q.get("question_type")
    logging.info("Processing QID %s (%s)", qid, qtype)

    api_url = API_MAP.get(qtype)
    if not api_url:
        logging.debug("No API mapping for type %s", qtype)
        return

    params = {
        "prediction": 0,
        "search": "",
        "type": 1,
        "mark": "all",
        "attempted": "all",
        "complexity": "all",
        "orderby": "desc",
        "practice": "true",
        "filterByVid": "none",
        "open_ques": 1,
        "qid": qid,
    }

    resp = sess.get(api_url, headers=headers, params=params, timeout=15)
    if resp.status_code != 200:
        logging.warning("API returned %s for QID %s", resp.status_code, qid)
        return

    data = resp.json()
    content = data.get("data")
    if not content:
        logging.warning("No data for QID %s", qid)
        return

    # data may be a list or dict
    question_data = content[0] if isinstance(content, list) else content
    options = question_data.get("option") or question_data.get("options") or []
    if not options:
        logging.info("No options for QID %s", qid)
        return

    # prepare batch rows
    rows = []
    for opt in options:
        text = opt.get("options") or opt.get("text") or ""
        is_correct = int(bool(opt.get("correct") or opt.get("is_correct")))
        sort_order = opt.get("index") if opt.get("index") is not None else None
        rows.append((qid, text, is_correct, sort_order))

    try:
        # Use transaction: delete old, insert new
        cursor.execute("DELETE FROM question_options WHERE question_id = %s", (qid,))
        insert_query = (
            "INSERT INTO question_options (question_id, option_text, is_correct, sort_order)"
            " VALUES (%s, %s, %s, %s)"
        )
        cursor.executemany(insert_query, rows)
        conn.commit()
        logging.info("Updated QID %s with %d options", qid, len(rows))
    except Exception:
        conn.rollback()
        logging.exception("DB error while updating QID %s", qid)


def main():
    parser = argparse.ArgumentParser(description="Sync question options from API into DB")
    parser.add_argument("--token", help="API bearer token (or set API_TOKEN env)")
    parser.add_argument("--db-host", default=os.environ.get("DB_HOST", DEFAULT_DB_CONFIG["host"]))
    parser.add_argument("--db-user", default=os.environ.get("DB_USER", DEFAULT_DB_CONFIG["user"]))
    parser.add_argument("--db-pass", default=os.environ.get("DB_PASS", DEFAULT_DB_CONFIG["password"]))
    parser.add_argument("--db-name", default=os.environ.get("DB_NAME", DEFAULT_DB_CONFIG["database"]))
    args = parser.parse_args()

    token = args.token or os.environ.get("API_TOKEN")
    if not token:
        parser.error("API token is required via --token or API_TOKEN env")

    db_config = {
        "host": args.db_host,
        "user": args.db_user,
        "password": args.db_pass,
        "database": args.db_name,
    }

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    sess = make_session()
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    conn = get_db_connection(db_config)
    cursor = conn.cursor(dictionary=True)

    try:
        questions = fetch_questions(cursor)
        logging.info("Total Questions: %d", len(questions))

        # Reuse DB cursor/connection for updates
        # Use a separate cursor for updates to avoid interfering with fetch cursor depending on connector behavior
        upd_cursor = conn.cursor()
        for q in questions:
            try:
                process_question(sess, headers, q, upd_cursor, conn)
            except Exception:
                logging.exception("Unexpected error processing QID %s", q.get("id"))
        upd_cursor.close()

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()