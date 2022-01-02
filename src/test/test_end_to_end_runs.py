from ..plant import Plant, RandomPlantData
from ..planification import Planification


def _check_unique_units(plant, planification):
    unique_unit = plant.unique_unit
    unique_grades = plant.unique_grades
    for unit, grades_list in planification.grades_plan.items():
        if unit != unique_unit:
            assert not unique_grades & {grade for grade, _ in grades_list}


def _check_minimum_production_times(plant, planification):
    grades_plan = planification.grades_plan
    for unit, unit_plan in grades_plan.items():
        for i, (grade, start_time) in enumerate(unit_plan[:-1]):
            _, next_start_time = unit_plan[i + 1]
            elapsed_time = next_start_time - start_time
            assert plant.t_min[grade] <= elapsed_time


def _check_10_days_orders(plant, planification):
    grades_plan = planification.grades_plan
    for unit, unit_plan in grades_plan.items():
        for i, (grade, start_time) in enumerate(unit_plan):
            if grade in plant.grades_after_10_days:
                assert start_time >= 10 * plant.intervals_per_day


def _check_possible_transitions(plant, planification):
    grades_plan = planification.grades_plan
    for unit, unit_plan in grades_plan.items():
        for i, (grade, start_time) in enumerate(unit_plan[:-1]):
            next_grade, _ = unit_plan[i + 1]
            not_allowed_grades = plant.not_allowed_transitions[grade]
            assert next_grade not in not_allowed_grades
            if grade in plant.only_consecutive:
                assert next_grade not in plant.only_consecutive[grade]


def test_end_to_end_runs():
    for i in range(4):
        plant_data = RandomPlantData.generate_random_data(seed=i)
        plant = Plant.from_dictionary(plant_data)
        planification = Planification(
            plant=plant,
            horizon=30 * 24
        )
        planification.calculate_initial_solution()
        assert set(list(planification.grades_plan.keys())) == set(range(plant.n_units))
        assert planification.calculate_revenue() >= 0
        assert planification.calculate_revenue() - planification.calculate_cost() >= 0
        _check_unique_units(plant, planification)
        _check_minimum_production_times(plant, planification)
        _check_10_days_orders(plant, planification)
