"""Process QuOCCA output from RedCap and output CSV for two reviewers.
Also output CSV of each reviewer and whether they agreed."""

from pathlib import Path
import argparse

import quocca_utils


def main(args):
    csv_file = Path(args.csv_file)
    quocca_utils.compare(csv_file, args.id_1, args.id_2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv_file",
        type=str,
        help="Full path to CSV file with QuOCCA scores exported (Labels) from RedCap",
    )
    parser.add_argument("id_1", type=str, help="Numerical id of first reviewer")
    parser.add_argument("id_2", type=str, help="Numerical id of second reviewer")
    args = parser.parse_args()
    main(args)
