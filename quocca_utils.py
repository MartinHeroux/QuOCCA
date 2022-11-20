from pathlib import Path
from datetime import datetime
import csv
import sys
import operator


def compare(csv_file: Path, id1: str, id2: str):
    """Main series of functions to read, clean, compare and write results."""
    raw_data = read_csv(csv_file)
    data_id1, data_id2 = _get_data_id1_id2(id1, id2, raw_data)
    _save_data_to_csv(data_id1, id1, csv_file.parent)
    _save_data_to_csv(data_id2, id2, csv_file.parent)
    diff_data = _get_diff_data(data_id1, data_id2, id1, id2)
    _save_diff_data_to_csv(diff_data, id1, id2, csv_file.parent)


def read_csv(csv_file):
    data = list()
    with open(csv_file, newline="") as f:
        raw_data = csv.reader(f, delimiter=",")
        for row in raw_data:
            data.append(row)
    return data


def _get_data_id1_id2(id1, id2, raw_data):
    header_item_indexes = _get_header_item_indexes(raw_data)
    id1_data = _get_data(id1, raw_data, header_item_indexes)
    _reviewer_has_data(id1, id1_data)
    id2_data = _get_data(id2, raw_data, header_item_indexes)
    _reviewer_has_data(id2, id2_data)
    return id1_data, id2_data


def _get_header_item_indexes(raw_data):
    """Get index of all required header items

    Note that RedCap includes multiples columns with the header item 'pub_id'.
    For a given QuOCCA entry (i.e. row), only one of these 'pub_id' items
    contains data.
    """
    full_header = raw_data[0]
    header = _gen_header()
    header_item_indexes = dict()
    for header_item_long_name, header_item_short_name in header:
        header_item_indexes[header_item_short_name] = _get_header_item_index(header_item_long_name, full_header)
    header_item_indexes = _add_comment_indexes(header_item_indexes)
    return header_item_indexes


def _gen_header():
    return [['Survey Timestamp',
      'timestamp'],
    ['Reviewer ID',
     'reviewer_id'],
    ['Publication identifier',
     "pub_id"],
    ["Were the study's hypotheses and analyses plans registered prior to the conduct of the study (i.e. pre-registered)?",
     "q1a"],
    ["If so, was the main conclusion reported in the abstract (or summary) based on the primary hypothesis/outcome?",
     "q1b"],
    ["",
     "q1comments"],
    ["Are the primary data accessible to independent researchers on a public website?",
     "q2"],
    ["",
     "q2comments"],
    ["Is code used for the study available on a public website to allow for reproduction or analysis of data?",
     "q3"],
    ["",
     "q3comments"],
    ["Are any reporting guidelines specified (e.g. Consort, Strobe)?",
     "q4"],
    ["",
     "q4comments"],
    ["Was ethics approval obtained?",
     "q5"],
    ["",
     "q5comments"],
    ["Was the sample size based on a formal sample size calculation (or other justification) done prior to starting the study?",
     "q6a"],
    ["If so, was the planned sample size adhered to?",
     "q6b"],
    ["",
     "q6comments"],
    ["Was data analysis blinded?",
     "q7"],
    ["",
     "q7comments"],
    ["Are all measures of variability defined in figures, tables and text?",
     "q8a"],
    ["Are any data summarised using standard error of the mean (SEM)?",
     "q8b"],
    ["If the SEM is used, are sample sizes specified for all reported SEM?",
     "q8c"],
    ["",
     "q8comments"],
    ["Was any data excluded?",
     "q9a"],
    ["If so, was a criterion given?",
     "q9b"],
    ["",
     "q9comments"],
    ["If null-hypothesis testing of significance was used, is a probability threshold specified for all statistical tests?",
     "q10a"],
    ["If used, are exact probability values used throughout the report, excluding figure legends?",
     "q10b"],
    ["",
     "q10comments"],
    ["Are claims made for the importance or significance of results associated with a P-value greater than or equal to 0.05 (or other threshold) i.e. spin?",
     "q11"],
    ["",
     "q11comments"],
    ["If you need to include any general notes for this QuOCCA entry, please use the free-form notes box below.",
     "general_comments"]]


def _get_header_item_index(header_item_long_name, full_header):
    index = list()
    if header_item_long_name != "":
        for i, header_item in enumerate(full_header):
            if header_item == header_item_long_name:
                index.append(i)
    return index


