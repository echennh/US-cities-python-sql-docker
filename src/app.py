"""
CLI with two sub-commands:

    load   – read CSV and populate DB
    query  – aggregate population totals

Usage examples (inside the container):

    # Load data with debug logging enabled
    python -m app load --file /data/cities.csv \
        --user root --pw-stdin --debug

    # Aggregate populations for NY and CA
    python -m app query --user root --pw-file /run/secrets/db-pw \
        --debug NY CA
"""
from __future__ import annotations # postpones annotations so that code definition order does not matter

import argparse
import csv
import getpass
import logging
import sys
import time
from pathlib import Path
from typing import List, Tuple
#this script executes in /opt/project/src

from .config import Config
from .db import MySQLConnection
from .us_states import normalize

# Inside a package, you must use *relative* imports so Python can unambiguously resolve siblings (with the dots)
# Pycharm's Docker Compose interpreter sometimes masks this by putting your project root on PYTHONPATH, making absolute `from config import Config` look like it works

__all__ = ["main"]

# ---------------------------------------------------------------------------
# Constants & logging format
# ---------------------------------------------------------------------------
_LOG_FORMAT = "%(" "asctime)sZ | %(levelname)-8s | %(name)s: %(message)s"
_SAMPLE_SIZE = 5  # number of rows from city_population to show after load
_LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Argument parsing helpers
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    """Build the top‑level :pyclass:`argparse.ArgumentParser`.

    Returns
    -------
    argparse.ArgumentParser
        Fully configured parser with *load* and *query* sub‑parsers.
    """
    parser = argparse.ArgumentParser(prog="us-cities")

    sub = parser.add_subparsers(
        title="sub‑commands",
        dest="command",
        required=True,
        metavar="{load,query}",
    )

    # ---- load -------------------------------------------------------------
    load_p = sub.add_parser("load", help="Load CSV into MySQL")
    load_p.add_argument(
        "--file",
        "-f",
        default="/data/cities.csv",
        metavar="PATH", # what is this metavar?
        help="Path to CSV (inside container)",
    )
    load_p.add_argument("--debug", action="store_true", help="Enable verbose logging")

    # common creds for both commands
    for p in (load_p,):
        _add_common_db_args(p)

    # ----- query ------------------------------------------------------------
    query_p = sub.add_parser("query", help="Aggregate populations")
    query_p.add_argument(
        "--states",
        nargs="+",
        metavar="STATE",
        help="One or more US states (full name or 2-letter code)",
    )
    query_p.add_argument("--debug", action="store_true", help="Enable verbose logging")
    _add_common_db_args(query_p)

    return parser


def _add_common_db_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--user", required=True, help="MySQL username for authentication")

    # Only one password mechanism may be provided at a time
    pw = p.add_mutually_exclusive_group(required=True)
    pw.add_argument("--pw-stdin", action="store_true", help="Prompt for password via stdin (character echo off)")
    pw.add_argument("--pw-file", metavar="FILE", help="Read the first line as password from a local file")
    pw.add_argument("--password", metavar="PW", help="⚠️  Plain‑text password (NOT recommended)")

# ---------------------------------------------------------------------------
# Password resolution
# ---------------------------------------------------------------------------

def _resolve_password(args: argparse.Namespace) -> str:
    """Resolve the password from *args* according to CLI flags."""
    if getattr(args, "pw_stdin", False):
        return getpass.getpass("MySQL password: ")
    if path := getattr(args, "pw_file", None):
        return Path(path).read_text().splitlines()[0].strip()
    logging.warning("⚠️  Supplying a password on the command line is insecure.")
    return args.password

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def _setup_logging(*, debug: bool) -> None:
    """Configure the root logger.

    * All timestamps are converted to UTC by pointing
      :pyattr:`logging.Formatter.converter` at :pyfunc:`time.gmtime`.
    * The log‑level is **DEBUG** when *debug* is *True*, otherwise **INFO**.
    """
    debug = debug or Config.from_env().debug
    logging.Formatter.converter = time.gmtime
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format=_LOG_FORMAT,
        stream=sys.stderr
    )
    _LOGGER.debug("Debug logging enabled = %s", debug)

# ---------------------------------------------------------------------------
# Sub‑command handlers
# ---------------------------------------------------------------------------

