import math
import numpy as np
from typing import Set
from ..plant import Plant


class UnitGreedySimpleGroup:
    def __init__(
            self,
            plant: "Plant",
            unit: int,
            complete: bool = False,
            horizon: int = 30 * 24,
            orders_completed: Set[str] = set(),
            # TODO: Maintenance stops
    ):
        self.plant = plant
        self.unit = unit
        self.complete = complete
        self.horizon = horizon
        self.orders_completed = orders_completed.copy()

        # [(order_id, grade, start_time, end_time, benefit, revenue)]
        self.orders_plan = []
        self.grades_plan = []  # [(grade, start_time)]

        self.orders = plant.orders['firm'].copy()
        self.grade2orders = self.plant.group_orders_by_grade(self.orders)
        self.grades = list(range(plant.n_grades))

        self.time_reg = 3  # time before transitions operates at 100%

        self.time_last_grade_start = 0
        self.time_left_grade_change = 0  # time before we can make a transition
        self.time_reg_left = 0  # time before unit operates at 100%

        self.is_initial = True
        self.stocks = np.zeros(plant.n_grades)

        self.time = 0
        self.actual_grade = -1

    def update_orders_completed(self, new_orders):
        self.orders_completed.update(new_orders)

    def calculate_min_stock_time_cost(self, grade):
        prod_flow = self.plant.prod_flow[grade, self.unit]
        man_cost = self.plant.man_cost[grade, self.unit]
        s_min = self.plant.s_min[grade]
        tons_left = max(0, s_min - self.stocks[grade])
        time = tons_left / prod_flow
        cost = man_cost * time
        return time, cost

    def calculate_min_transition_time(self, grade):
        return self.plant.t_min[grade]

    def calculate_order_time_cost(self, tons, grade):
        prod_flow = self.plant.prod_flow[grade, self.unit]
        man_cost = self.plant.man_cost[grade, self.unit]
        time = tons / prod_flow
        cost = man_cost * time
        return time, cost

    def calculate_order_time_benefit(self, order, time_reg_left=3):
        """
        time_reg_left : time to have regular production, before this time, price is penalized
        """
        (grade, tons, price, priority) = order
        time, cost = self.calculate_order_time_cost(tons, grade)
        time_low = min(time_reg_left, time)
        time_normal = time - time_low
        price_reduction = (0.7 * (time_low / time) + (time_normal / time))
        revenue = price * price_reduction
        benefit = revenue - cost
        ratio = benefit / time
        return ratio, time, benefit, revenue

    def get_best_grade_order_group(self, grade_orders, time_reg_left=3, time_left=0):
        """
        time_reg_left: time to have regular production, before this time, price is penalized
        """
        orders_data = [(order_id, self.calculate_order_time_benefit(
            self.orders[order_id], time_reg_left)) for order_id in grade_orders]

        if not orders_data:
            return None

        if time_left == 0:
            order_id, (ratio, time, benefit, revenue) = max(
                orders_data,
                key=lambda z: z[1][0]
            )
            orders_group = [(order_id, ratio, time, benefit, revenue)]
            return (ratio, time, benefit, revenue), orders_group

        aggregated_time = 0
        aggregated_benefit = 0
        aggregated_revenue = 0
        orders_done = set()
        orders_group = []
        while aggregated_time < time_left:
            order_id, (ratio, time, benefit, revenue) = max(
                orders_data, key=lambda z: z[1][0]
            )
            orders_group.append((order_id, ratio, time, benefit, revenue))
            aggregated_time += time
            aggregated_benefit += benefit
            aggregated_revenue += revenue
            orders_done.add(order_id)

            time_reg_left = max(time_reg_left-aggregated_time, 0)
            orders_data = [
                (order_id2, self.calculate_order_time_benefit(
                    self.orders[order_id2], time_reg_left))
                for order_id2 in grade_orders if order_id2 not in orders_done]
            if not orders_data:
                break

        aggregated_time += max(0, time_left - aggregated_time)
        ratio = aggregated_benefit / aggregated_time
        group_data = (ratio, aggregated_time,
                      aggregated_benefit, aggregated_revenue)
        return group_data, orders_group

    def calculate_best_grade_solution(self, actual_grade, possible_transitions):

        grade_solutions = []
        for grade in possible_transitions:

            grade_change = (grade != actual_grade)
            if grade_change:
                time_reg_left = self.time_reg
                time_left = self.calculate_min_transition_time(grade)
            else:
                time_reg_left = self.time_reg_left
                time_left = self.time_left_grade_change

            if grade not in self.grade2orders:
                continue
            grade_orders = self.grade2orders[grade] - self.orders_completed
            best_order_data = self.get_best_grade_order_group(
                grade_orders, time_reg_left, time_left)
            if best_order_data is None:
                continue
            (ratio, order_time, benefit, revenue), orders_group = best_order_data

            solution = {
                'orders_group': orders_group,
                'ratio': ratio,
                'order_time': order_time,
                'grade': grade,
                'benefit': benefit,
                'revenue': revenue
            }

            grade_solutions.append(solution)
        if not grade_solutions:
            return {}
        best_solution = max(grade_solutions, key=lambda z: z['ratio'])
        return best_solution

    def update_restrictions_times(self, grade, grade_change, order_time_group):
        if grade_change:
            self.time_reg_left = max(
                0, self.time_reg - order_time_group
            )
            self.time_last_grade_start = self.time

            t_min = self.calculate_min_transition_time(grade)
            t_stock_min, _ = self.calculate_min_stock_time_cost(
                grade)

            self.time_left_grade_change = max(t_min, t_stock_min)
            self.time_left_grade_change = max(
                0, order_time_group - self.time_left_grade_change
            )

        else:
            self.time_reg_left = max(
                0, self.time_reg_left - order_time_group
            )
            self.time_left_grade_change = max(
                0, self.time_left_grade_change - order_time_group
            )

    def update_plans(self, grade, orders_group, grade_change):
        if grade_change:
            self.grades_plan.append((grade, self.time))
        init_time = self.time
        for (order_id, ratio, order_time, benefit, revenue) in orders_group:
            end_time = init_time + order_time
            self.orders_plan.append(
                (order_id, grade, init_time,
                 end_time, benefit, revenue)
            )
            self.orders_completed.add(order_id)
            init_time = end_time

    def update_stocks(self, grade_change):
        if grade_change and self.actual_grade != -1:
            # update stocks
            stock_tons = (math.ceil(self.time) - self.time) * \
                         self.plant.prod_flow[self.actual_grade, self.unit]
            self.stocks[self.actual_grade] += stock_tons
            self.time = math.ceil(self.time)
        elif grade_change:
            if self.stocks[self.actual_grade] < self.plant.s_min[self.actual_grade]:
                s_diff = self.plant.s_min[self.actual_grade] - self.stocks[self.actual_grade]
                t_diff = s_diff / self.plant.prod_flow[self.unit, self.actual_grade]
                total_time = math.ceil(self.time + t_diff) - self.time
                tons = self.plant.prod_flow[self.unit, self.actual_grade] * total_time
                self.stocks[self.actual_grade] += tons
                self.time = math.ceil(self.time + t_diff)

    def obtain_best_solution(self):
        if self.time_left_grade_change > 0 and self.actual_grade != -1:
            possible_transitions = [self.actual_grade]
        else:
            possible_transitions = self.plant.calculate_possible_transitions(
                self.time, self.unit, self.actual_grade)
        best_solution = self.calculate_best_grade_solution(
            self.actual_grade, possible_transitions)
        return best_solution

    def update_with_solution(self, best_solution):

        grade = best_solution['grade']
        orders_group = best_solution['orders_group']
        order_time_group = best_solution['order_time']
        benefit_group = best_solution['benefit']

        if benefit_group < 0:
            print(f'No more profitable orders, time={self.time}')
            self.complete = True
            return

        grade_change = (grade != self.actual_grade)
        self.update_stocks(grade_change)
        if self.time >= self.horizon:
            self.complete = True
            return
        self.update_restrictions_times(grade, grade_change, order_time_group)
        self.update_plans(grade, orders_group, grade_change)

        self.time += order_time_group
        self.actual_grade = grade
        if self.is_initial:
            self.is_initial = False

    def find_planification(self):

        self.actual_grade = -1  # initial
        self.time = 0
        while self.time < self.horizon:

            best_solution = self.obtain_best_solution()
            if not best_solution:
                print(f'No more orders, time={self.time}')
                break

            grade = best_solution['grade']
            orders_group = best_solution['orders_group']
            order_time_group = best_solution['order_time']
            benefit_group = best_solution['benefit']
            revenue_group = best_solution['revenue']

            if benefit_group < 0:
                print(f'No more profitable orders, time={self.time}')
                break

            grade_change = (grade != self.actual_grade)

            self.update_stocks(grade_change)
            if self.time >= self.horizon:
                break
            self.update_restrictions_times(grade, grade_change, order_time_group)
            self.update_plans(grade, orders_group, grade_change)

            self.time += order_time_group
            self.actual_grade = grade
            if self.is_initial:
                self.is_initial = False

        self.complete = True