def _add_comment_indexes(header_item_indexes):
    """Add indexes to 'comments' header for each question.

    Each question allowed user to add a comment. These headers all have
    the same name (i.e. 'comment'), which makes them non-unique.
    Thus, this additional step is needed to determine which colum
    contains comments.
    """
    revised_header_item_indexes = dict()
    for key, value in header_item_indexes.items():
        if len(value) > 0:
            revised_header_item_indexes[key] = value
            previous_value = value
        else:
            revised_header_item_indexes[key] = [previous_value[0] + 1]
    return revised_header_item_indexes


def _get_data(_id, raw_data, header_item_indexes):
    """Get header and QuOCCA entries for a specific reviewer."""
    data = list()
    data.append(list(header_item_indexes.keys()))
    for quocca in raw_data[1:]:
        if _is_id(quocca, header_item_indexes, _id):
            clean_quocca = _get_clean_quocca(quocca, header_item_indexes)
            data.append(clean_quocca)
    print(f'A total of {len(data)-1} records were retrieved for reviewer {_id}')
    return data


def _is_id(quocca, header_indexes, _id):
    if quocca[header_indexes['reviewer_id'][0]] == _id:
        return True


def _get_clean_quocca(quocca, header_indexes):
    """Get data from current row (i.e. QuOCCA entry).

    Because RedCap outputs the data will several 'pub_id' columns,
    the header item for 'pub_id' contains several indexes. Each of
    these indexes need to be verified to determine, for a given row,
    which one contains the actual 'pub_id. For all other header items,
    there is only one available index (i.e. index[0]).'
    """
    clean_quocca= list()
    for header_item, index in header_indexes.items():
        if _is_pub_id(header_item):
            clean_quocca.append(_get_pub_id(index, quocca))
        else:
            clean_quocca.append(quocca[index[0]])
    return clean_quocca


def _is_pub_id(header):
    if header == 'pub_id':
        return True
    else:
        return False


def _get_pub_id(indexes, quocca):
    for index in indexes:
        if len(quocca[index]) > 0:
            return quocca[index]


def _reviewer_has_data(_id, id_data):
    if len(id_data) <= 1:
        print(f'\n\n!!! There was error processing your request!!!\n'
              f'\nThe provided QuOCCA output file from RedCap does not include any entries for reviewer {_id}.'
              f'\nPlease make sure you have entered to correct reviewer id.\n')
        sys.exit(1)


def _save_data_to_csv(data, _id, path: Path):
    """Save cleaned reviewer data to CSV."""
    save_path = path / f'reviewer_{_id}_quoccas.csv'
    save_csv(save_path, data)

def save_csv(save_path, data):
    with open(save_path, 'w') as f:
        writer = csv.writer(f)
        for row in data:
            writer.writerow(row)
    print(f'Saved {save_path}')


def _get_diff_data(data_id1, data_id2, id1, id2):
    clean_data_id1 = _clean_data(data_id1)
    clean_data_id2 = _clean_data(data_id2)
    diff_data = _gen_diff_data(clean_data_id1, clean_data_id2, id1, id2)
    return diff_data


def _clean_data(data):
    clean_data = _remove_incomplete_entries(data)
    clean_data = _remove_entries_with_no_pub_id(clean_data)
    clean_data = _remove_duplicate_entries(clean_data)
    clean_data = _remove_comments_and_timestamps(clean_data)
    return clean_data


def _remove_incomplete_entries(data):
    clean_data = list()
    clean_data.append(data[0])
    for quocca in data[1:]:
        if quocca[0] != '[not completed]':
            clean_data.append(quocca)
    return clean_data


def _remove_entries_with_no_pub_id(data):
    clean_data = list()
    clean_data.append(data[0])
    for quocca in data[1:]:
        if quocca[2]:
            clean_data.append(quocca)
    return clean_data



def _remove_duplicate_entries(data):
    clean_data = list()
    clean_data.append(data[0])
    duplicate_pub_ids = list()
    for index_current_row, row in enumerate(data[1:], start=1):
        if _not_a_duplicate(row, duplicate_pub_ids):
            duplicates, duplicate_times, duplicate_pub_ids = _find_duplicates(row, data, duplicate_pub_ids, index_current_row)
            if _no_duplicates(duplicates):
                clean_data.append(row)
            else:
                index_of_most_recent_duplicate = duplicate_times.index(max(duplicate_times))
                clean_data.append(duplicates[index_of_most_recent_duplicate])
    return clean_data


