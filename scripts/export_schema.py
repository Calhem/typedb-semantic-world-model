"""Export the schema of a TypeDB database (LABS-1.024): schema.tql, schema.json, schema-explorer.html, manifest.json.

    uv run python scripts/export_schema.py <database> [--out DIR] [--require-verified]
    uv run python scripts/export_schema.py --reference [--out docs/schema]

--reference builds a temporary database with the full core and every registered profile, in their canonical order,
exports it, and deletes it: this is the committed reference export under docs/schema/.

Exit status: 0 exported; 1 refused (the exporter could not account for the schema exactly; nothing is written);
2 exported, but --require-verified was given and the replay did not verify the attribution.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from worldmodel import CORE_MODULES, PROFILES, WorldModel, connect  # noqa: E402
from worldmodel.schema_export import SchemaExportError  # noqa: E402
from worldmodel.schema_export.export import export_to  # noqa: E402

REFERENCE = "wm-schema-reference"


def build_reference(driver, name=REFERENCE):
    """The reference database: the full core, then every registered profile in registration order."""
    wm = WorldModel.create(name, driver=driver, modules=CORE_MODULES)
    for p in PROFILES:
        wm.install_profile(p)
    return wm


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("database", nargs="?")
    ap.add_argument("--reference", action="store_true", help="export a fresh reference database (core + profiles)")
    ap.add_argument("--out", type=Path, help="output directory (default: exports/<database>, or docs/schema)")
    ap.add_argument("--require-verified", action="store_true", help="exit 2 unless the attribution is verified")
    args = ap.parse_args(argv)
    if bool(args.database) == args.reference:
        ap.error("give a database name, or --reference")
    driver = connect()
    made = None
    try:
        if args.reference:
            if driver.databases.contains(REFERENCE):
                ap.error(f"database {REFERENCE!r} exists; delete it first")
            made = build_reference(driver)
            database, out = REFERENCE, args.out or ROOT / "docs" / "schema"
        else:
            database, out = args.database, args.out or ROOT / "exports" / args.database
        try:
            doc, written, timings = export_to(driver, database, out)
        except SchemaExportError as e:
            print(f"export refused: {e}", file=sys.stderr)
            return 1
        a = doc["attribution"]
        print(f"exported {database} to {out}: {', '.join(written)}")
        print(f"  schema: {doc['schema']['counts']}")
        print(f"  checks: parse exact, query cross-check passed, round trip identical")
        print(f"  attribution: {a['verification']} {a['counts']}")
        for p in a["problems"][:20]:
            print(f"    - {p}")
        print("  time: " + ", ".join(f"{k} {v:.2f} s" for k, v in timings.items()))
        return 2 if args.require_verified and a["verification"] != "verified" else 0
    finally:
        if made is not None:
            driver.databases.get(REFERENCE).delete()


if __name__ == "__main__":
    sys.exit(main())
