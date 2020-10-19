import enum
import json
import sqlite3
from collections import defaultdict
from typing import List, Optional, Dict, Any

from rimejudge.project import RimeProject
import multiprocessing
from datetime import datetime
from pathlib import Path

from rimejudge.rime.languages import RimeLanguage
import rimejudge.util

DB_SQL = Path(__file__).parent.parent / "sql" / "contestdb.sql"
WA_PENALTY = 20 * 60


class SubmissionStatus(enum.Enum):
    SUBMITTED = "Submitted", False
    JUDGING = "Judging", False
    ACCEPTED = "Accepted", True
    TIME_LIMIT_EXCEEDED = "Time Limit Exceeded", True
    WRONG_ANSWER = "Wrong Answer", True
    COMPILE_ERROR = "Compile Error", True

    def __init__(self, display_name: str, judged: bool):
        self.display_name = display_name
        self.judged = judged


class ContestDB:
    def __init__(self, db_file: Path):
        self.db_file = db_file

    def get_connection(self):
        return sqlite3.connect(str(self.db_file))

    def ensure_tables(self):
        conn = self.get_connection()
        cur = conn.cursor()
        with DB_SQL.open() as f:
            cur.executescript(f.read())
        cur.close()
        conn.commit()
        conn.close()

    def add_solution(self, problem_id: str, contestant_id: str, solution_id: str, language: RimeLanguage, source: str) -> int:
        conn = self.get_connection()
        cur = conn.cursor()
        now = int(datetime.now().timestamp())
        cur.execute(
            "INSERT INTO submissions (problem_id, contestant_id, solution_id, language, status, source, submit_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (problem_id, contestant_id, solution_id, language.name, SubmissionStatus.SUBMITTED.name, source, now))
        submission_id = cur.lastrowid
        cur.close()
        conn.commit()
        conn.close()
        return submission_id

    def get_standings_submissions(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        start_timestamp = int(start_time.timestamp())
        end_timestamp = int(end_time.timestamp())
        cur.execute("SELECT * FROM submissions WHERE ? <= submit_time AND submit_time < ? ORDER BY submit_time", (start_timestamp, end_timestamp))
        submissions = cur.fetchall()
        cur.close()
        conn.close()
        return submissions

    def get_contestant_submissions(self, contestant_id: str) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM submissions WHERE contestant_id = ?",
                    (contestant_id,))
        submissions = cur.fetchall()
        cur.close()
        conn.close()
        return submissions

    def get_all_submissions(self) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM submissions")
        submissions = cur.fetchall()
        cur.close()
        conn.close()
        return submissions

    def get_submission_by_id(self, submission_id: int) -> Dict[str, Any]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
        submission = cur.fetchone()
        cur.close()
        conn.close()
        return submission

    def update_submission_status(self, submission_id: int, status: SubmissionStatus):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("UPDATE submissions SET status = ? WHERE id = ?", (status.name, submission_id))
        cur.close()
        conn.commit()
        conn.close()


def _worker_process(rime: RimeProject, db: ContestDB, judge_queue: multiprocessing.Queue):
    while True:
        submission_id = judge_queue.get()
        db.update_submission_status(submission_id, SubmissionStatus.JUDGING)
        submission = db.get_submission_by_id(submission_id)
        problem_id = submission["problem_id"]
        solution_id = submission["solution_id"]
        rime.run_command("judge", problem_id, solution_id)
        project_dir = Path(rime.project_dir)
        judge_out_dir = project_dir / problem_id / "rime-out" / solution_id
        status = SubmissionStatus.ACCEPTED
        found_accepted = False
        for judge_out_file in judge_out_dir.iterdir():
            if judge_out_file.is_dir():
                continue
            if not judge_out_file.name.endswith("cache"):
                continue
            with judge_out_file.open() as f:
                result = json.load(f)
            verdict = result["verdict"]
            if verdict == "Accepted":
                found_accepted = True
            elif verdict == "Time Limit Exceeded":
                status = SubmissionStatus.TIME_LIMIT_EXCEEDED
            else:
                status = SubmissionStatus.WRONG_ANSWER
        if not found_accepted:
            status = SubmissionStatus.COMPILE_ERROR
        db.update_submission_status(submission_id, status)


class Contest:
    def __init__(self, rime: RimeProject, start_time: datetime, end_time: datetime, n_workers: int, db: ContestDB):
        self.rime = rime
        self.start_time = start_time
        self.end_time = end_time
        workers = []
        self.judge_queue = multiprocessing.Queue()
        self.db = db
        self.problem_ids = None
        for _ in range(n_workers):
            worker = multiprocessing.Process(target=_worker_process, args=(rime, db, self.judge_queue))
            worker.start()
            workers.append(worker)
        self.workers = workers

    def submit(self, contestant_id: str, problem_id: str, language: RimeLanguage, source: str):
        solution_id = contestant_id + "_" + rimejudge.util.generate_random_code()
        self.rime.add_solution(problem_id, solution_id, language, source)
        submission_id = self.db.add_solution(problem_id, contestant_id, solution_id, language, source)
        self.judge_queue.put(submission_id)

    def get_problem_ids(self) -> List[str]:
        if self.problem_ids is None:
            self.problem_ids = []
            for subdir in Path(self.rime.project_dir).iterdir():
                if not subdir.is_dir():
                    continue
                problem_file = subdir / "PROBLEM"
                if problem_file.exists():
                    self.problem_ids.append(subdir.name)
        return self.problem_ids

    def get_standings(self) -> List[Dict[str, Any]]:
        submissions = self.db.get_standings_submissions(self.start_time, self.end_time)
        wa_counts = defaultdict(lambda: defaultdict(int))
        penalties = defaultdict(lambda: defaultdict(int))
        solved_problems = defaultdict(set)
        participants = set()
        for submission in submissions:
            status = SubmissionStatus[submission["status"]]
            if not status.judged:
                continue
            problem_id = submission["problem_id"]
            contestant_id = submission["contestant_id"]
            elapsed = submission["submit_time"] - int(self.start_time.timestamp())
            participants.add(contestant_id)
            if status == SubmissionStatus.ACCEPTED:
                if problem_id not in solved_problems[contestant_id]:
                    solved_problems[contestant_id].add(problem_id)
                    penalties[contestant_id][problem_id] = elapsed
            else:
                if problem_id not in solved_problems[contestant_id]:
                    wa_counts[contestant_id][problem_id] += 1
        standings = []
        for contestant_id in participants:
            solved = 0
            penalty = 0
            problems = {}
            for problem_id in self.get_problem_ids():
                if problem_id in solved_problems[contestant_id]:
                    solved += 1
                    time = penalties[contestant_id][problem_id]
                    wa = wa_counts[contestant_id][problem_id]
                    penalty += time + WA_PENALTY * wa
                    problems[problem_id] = "{} (+{})".format(time, wa)
                else:
                    problems[problem_id] = "-"
            standings.append({
                "contestant_id": contestant_id,
                "solved": solved,
                "penalty": penalty,
                "problems": problems
            })
        standings.sort(key=lambda row: (-row["solved"], row["penalty"], row["contestant_id"]))
        return standings

    def get_submissions(self, contestant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if contestant_id is None:
            return self.db.get_all_submissions()
        else:
            return self.db.get_contestant_submissions(contestant_id)

    def requeue(self):
        submissions = self.db.get_all_submissions()
        for submission in submissions:
            if not SubmissionStatus[submission["status"]].judged:
                self.judge_queue.put(submission["id"])