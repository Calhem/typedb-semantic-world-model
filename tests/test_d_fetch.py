"""Stage D optimisation: attestation attributes are read with a `fetch` stage. The records must be exactly what the
earlier concept-row reads returned (checked against an independent row-based read here), on both query paths."""

from datetime import datetime, timezone

from conftest import T
from worldmodel import WorldModel
from worldmodel import typeql as q
from worldmodel.model import READ


def rows_oracle(wm, aid):
    """The attestation's attributes read the old way: concept rows with `try` blocks."""
    with wm.driver.transaction(wm.database, READ) as tx:
        (r,) = q.rows(tx, """match $a isa attestation, has wm-id == $id, has stance $st, has polarity $pol,
            has basis $bs, has end-basis $eb, has recorded-at $rec;
            try { $a has valid-from-earliest $sfe; }; try { $a has valid-from-latest $sfl; };
            try { $a has valid-to-earliest $tte; }; try { $a has valid-to-latest $ttl; }; try { $a has credence $cr; };""",
                      {"id": aid})
    return {k: q.opt(r, k) for k in ("st", "pol", "bs", "eb", "rec", "sfe", "sfl", "tte", "ttl", "cr")}


def test_fetched_records_match_row_reads_on_both_paths(wm):
    w = wm.create_world("actual", id="actual")
    for kind, n in (("physical-object", "rock"), ("place", "crater"), ("quality-kind", "mass"), ("unit", "kg"),
                    ("physical-object", "A")):
        wm.add_entity(kind, n, id=n)
    precise = datetime(2026, 11, 9, 10, 0, 0, 123456, tzinfo=timezone.utc)
    loc = wm.attest(w, "located-at", {"located": "rock", "place": "crater"}, start=precise, end=(T("11:00"), None),
                    credence=0.75, attester="A")
    mass = wm.attest(w, "has-quality", {"bearer": "rock", "quality": "mass", "unit": "kg"},
                     params={"lower": 3.47, "upper": 3.55, "coverage-level": 0.95}, start=(T("09:00"), T("09:30")),
                     until_superseded=True)
    full = WorldModel.open(wm.database, driver=wm.driver)
    full.selective = False
    for model in (wm, full):
        for loaded in (model.visible(w, perspective="A"),                                   # untyped load
                       model._load(w, types=["has-quality"], subjects=["rock"], perspective="A")):  # typed, selective
            for aid, rec in loaded.items():
                o = rows_oracle(wm, aid)
                assert (rec.stance, rec.polarity, rec.basis, rec.end_basis, rec.recorded_at, rec.credence) == \
                    (o["st"], o["pol"], o["bs"], o["eb"], o["rec"], o["cr"])
                assert (rec.start.earliest, rec.start.latest) == (o["sfe"], o["sfl"])
                assert (rec.end.earliest if rec.end else None, rec.end.latest if rec.end else None) == (o["tte"], o["ttl"])
            if mass in loaded:
                assert loaded[mass].params == {"lower": 3.47, "upper": 3.55, "coverage-level": 0.95}
    rec = full.visible(w, perspective="A")[loc]
    assert rec.start.earliest == precise and rec.end.latest is None and rec.credence == 0.75
    assert wm.value_at(w, "located-at", "rock", T("10:30"), perspective="A") == \
        full.value_at(w, "located-at", "rock", T("10:30"), perspective="A")
