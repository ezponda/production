import json
import numpy as np
from typing import List, Dict, Tuple


class Plant:
    def __init__(
            self,
            n_grades: int,
            n_units: int,
            prod_flow: List[float],
            man_cost: List[float],
            not_allowed_transitions: Dict[int, List[int]],
            unique_grades: List[int],
            unique_unit: int,
            s_min: List[float],
            t_min: List[float],
            only_consecutive: Dict[int, int],
            only_predecessor: Dict[int, int],
            grades_after_10_days: List[int],
            orders: Dict[int, List[Tuple[int, float, float, float]]],
    ):
        self.__n_grades = n_grades
        self.__n_units = n_units
        self.__prod_flow = np.array(prod_flow)
        self.__man_cost = np.array(man_cost)
        self.__not_allowed_transitions = not_allowed_transitions
        self.__unique_grades = set(unique_grades)
        self.__unique_unit = unique_unit
        self.__s_min = np.array(s_min)
        self.__t_min = np.array(t_min)
        self.__only_consecutive = only_consecutive
        self.__only_predecessor = only_predecessor
        self.__grades_after_10_days = set(grades_after_10_days)
        self.__orders = orders


    @staticmethod
    def from_json_file(file_path):
        def __dict_keys2int(data):
            new_data = {}
            for k, v in data.items():
                if isinstance(v, dict) and k != 'orders':
                    new_data[k] = {int(kk): vv for kk, vv in v.items()}
                else:
                    new_data[k] = v
            return new_data
        plant_data = json.loads(open(file_path, "r").read(), object_hook=__dict_keys2int)
        plant = Plant(
            n_grades=plant_data.get('n_grades'),
            n_units=plant_data.get('n_units'),
            prod_flow=plant_data.get('prod_flow'),
            man_cost=plant_data.get('man_cost'),
            not_allowed_transitions=plant_data.get('not_allowed_transitions'),
            unique_grades=plant_data.get('unique_grades'),
            unique_unit=plant_data.get('unique_unit'),
            s_min=plant_data.get('s_min'),
            t_min=plant_data.get('t_min'),
            only_consecutive=plant_data.get('only_consecutive'),
            only_predecessor=plant_data.get('only_predecessor'),
            grades_after_10_days=plant_data.get('grades_after_10_days'),
            orders=plant_data.get('orders'),
        )
        return plant

    @staticmethod
    def from_dictionary(plant_data):
        plant = Plant(
            n_grades=plant_data.get('n_grades'),
            n_units=plant_data.get('n_units'),
            prod_flow=plant_data.get('prod_flow'),
            man_cost=plant_data.get('man_cost'),
            not_allowed_transitions=plant_data.get('not_allowed_transitions'),
            unique_grades=plant_data.get('unique_grades'),
            unique_unit=plant_data.get('unique_unit'),
            s_min=plant_data.get('s_min'),
            t_min=plant_data.get('t_min'),
            only_consecutive=plant_data.get('only_consecutive'),
            only_predecessor=plant_data.get('only_predecessor'),
            grades_after_10_days=plant_data.get('grades_after_10_days'),
            orders=plant_data.get('orders'),
        )
        return plant