def _not_a_duplicate(quocca, duplicate_pub_ids):
    return quocca[2] not in duplicate_pub_ids


def _find_duplicates(quocca, data, duplicate_pub_ids, index_current_row):
    current_pub_id = quocca[2]
    duplicates = list()
    duplicate_times = list()
    duplicates.append(quocca)
    duplicate_times.append(datetime.strptime(quocca[0], '%Y-%m-%d %H:%M:%S'))
    for row_below in data[index_current_row + 1:]:
        if row_below[2] == current_pub_id:
            duplicates.append(row_below)
            duplicate_times.append(datetime.strptime(row_below[0], '%Y-%m-%d %H:%M:%S'))
            duplicate_pub_ids.append(row_below[2])
    return duplicates, duplicate_times, duplicate_pub_ids


def _no_duplicates(duplicates):
    return len(duplicates) == 1


def _remove_comments_and_timestamps(data):
    header_indexes = _get_header_indexes(data)
    clean_data = list()
    for row in data:
        clean_data.append(list(operator.itemgetter(*header_indexes)(row)))
    return clean_data


def _get_header_indexes(data):
    header = _diff_output_header()
    header_indexes = list()
    for header_item in header:
        header_indexes.append(data[0].index(header_item))
    return header_indexes


def _diff_output_header():
    return ['reviewer_id',
            "pub_id",
            "q1a",
            "q1b",
            "q2",
            "q3",
            "q4",
            "q5",
             "q6a",
             "q6b",
             "q7",
             "q8a",
             "q8b",
             "q8c",
             "q9a",
             "q9b",
             "q10a",
             "q10b",
             "q11",
            ]


def _gen_diff_data(data_id1, data_id2, id1, id2):
    unique_pub_ids = _get_unique_pub_ids(data_id1, data_id2)
    diff = list()
    diff.append(data_id1[0])
    for pub_id in unique_pub_ids:
        pub_id_data_id1 = _get_data_for_current_pub_id(data_id1, id1, pub_id)
        pub_id_data_id2 = _get_data_for_current_pub_id(data_id2, id2, pub_id)
        pub_id_diff = _get_pub_id_diff(pub_id_data_id1, pub_id_data_id2)
        diff.append(pub_id_data_id1)
        diff.append(pub_id_data_id2)
        diff.append(pub_id_diff)
    return diff


def _get_unique_pub_ids(data_id1, data_id2):
    id1_pub_ids = _get_pub_ids(data_id1)
    id2_pub_ids = _get_pub_ids(data_id2)
    unique_ids = _unique_pub_ids(id1_pub_ids, id2_pub_ids)
    return unique_ids


def _get_pub_ids(data):
    ids = list()
    for row in data[1:]:
        ids.append(row[1])
    return ids


def _unique_pub_ids(pub_ids1, pub_ids2):
    pub_ids1.extend(pub_ids2)
    unique_pub_ids = set(pub_ids1)
    unique_pub_ids = list(unique_pub_ids)
    unique_pub_ids.sort()
    return unique_pub_ids


def _get_data_for_current_pub_id(data, _id, pub_id):
    pub_id_data = list()
    for row in data[1:]:
        if pub_id == row[1]:
            pub_id_data = row
    if len(pub_id_data) == 0:
        pub_id_data = _gen_empty_pub_id_data(pub_id, _id)
    return pub_id_data


def _gen_empty_pub_id_data(pub_id, _id):
    empty_pub_id_data = list()
    empty_pub_id_data.append(_id)
    empty_pub_id_data.append(pub_id)
    for _ in range(17):
        empty_pub_id_data.append("-")
    return empty_pub_id_data


def _get_pub_id_diff(pub_id_data_id1, pub_id_data_id2):
    pub_id_diff = list()
    pub_id_diff.append('consensus')
    pub_id_diff.append(pub_id_data_id1[1])
    for response1, response2 in zip(pub_id_data_id1[2:], pub_id_data_id2[2:]):
        if response1 == response2:
            pub_id_diff.append(response1)
        else:
            pub_id_diff.append('?')
    return pub_id_diff


def _save_diff_data_to_csv(diff_data, id1, id2, path):
    save_path = path / f"quocca_diff_reviewer{id1}_reviewer{id2}.csv"
    save_csv(save_path, diff_data)
