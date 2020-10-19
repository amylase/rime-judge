from flask import Flask, render_template, request, redirect, make_response, url_for
import json
from pathlib import Path
import shutil
import datetime
import os

from rimejudge.contest import Contest, ContestDB
from rimejudge.project import RimeProject
from rimejudge.rime.languages import RimeLanguage


def init_contest(project_dir: Path):
    config_path = project_dir / "contest.json"
    cache_dir = project_dir / "contest_cache"
    if not cache_dir.exists():
        cache_dir.mkdir()
    with config_path.open() as f:
        config = json.load(f)
    n_workers = int(config["n_workers"])
    start_time = datetime.datetime.strptime(config["start_time"], "%Y-%m-%dT%H:%M:%S")
    end_time = datetime.datetime.strptime(config["end_time"], "%Y-%m-%dT%H:%M:%S")
    project_cache = cache_dir / "project"
    if not project_cache.exists():
        shutil.copytree(project_dir, project_cache, ignore=shutil.ignore_patterns("contest_cache"))
    project = RimeProject(str(project_cache))
    project.run_command("build")
    db = ContestDB(cache_dir / "contest.sqlite")
    db.ensure_tables()
    contest = Contest(project, start_time, end_time, n_workers, db)
    contest.requeue()
    return contest


contest = init_contest(Path(os.environ.get("CONTEST_PROJECT", ".")))
app = Flask(__name__)


@app.route('/standings')
def standings():
    start_time = contest.start_time
    end_time = contest.end_time
    now = datetime.datetime.now().replace(microsecond=0)
    if now < start_time:
        status = "Before start {}".format(start_time - now)
    elif now < end_time:
        status = "Remaining {}".format(end_time - now)
    else:
        status = "Finished"
    standings_data = contest.get_standings()
    problem_ids = contest.get_problem_ids()
    return render_template("standings.html", start_time=contest.start_time, end_time=contest.end_time, status=status,
                           standings=standings_data, problem_ids=problem_ids)


@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'GET':
        default_name = request.cookies.get('contestant_name', '')
        default_language = request.cookies.get('default_language', '')
        return render_template("submit.html", default_name=default_name, languages=RimeLanguage,
                               default_language=default_language, problem_ids=contest.get_problem_ids())
    else:
        contestant_name = request.form["contestant"]
        language = request.form["language"]
        rime_language = RimeLanguage[language]
        problem_id = request.form["problem"]
        source = request.form["source"]
        contest.submit(contestant_name, problem_id, rime_language, source)
        response = make_response(redirect(url_for("private_submissions", contestant_id=contestant_name)))
        response.set_cookie('contestant_name', contestant_name)
        response.set_cookie('default_language', language)
        return response


@app.route('/submissions')
def submissions():
    submission_items = contest.get_submissions()
    return render_template("submissions.html", submissions=submission_items)


@app.route('/submissions/<contestant_id>')
def private_submissions(contestant_id: str):
    submission_items = contest.get_submissions(contestant_id)
    return render_template("submissions.html", submissions=submission_items)


@app.route('/')
def home():
    return render_template("home.html")


if __name__ == '__main__':
    app.run()
