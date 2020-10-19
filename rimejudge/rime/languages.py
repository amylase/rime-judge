import enum


class RimeLanguage(enum.Enum):
    CPP14 = "C++ 14", "main.cpp", "cxx_solution(src='{}', flags=['-std=c++1y', '-O2'], challenge_cases=[])", False
    CPP17 = "C++ 17", "main.cpp", "cxx_solution(src='{}', flags=['-std=c++1z', '-O2'], challenge_cases=[])", False
    SCRIPT = "Script (Shebang Required)", "main.exe", "script_solution(src='{}', challenge_cases=[])", True

    def __init__(self, display_name: str, solution_file: str, solution_config_template: str, need_permission):
        self.display_name = display_name
        self.solution_file = solution_file
        self.solution_config_template = solution_config_template
        self.need_permission = need_permission

    def get_solution_config(self):
        return self.solution_config_template.format(self.solution_file)