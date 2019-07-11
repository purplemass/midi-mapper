"""Import and process mapping CSV files."""
from typing import Any, Dict, List

import csv
from os import listdir


def import_mappings(folder: str) -> List[Dict[str, Any]]:
    """List and import CSV files in the specified folder."""
    data: List = []
    files = filter(lambda x: x.endswith('.csv'), listdir(folder))
    for filename in files:
        csv = csv_dict_list(f'{folder}/{filename}')
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
        fieldnames = [f.lower().replace(' ', '-') for f in fieldnames]
        prefix_output_fieldname = False
        for idx, name in enumerate(fieldnames):
            if prefix_output_fieldname is True:
                fieldnames[idx] = f'o-{fieldnames[idx]}'
            if 'output' in name:
                prefix_output_fieldname = True
        data: List[Dict[str, Any]] = list(csv.DictReader(fd, fieldnames))

    for d in data:
        d['memory'] = 0
    return data
