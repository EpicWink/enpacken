"""Find package installation candidates."""

import argparse
import logging as lg

from . import __version__
from . import find


def build_find_parser(subparsers):  # TODO: unit-test, document
    parser: argparse.ArgumentParser = subparsers.add_parser("find")
    parser.add_argument(
        "index",
        nargs="*",
        help=(
            "extra index to search in (can be specified multiple times), can"
            "possibly be a local directory. Default: just PyPI"
        )
    )
    parser.add_argument(
        "--no-pypi",
        action="store_true",
        help="don't for package in PyPI"
    )
    parser.set_defaults(func=find_distributions)


def find_distributions(args):  # TODO: unit-test, document
    dists = find.find_distributions(*args.index, pypi=not args.no_pypi)
    print("\n".join(dists))


def build_parser():  # TODO: unit-test, document
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="%(prog)s " + __version__
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="increase verbosity"
    )
    subparsers = parser.add_subparsers()
    build_find_parser(subparsers)
    return parser


def setup_logging(verbose=0):  # TODO: unit-test, document
    level = lg.WARNING - lg.DEBUG * verbose
    format_ = "[%(levelname)8s] %(name)s: %(message)s"
    lg.basicConfig(level=level, format=format_)


def main():  # TODO: unit-test, document
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(args.verbose)
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