class PlantGreedySimpleGroup:
    def __init__(
            self,
            plant: "Plant",
            horizon: int = 30 * 24,
            # TODO: Maintenance stops
    ):
        self.plant = plant
        self.horizon = horizon
        self.orders_completed = set()
        self.stocks = np.zeros(plant.n_grades)

    def find_planification(self):
        orders_plan = {}
        grades_plan = {}
        for unit in range(self.plant.n_units):
            model = UnitGreedySimpleGroup(
                plant=self.plant, unit=unit, orders_completed=self.orders_completed
            )
            model.find_planification()
            self.orders_completed.update(model.orders_completed)
            self.stocks += model.stocks
            orders_plan[unit] = model.orders_plan
            grades_plan[unit] = model.grades_plan

        return orders_plan, grades_plan, self.orders_completed, self.stocks


class PlantGreedyGroup:
    def __init__(
            self,
            plant: "Plant",
            horizon: int = 30 * 24,
            # TODO: Maintenance stops
    ):
        self.plant = plant
        self.horizon = horizon
        self.orders_completed = set()
        self.stocks = np.zeros(plant.n_grades)

    @staticmethod
    def obtain_plant_best_solution(unit_models):
        plant_solutions = [
            (unit, model.obtain_best_solution()) for unit, model in unit_models.items()
            if not model.complete
        ]
        plant_solutions = [(unit, solution)
                           for unit, solution in plant_solutions
                           if solution]
        if not plant_solutions:
            return None
        unit, best_solution = max(plant_solutions, key=lambda z: z[1]['ratio'])
        return unit, best_solution

    def find_planification(self):
        orders_plan = {}
        grades_plan = {}

        unit_models = {}
        for unit in range(self.plant.n_units):
            model = UnitGreedySimpleGroup(
                plant=self.plant, unit=unit, orders_completed=self.orders_completed
            )
            unit_models[unit] = model

        while not all(model.complete for unit, model in unit_models.items()):

            plant_best_solution = PlantGreedyGroup.obtain_plant_best_solution(unit_models)
            if not plant_best_solution:
                print(f'No more orders')
                break

            unit, best_solution = plant_best_solution
            unit_models[unit].update_with_solution(best_solution)

            # update new completed orders
            orders_group = best_solution['orders_group']
            new_orders = {order_id for (order_id, _, _, _, _) in orders_group}
            for unit, model in unit_models.items():
                model.update_orders_completed(new_orders)

        for unit, model in unit_models.items():
            self.orders_completed.update(model.orders_completed)
            self.stocks += model.stocks
            orders_plan[unit] = model.orders_plan
            grades_plan[unit] = model.grades_plan

        return orders_plan, grades_plan, self.orders_completed, self.stocks
