CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    problem_id TEXT NOT NULL,
    contestant_id TEXT NOT NULL,
    solution_id TEXT NOT NULL,
    language TEXT NOT NULL,
    status TEXT NOT NULL,
    source TEXT NOT NULL,
    submit_time INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS problem_index ON submissions(problem_id);
CREATE INDEX IF NOT EXISTS contestant_index ON submissions(contestant_id);
CREATE INDEX IF NOT EXISTS status_index ON submissions(status);
CREATE INDEX IF NOT EXISTS submit_time ON submissions(submit_time);
