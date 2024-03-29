import numpy as np
import json
from typing import List, Dict, Tuple
from .plant import Plant
from .optimization.greedy_simple_group import PlantGreedyGroup


class Planification:
    def __init__(
            self,
            plant: Plant,
            complete: bool = False,
            horizon: int = 30 * 24,
            # (order_id, grade, start_time, end_time, benefit, revenue)
            orders_plan: Dict[int,
                              List[Tuple[str, int, int, int, float, float]]] = None,
            # (grade, start_time)
            grades_plan: Dict[int, List[Tuple[int, int]]] = None,
            # TODO: Maintenance stops
    ):
        self.plant: Plant = plant
        self.complete: bool = complete
        self.horizon: int = horizon
        self.stocks = np.zeros(plant.n_grades)

        if orders_plan:
            self.orders_plan = orders_plan
        else:
            self.orders_plan = {i: [] for i in range(self.plant.n_units)}

        if grades_plan:
            self.grades_plan = grades_plan
        else:
            self.grades_plan = {i: [] for i in range(self.plant.n_units)}

        self.orders_completed = set()
        self.benefits = 0

    def check_feasibility(self):
        raise NotImplementedError('Method not implemented!')

    def calculate_benefits(self):
        return self.calculate_revenue() - self.calculate_cost()

    def calculate_revenue(self):
        return sum([order[-1] for unit, order_list in self.orders_plan.items() for order in order_list])

    def calculate_cost(self):
        cost = 0
        for unit, grades_list in self.grades_plan.items():
            size = len(grades_list)
            for i, (grade, start_time) in enumerate(grades_list):
                if i < size - 1:
                    end_time = grades_list[i + 1][-1]
                else:
                    end_time = self.horizon
                cost += self.plant.man_cost[grade, unit] * (end_time - start_time)
        return cost

    def calculate_initial_solution(self):
        model = PlantGreedyGroup(
            plant=self.plant,
            horizon=self.horizon,
        )
        orders_plan, grades_plan, orders_completed, stocks = model.find_planification()
        self.orders_plan = orders_plan
        self.grades_plan = grades_plan
        self.orders_completed = orders_completed
        self.stocks = stocks
        self.benefits = self.calculate_benefits()

    def save_data(self, output_file_path):
        data = {
            'stocks': self.stocks.tolist(),
            'orders_plan': self.orders_plan,
            'grades_plan': self.grades_plan,
            'orders_completed': list(self.orders_completed),
            'benefits': self.benefits
        }
        with open(output_file_path, 'w') as outfile:
            json.dump(data, outfile, indent=2, sort_keys=True)
