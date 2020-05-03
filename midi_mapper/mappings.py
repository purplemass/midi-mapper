"""Import and process mapping CSV files."""
from typing import Any, Dict, List

import csv
from os import listdir


MAPPINGS_FOLDER = './mappings/'


def import_mappings() -> List[Dict[str, Any]]:
    """List and import CSV files in the specified folder."""
    data: List[Dict[str, Any]] = []
    files = filter(lambda x: x.endswith('.csv'), listdir(MAPPINGS_FOLDER))
    for filename in files:
        csv = csv_dict_list(f'{MAPPINGS_FOLDER}/{filename}')
        data += csv
    return data


def csv_dict_list(filename: str) -> List[Dict[str, Any]]:
    """Read mappings CSV file and convert to a dictionary.

    Ensure output fieldnames are not the same as input fieldnames and
    add 'memory' to remember readings per bank.
    """
    with open(filename, 'r') as fd:
        reader = csv.reader(fd, delimiter=',')
        fieldnames = next(reader)
        fieldnames = [f.lower().replace(' ', '') for f in fieldnames]
        prefix_output_fieldname = False
        for idx, name in enumerate(fieldnames):
            if prefix_output_fieldname is True:
                fieldnames[idx] = f'o-{fieldnames[idx]}'
            if 'output' in name:
                prefix_output_fieldname = True
        data: List[Dict[str, Any]] = list(csv.DictReader(fd, fieldnames))

    for d in data:
        d['o-level'] = 0
        d['memory'] = 0
        # strip value in case CSV file has extra spaces in it
        for key in d.keys():
            d[key] = str(d[key]).strip()
    return data