class RandomPlantData:

    @classmethod
    def generate_random_data(cls, n_grades=20, n_units=3, prod_flow_lims=(1, 10),
                             man_cost_lims=(1, 11), n_not_allowed_max=4, t_min_lims=(1, 7),
                             s_min_lims=(2, 15), only_consecutive_p=0.25,
                             n_orders=100, orders_tons_lims=(5, 15), orders_price_lims=(12, 50),
                             grades_after_10_days_max=10, unique_unit=0):

        plant_data = {}
        plant_data['n_grades'] = n_grades
        plant_data['n_units'] = n_units

        # production flow (tons / hour)
        prod_flow = RandomPlantData.generate_rand(prod_flow_lims, n_grades, n_units)
        plant_data['prod_flow'] = prod_flow.flatten().tolist()

        # manufacturing cost ($ / hour)
        man_cost = RandomPlantData.generate_rand(man_cost_lims, n_grades, n_units)
        plant_data['man_cost'] = man_cost.flatten().tolist()

        # not allowed transitions
        not_allowed_transitions = RandomPlantData.generate_random_not_allowed_transitions(
            n_grades, n_not_allowed_max)
        plant_data['not_allowed_transitions'] = not_allowed_transitions

        # minimum duration
        t_min = RandomPlantData.generate_rand(t_min_lims, n_grades, 1)
        plant_data['t_min'] = t_min.flatten().tolist()

        # minimum stock
        s_min = RandomPlantData.generate_rand(s_min_lims, n_grades, 1)
        plant_data['s_min'] = s_min.flatten().tolist()

        # only consecutive grade, previous grade => consecutive grade
        # previous grade => consecutive grade
        only_consecutive = RandomPlantData.generate_random_only_consecutive(
            n_grades, only_consecutive_p)
        # consecutive grade => previous grade
        only_predecessor = {v: k for k, v in only_consecutive.items()}
        plant_data['only_consecutive'] = only_consecutive
        plant_data['only_predecessor'] = only_predecessor

        orders = RandomPlantData.generate_random_orders(
            n_orders, n_grades, orders_tons_lims, orders_price_lims)
        plant_data['orders'] = orders

        # Grades only after 10 days
        n_after_10_days = np.random.randint(1, grades_after_10_days_max)
        grades_after_10_days = np.random.choice(
                range(n_grades), size=(n_after_10_days,), replace=False
            )
        plant_data['grades_after_10_days'] = grades_after_10_days.tolist()

        # unique unit and unique grades
        unique_grades = np.random.choice(
                range(n_grades), size=(5,), replace=False
            )
        plant_data['unique_unit'] = unique_unit
        plant_data['unique_grades'] = unique_grades.tolist()

        return plant_data

    @classmethod
    def generate_random_data_save(cls, file_name):
        plant_data = cls.generate_random_data()
        with open(file_name, 'w') as fp:
            json.dump(plant_data, fp, indent=4)
        return

    @staticmethod
    def generate_rand(lims, dim0=None, dim1=None):
        if dim0 is None:
            return lims[0] + (lims[1] - lims[0]) * np.random.rand()
        return lims[0] + (lims[1] - lims[0]) * np.random.rand(dim0, dim1)

    @staticmethod
    def generate_random_only_consecutive(n_grades, only_consecutive_p):
        only_consecutive = {}  # previous grade => consecutive grade
        only_predecessor = {}  # consecutive grade => previous grade
        for grade in range(n_grades):
            p = np.random.rand()
            if p < only_consecutive_p:
                # consecutive grade
                possible_consecutive = list(
                    set(range(n_grades)) - set([grade]) -
                    set([only_predecessor.get(grade)])
                )
                consecutive = int(np.random.choice(possible_consecutive))
                only_consecutive[grade] = consecutive
                only_predecessor[consecutive] = grade

        return only_consecutive

    @staticmethod
    def generate_random_orders(n_orders, n_grades, orders_tons_lims, orders_price_lims):
        orders = {}
        # order = (grade, tons, price, priority)
        for order_id in range(n_orders):
            tons = RandomPlantData.generate_rand(orders_tons_lims)
            price = RandomPlantData.generate_rand(orders_price_lims)
            priority = np.random.rand()
            grade = int(np.random.choice(range(n_grades)))
            order = (grade, tons, price, priority)
            orders[order_id] = order
        return orders

    @staticmethod
    def generate_random_not_allowed_transitions(n_grades, n_not_allowed_max):
        not_allowed_transitions = {}
        for grade in range(n_grades):
            n_not_allowed = np.random.randint(0, n_not_allowed_max)
            not_allowed_grades = np.random.choice(
                list(set(range(n_grades)) - set([grade])),
                size=(n_not_allowed,), replace=False
            )
            not_allowed_transitions[grade] = not_allowed_grades.tolist()
        return not_allowed_transitions
