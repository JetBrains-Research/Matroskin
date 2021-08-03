from abc import ABC, abstractmethod


class CellProcessor():
    task_mapping = {}
    cell = {}

    def process_cell(self, tasks) -> dict:
        tasks_functions = {
            task: function
            for task, function in tasks.items()
            if (task in self.task_mapping.keys())
        }
        for function in tasks_functions:
            self.cell[function] = self.task_mapping[function](self.cell)

        return self.cell

