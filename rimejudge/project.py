import subprocess
from pathlib import Path

from rimejudge.rime.languages import RimeLanguage
from rimejudge.rime.myrime import run_command


class RimeProject:
    def __init__(self, project_dir: str):
        self.project_dir = project_dir

    def run_command(self, command: str, *argv: str) -> subprocess.CompletedProcess:
        return run_command(self.project_dir, command, *argv)

    def check_command(self, command: str, *argv: str) -> None:
        result = self.run_command(command, *argv)
        if result.returncode != 0:
            raise ChildProcessError("Failed to run Rime command {} {}.\nRime stdout:\n{}".format(command, ' '.join(argv), result.stdout))

    def add_solution(self, problem_id: str, solution_id: str, language: RimeLanguage, source: str):
        project_dir = Path(self.project_dir)
        problem_dir = project_dir / problem_id
        if not problem_dir.exists() or not problem_dir.is_dir():
            raise IOError("Problem directory {} does not exist".format(problem_id))
        solution_dir = problem_dir / solution_id
        if solution_dir.exists():
            raise IOError("Solution {} already exists for problem {}".format(solution_id, problem_id))
        solution_dir.mkdir()
        solution_file = solution_dir / language.solution_file
        with solution_file.open("w") as f:
            f.write(source)
        if language.need_permission:
            solution_file.chmod(0o777)
        config_file = solution_dir / "SOLUTION"
        with config_file.open("w") as f:
            f.write(language.get_solution_config())
