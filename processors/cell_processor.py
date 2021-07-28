from abc import ABC, abstractmethod


class CellProcessor(ABC):
    task_mapping = {}
    cell = {}

    def __init__(self, cell_data):
        self.cell = cell_data

    @abstractmethod
    def process_cell(self, tasks) -> dict:
        for function in {
            k: v
            for k, v in tasks.items()
            if (v and k in self.task_mapping.keys())
        }:
            self.cell[function] = self.task_mapping[function](self.cell)
        return self.cell

