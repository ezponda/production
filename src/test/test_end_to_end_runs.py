from ..plant import Plant, RandomPlantData
from ..planification import Planification


def _check_unique_units(plant, planification):
    unique_unit = plant.unique_unit
    unique_grades = plant.unique_grades
    for unit, grades_list in planification.grades_plan.items():
        if unit != unique_unit:
            assert not unique_grades & {grade for grade, _ in grades_list}


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
