#!/usr/bin/python

import os
from rime.core import commands
from rime.basic.targets import problem, solution


class Judge(commands.CommandBase):
    def __init__(self, parent):
        super(Judge, self).__init__(
            'judge',
            'problem solution',
            'judge a+b cpp-correct',
            'judge a single solution.',
            parent)

    def Run(self, project, args, ui):
        if len(args) < 2:
            ui.errors.Error(None,
                            '2 arguments are required but {} were given'.format(len(args)))
            return None

        problem_dir = os.path.abspath(args[0])
        soluton_dir = os.path.join(problem_dir, args[1])

        problem_obj = project.FindByBaseDir(problem_dir)
        if not problem_obj:
            ui.errors.Error(None,
                            'Target directory is missing or not managed by Rime.')
            return None

        if not isinstance(problem_obj, problem.Problem):
            ui.errors.Error(None, 'specified problem is not a Rime problem object.')
            return None

        soluton_obj = problem_obj.FindByBaseDir(soluton_dir)

        if not soluton_obj:
            ui.errors.Error(None,
                            'Target directory is missing or not managed by Rime.')
            return None

        if not isinstance(soluton_obj, solution.Solution):
            ui.errors.Error(None, 'specified solution is not a Rime solution object.')
            return None

        return problem_obj.TestSolution(soluton_obj, ui)


commands.registry.Add(Judge)
