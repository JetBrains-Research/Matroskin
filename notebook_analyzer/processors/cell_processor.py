from abc import ABC


class CellProcessor(ABC):
    task_mapping = {}
    cell = {}

    def process_cell(self, tasks) -> dict:
        functions = [
            function for function, executing in tasks.items()
            if (function in self.task_mapping.keys() and executing is True)
        ]

        for function in functions:
            self.cell[function] = self.task_mapping[function](self.cell)

        return self.cell