def _handle_load(args: argparse.Namespace, cfg: Config) -> None:
    """Implementation of the *load* sub‑command."""
    _setup_logging(debug=args.debug)
    _LOGGER.info("Loading CSV '%s' into %s:%s/%s", args.file, cfg.host, cfg.port, cfg.database)

    conn = MySQLConnection(
        host=cfg.host,
        port=cfg.port,
        user=args.user,
        password=_resolve_password(args),
        database=cfg.database,
    )
    # at this point in the code, the cwd is /opt/project/src
    with open(args.file, newline="") as fh:
        reader = csv.DictReader(fh)
        rows = (
            (r["City"], r["State"], int(r["year"]), int(r["Population"]))
            for r in reader
        )
        row_counter = conn.insert_population_rows(rows)

    _LOGGER.info("CSV load complete — %d rows written.", row_counter)
    # 2. Print verification snapshot ----------------------------------------
    _dump_load_summary(conn)


def _handle_query(args: argparse.Namespace, cfg: Config) -> None:
    """Implementation of the *query* sub‑command."""
    _setup_logging(debug=args.debug)
    _LOGGER.info("CLI input states = %s", args.states)

    # normalize
    try:
        states = [normalize(s) for s in args.states]
    except KeyError as exc:
        logging.error("Bad state: %s", exc)
        sys.exit(1)

    if len(set(states)) != len(states):
        logging.warning("Duplicate state inputs detected; deduplicating.")
        states = list(dict.fromkeys(states))

    _LOGGER.debug("Normalized states = %s", states)

    conn = MySQLConnection(
        host=cfg.host,
        port=cfg.port,
        user=args.user,
        password=_resolve_password(args),
        database=cfg.database,
    )

    latest = conn.latest_year()
    _LOGGER.info("Querying latest year present in DB: %d", latest)
    rows = conn.sum_population(states, latest)

    per_state = {s: p for s, p in rows}
    grand_total = sum(per_state.values())

    for state in states:
        pop = per_state[state]
        print(f"{state:<25} {pop:,}")
    print("-" * 34)
    print(f"{'Grand Total':<25} {grand_total:,}")
    _LOGGER.info("Query finished successfully")

# ---------------------------------------------------------------------------
# helpers for summary stats after db load
# ---------------------------------------------------------------------------
def _dump_load_summary(conn: MySQLConnection) -> None:
    """Print row/column stats and a random sample after CSV ingest."""
    _LOGGER.info("Running some summary statistics to help you validate that the data loaded in correctly.")
    with conn as cur:
        cur.execute("SELECT COUNT(*) FROM city_population;")
        total_rows: int = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT city) FROM city_population;")
        total_cities: int = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT state) FROM city_population;")
        total_states: int = cur.fetchone()[0]

        cur.execute("SELECT MAX(year) FROM city_population;")
        latest_year: int = cur.fetchone()[0]

        cur.execute(
            "SELECT year, COUNT(*) "
            "FROM city_population GROUP BY year ORDER BY year;"
        )
        per_year: List[Tuple[int, int]] = list(cur.fetchall())

        cur.execute(
            "SELECT city, state, year, population "
            "FROM city_population "
            "ORDER BY RAND() LIMIT %s;", (_SAMPLE_SIZE,)
        )
        sample: List[Tuple[str, str, int, int]] = list(cur.fetchall())

    _LOGGER.debug("Summary rows per year = %s", per_year)

    # ── Pretty-print --------------------------------------------------------
    logging.info("Load verification snapshot:")
    print()
    print(f"Total rows:          {total_rows:,}")
    print(f"Distinct cities:     {total_cities:,}")
    print(f"Distinct states:     {total_states:,}")
    print(f"Latest year present: {latest_year}")
    print("Rows per year:")
    for yr, cnt in per_year:
        print(f"  {yr}: {cnt:,}")

    print(f"\nRandom {_SAMPLE_SIZE}-row sample:")
    print("city | state | year | population")
    print("-" * 40)
    for city, state, year, pop in sample:
        print(f"{city} | {state} | {year} | {pop:,}")
    print()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    """Program entry‑point – dispatched through :pymeth:`argparse`."""
    cfg = Config.from_env()
    args = _build_parser().parse_args()

    if args.command == "load":
        _handle_load(args, cfg)
    elif args.command == "query":
        _handle_query(args, cfg)
    else:  # should be unreachable thanks to *required=True*
        raise RuntimeError("Unknown command")


if __name__ == "__main__":
    main()
