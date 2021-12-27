import numpy as np
from typing import List, Dict, Tuple
from .plant import Plant


class Planification:
    def __init__(
            self,
            plant: "Plant",
            complete: bool = False,
            horizon: int = 30 * 24,
            orders_plan: Dict[int,
                              List[Tuple[int, int, int, float, int]]] = {},
            grades_plan: Dict[int, List[Tuple[int, int, int]]] = {},
            # TODO: Maintenance stops
    ):
        self.plant = plant
        self.complete = complete
        self.horizon = horizon

        if orders_plan:
            self.orders_plan = orders_plan
        else:
            self.orders_plan = {i: [] for i in range(self.plant.n_units)}

        if grades_plan:
            self.grades_plan = grades_plan
        else:
            self.grades_plan = {i: [] for i in range(self.plant.n_units)}

    def check_feasibility(self):
        raise NotImplementedError('Method not implemented!')

    def calculate_benefits(self):
        raise NotImplementedError('Method not implemented!')