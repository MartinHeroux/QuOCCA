"""Retrieve and collate consensus responses from all pairs of raters."""

from pathlib import Path
import argparse

import quocca_utils


def main(args):
    summary = list()
    for i, csv_file in enumerate(args.csv_files):
        csv_file_path = Path(csv_file)
        current_data = quocca_utils.read_csv(csv_file_path)
        if i == 0:
            summary.append(current_data[0][1:])
        for row in current_data[1:]:
            if row[0] == 'consensus':
                summary.append(row[1:])
    path = csv_file_path.parent / 'QuOCCA_summary.csv'
    quocca_utils.save_csv(path, summary)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv_files",
        type=str,
        nargs='*',
        help="Full path to CSV files with QuOCCA values and consensus from two reviewers",
    )
    args = parser.parse_args()
    main(args)
