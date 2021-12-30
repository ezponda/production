Manufacturing Schedule 
==============================
To install python requirements:
```bash
pip install -r requirements.txt
```

For finding a planification with [input data](#input-data-format) stored in input/file/path 
and saving it in output/file/path:

```bash
python main.py --input_file_path input/file/path --output_file_path output/file/path
```
For example:

```bash
python main.py --input_file_path data/example.json --output_file_path data/out.json
```

For running the tests:
```bash
pytest src/test/
```

Input Data Format
------------

Input file example in `/data/example.json`.

It has been generated with class `RandomPlantData` in `/src/plant.py`

```python
from src.plant import RandomPlantData
file_path = 'data/example.json'
RandomPlantData.generate_random_data_save(file_path, {'n_orders':2500, 'n_grades':20})
```

```
{
    "n_grades": 8,
    "n_units": 3,
    "intervals_per_day": 24,
    "prod_flow": [
        [
            240.45432233885333,
            164.66963637321834,
            120.9843704822231
        ],
        [
            67.08143731488329,
            169.74306184263352,
            67.64331987766394
        ],
        ...,
    "man_cost": [
        [
            13.780502851702533,
            49.749431341869936,
            27.035629345162747
        ],
        ...
    ],
    "t_min": [
        13.955123588014606,
        6.613644065292002,
        ...
    ],
    "s_min": [
        11.235784547916863,
        13.164644187295762,
        ...
    ],
    "only_consecutive": {
        "5": 2,
        "6": 1
    },
    "only_predecessor": {
        "2": 5,
        "1": 6
    },
    "not_allowed_transitions": {
        "0": [
            4,
            6,
            3
        ],
        "1": [
            0
        ],
        "2": [
            6,
            7,
            3
        ],
     ...
    },
    "orders": {
        "firm": {
            "4602c2ae-50f2-4e6f-99fd-24af03b82479": [
                3,
                892.1282577694125,
                961.1799051162487,
                0.11576984037518845
            ],
         ...
        },
        "estimated": {
            "f8321438-b16b-41f5-a289-319fd73d64d4": [
                1,
                1769.2979099532554,
                868.7581637299304,
                0.047562601399418036
            ],
            ...
        }
    },
    "grades_after_10_days": [
        3,
        0,
        5,
        4,
        6
    ],
    "unique_unit": 0,
    "unique_grades": [
        7,
        2,
        4,
        6,
        3
    ]
}
```