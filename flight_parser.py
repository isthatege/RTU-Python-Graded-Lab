"""Flight Schedule Parser and Query Tool - command-line entry point."""

import argparse
from datetime import datetime
import json
import logging
import os
import sys

from csv_loader import parse_files
from query import run_queries
from validator import load_airports

STUDENT_ID = "260ADM039"
FIRST_NAME = "Ege"
LAST_NAME = "Engin"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flight_parser.py",
        description="Flight Schedule Parser and Query Tool",
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("-i", dest="input_file", metavar="FILE", help="Parse a single CSV file")
    source.add_argument(
        "-d",
        dest="input_dir",
        metavar="FOLDER",
        help="Parse all .csv files in a folder (sorted, not recursive)",
    )
    source.add_argument(
        "-j",
        dest="json_db",
        metavar="FILE",
        help="Load an existing JSON database",
    )
    parser.add_argument(
        "-a",
        dest="airports_file",
        metavar="FILE",
        help="Airport list file (required with -i/-d, ignored with -j)",
    )
    parser.add_argument(
        "-o",
        dest="output_file",
        metavar="FILE",
        default=None,
        help="Output path for the JSON database (default: db.json; only with -i/-d)",
    )
    parser.add_argument(
        "-q",
        dest="query_file",
        metavar="FILE",
        help="Run queries from this JSON file",
    )
    parser.add_argument(
        "-r",
        dest="response_dir",
        metavar="FOLDER",
        default=".",
        help="Folder for the query response file (default: current directory)",
    )
    return parser


def _read_json(path: str) -> object:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, mode="r", encoding="utf-8-sig") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path} is not valid JSON: {exc.msg}") from None


def _write_json(path: str, data: object) -> None:
    with open(path, mode="w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False, allow_nan=False)
        fh.write("\n")


def _format_error(exc: Exception) -> str:
    if isinstance(exc, OSError) and exc.filename is not None:
        return f"{exc.strerror or 'cannot access'}: {exc.filename}"
    return str(exc).replace("\n", " ")


def main(argv: list[str] | None = None) -> int:
    """Parse CLI args with argparse. Return exit code (0, 1, or 2)."""
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
        if not (args.input_file or args.input_dir or args.json_db):
            parser.error("one of -i, -d, or -j is required")
        if args.json_db is not None and args.output_file is not None:
            parser.error("-o can only be used with -i or -d")
        if args.json_db is None and args.airports_file is None:
            parser.error("-a is required with -i or -d")
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 2
        return 0 if code == 0 else 2

    output_path = args.output_file if args.output_file is not None else "db.json"

    logger = logging.getLogger("flight_parser")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handler: logging.FileHandler | None = None

    try:
        if args.json_db is not None:
            raw_db = _read_json(args.json_db)
            if not isinstance(raw_db, list) or not all(
                isinstance(item, dict) for item in raw_db
            ):
                raise ValueError(f"{args.json_db} must contain a JSON array of objects")
            db = raw_db
        else:
            if not os.path.isfile(args.airports_file):
                raise FileNotFoundError(f"Airport file not found: {args.airports_file}")

            if args.input_file is not None:
                if not os.path.isfile(args.input_file):
                    raise FileNotFoundError(f"CSV file not found: {args.input_file}")
                csv_paths = [args.input_file]
            else:
                if not os.path.isdir(args.input_dir):
                    raise FileNotFoundError(f"Directory not found: {args.input_dir}")
                csv_names = sorted(
                    name
                    for name in os.listdir(args.input_dir)
                    if name.endswith(".csv")
                    and os.path.isfile(os.path.join(args.input_dir, name))
                )
                if not csv_names:
                    raise FileNotFoundError(
                        f"No .csv files found in directory: {args.input_dir}"
                    )
                csv_paths = [os.path.join(args.input_dir, name) for name in csv_names]

            airports = load_airports(args.airports_file)

            output_dir = os.path.dirname(os.path.abspath(output_path))
            if not os.path.isdir(output_dir):
                raise FileNotFoundError(f"Output directory not found: {output_dir}")
            log_path = os.path.join(output_dir, "errors.log")

            handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )
            logger.addHandler(handler)

            db, errors = parse_files(csv_paths, airports)
            for error in errors:
                logger.warning(error)

            _write_json(output_path, db)

        if args.query_file is not None:
            queries = _read_json(args.query_file)
            entries = run_queries(db, queries)

            if not os.path.isdir(args.response_dir):
                raise FileNotFoundError(
                    f"Response directory not found: {args.response_dir}"
                )

            timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M")
            response_filename = (
                f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{timestamp}.json"
            )
            _write_json(os.path.join(args.response_dir, response_filename), entries)

        return 0
    except (OSError, UnicodeDecodeError, ValueError, TypeError) as exc:
        print(f"Error: {_format_error(exc)}", file=sys.stderr)
        return 1
    finally:
        if handler is not None:
            logger.removeHandler(handler)
            handler.close()


if __name__ == "__main__":
    sys.exit(main())