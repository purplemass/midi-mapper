"""Utility functions."""

import csv


def csv_dict_list(filename):
    """Read translations CSV file and convert to a dictionary.

    Ensure output fieldnames are not the same as input fieldnames.
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
        data = list(csv.DictReader(fd, fieldnames))
    return data
