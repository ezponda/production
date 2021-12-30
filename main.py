from src.plant import Plant
from src.planification import Planification
import argparse


def main(args):
    plant = Plant.from_json_file(args.input_file_path)
    planification = Planification(
        plant=plant,
        horizon=30 * 24,
        orders_plan={},
        grades_plan={}
    )
    planification.calculate_initial_solution()
    planification.save_data(args.output_file_path)
    return


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(
            description="Planification"
        )
        parser.add_argument('--input_file_path', dest='input_file_path',
                            type=str, help='Input file for planification data')
        parser.add_argument('--output_file_path', dest='output_file_path',
                            type=str, help='Output file for planification solution')
        args = parser.parse_args()
        main(args)

    except RuntimeError as e:
        raise
