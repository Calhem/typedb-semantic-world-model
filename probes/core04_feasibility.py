"""LABS-1.001 Core 0.4 planning: feasibility probes on TypeDB 3.14.1. EXPLORATORY, not approved architecture.

    uv run python -I probes/core04_feasibility.py > probes/core04_feasibility.out.json

Loads the merged Core 0.3 schema (schema/core/core-0.3.tql, unchanged) into throwaway databases (wm-c04-*), adds the
DRAFT definitions below (which exist only in this probe), inserts small scenarios, and runs the representative queries
used in docs/plans/core-0.4-plan.md. Every database is deleted afterwards. Nothing here changes schema/ or src/.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from typedb.driver import TransactionType as T  # noqa: E402

from worldmodel import connect  # noqa: E402
from worldmodel import typeql as q  # noqa: E402

CORE = (ROOT / "schema" / "core" / "core-0.3.tql").read_text()

# DRAFT Core 0.4 additions (Stages A-C), exploratory only.
DRAFT_CORE = """define
attribute x-min, value double; attribute x-max, value double; attribute y-min, value double;
attribute y-max, value double; attribute z-min, value double; attribute z-max, value double;
attribute qw, value double; attribute qx, value double; attribute qy, value double; attribute qz, value double;
attribute tx, value double; attribute ty, value double; attribute tz, value double;
attribute dimension, value string; attribute si-factor, value double; attribute si-offset, value double;
unit owns dimension, owns si-factor, owns si-offset;

proposition owns wm-id @key;                                            # Q-A1: a second key on propositions
relation constitution sub proposition, relates constituted, relates constituent;
relation positioned-in sub proposition, relates positioned, relates frame,
  owns x-min, owns x-max, owns y-min, owns y-max, owns z-min, owns z-max, owns qw, owns qx, owns qy, owns qz;
relation anchored-to sub proposition, relates frame, relates anchor;
relation frame-transform sub proposition, relates parent, relates child,
  owns tx, owns ty, owns tz, owns qw, owns qx, owns qy, owns qz;
relation causes sub proposition, relates cause, relates effect;
relation has-capability sub proposition, relates bearer, relates capability;
particular plays constitution:constituted, plays constitution:constituent, plays anchored-to:anchor,
  plays has-capability:bearer;
physical-object plays positioned-in:positioned;
spatial-frame plays positioned-in:frame, plays anchored-to:frame, plays frame-transform:parent, plays frame-transform:child;
category plays has-capability:capability;
event plays causes:cause, plays causes:effect;
occurrence plays causes:cause, plays causes:effect;

fun frames_reachable($f: spatial-frame, $w: world) -> { spatial-frame }:
  match
    { $c isa frame-transform (parent: $f, child: $g); attestation (content: $c, context: $w); } or
    { $c isa frame-transform (parent: $f, child: $m); attestation (content: $c, context: $w);
      let $g in frames_reachable($m, $w); };
  return { $g };

# Verified while probing: the declared return type must cover every type that can play the role (causes:effect is also
# played by occurrences, which share no supertype with events), so the match narrows $x to events (FIN4 otherwise).
fun effects_of($e: event, $w: world) -> { event }:
  match
    { $c isa causes (cause: $e, effect: $x); $x isa event; attestation (content: $c, context: $w); } or
    { $c isa causes (cause: $e, effect: $m); $m isa event; attestation (content: $c, context: $w);
      let $x in effects_of($m, $w); };
  return { $x };
"""

# DRAFT profile (Stage D), exploratory only: sortals, role specialisation, a domain relation.
DRAFT_PROFILE = """define
entity person sub physical-object;
entity organisation sub social-object;
relation pickup sub event, relates picker as actor, relates picked as patient;
relation employment sub proposition, relates employer, relates employee;
person plays pickup:picker, plays employment:employee;
physical-object plays pickup:picked;
organisation plays employment:employer;
"""

d = connect()


def fresh(name, *schemas):
    if d.databases.contains(name):
        d.databases.get(name).delete()
    d.databases.create(name)
    for text in schemas:
        with d.transaction(name, T.SCHEMA) as tx:
            tx.query(text).resolve()
            tx.commit()


def write(db, text):
    with d.transaction(db, T.WRITE) as tx:
        q.run(tx, text)
        tx.commit()


def read(db, text):
    with d.transaction(db, T.READ) as tx:
        return q.rows(tx, text)


def attempt(fn):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        return {"error": " ".join(str(e).split())[:300]}


out = {}

# ---- P1: draft schema loads on top of the merged Core 0.3 schema, and the profile on top of both ----------------------
db = "wm-c04-a"
out["P1 core-0.3 + draft core + draft profile load"] = attempt(lambda: (fresh(db, CORE, DRAFT_CORE, DRAFT_PROFILE), "accepted")[1])

# Common data: world, system agent, a robot (person kind for the profile test), frames, a box.
BASE = """insert $w isa world, has wm-id "actual", has world-kind "actual";
$s isa social-object, has wm-id "system";
$bob isa person, has wm-id "bob"; $box isa physical-object, has wm-id "box";
$rover isa physical-object, has wm-id "rover"; $rock isa physical-object, has wm-id "rock";
$sample isa physical-object, has wm-id "sample-12";
$map isa spatial-frame, has wm-id "map"; $base isa spatial-frame, has wm-id "rover-base";
$cam isa spatial-frame, has wm-id "rover-cam";
$acme isa organisation, has wm-id "acme"; $drive isa category, has wm-id "can-drive";"""


def att(content_var, aid, extra=""):
    return f'attestation (attester: $s, content: {content_var}, context: $w), has wm-id "{aid}", has stance "asserts", ' \
           f'has polarity true, has basis "testimony", has end-basis "until-superseded", has recorded-at 2030-01-01T00:00:00Z{extra};'


def scenario():
    write(db, BASE)
    write(db, """match $w isa world, has wm-id "actual"; $s isa social-object, has wm-id "system";
      $rock isa physical-object, has wm-id "rock"; $sample isa physical-object, has wm-id "sample-12";
      $map isa spatial-frame, has wm-id "map"; $base isa spatial-frame, has wm-id "rover-base";
      $cam isa spatial-frame, has wm-id "rover-cam"; $rover isa physical-object, has wm-id "rover";
      $box isa physical-object, has wm-id "box"; $bob isa person, has wm-id "bob"; $acme isa organisation, has wm-id "acme";
      $drive isa category, has wm-id "can-drive";
    insert
      $k isa constitution (constituted: $sample, constituent: $rock), has proposition-key "k-constitution", has wm-id "p:1";
      $t1 isa frame-transform (parent: $map, child: $base), has proposition-key "k-tf1", has wm-id "p:2",
        has tx 10.0, has ty 5.0, has tz 0.0, has qw 1.0, has qx 0.0, has qy 0.0, has qz 0.0;
      $t2 isa frame-transform (parent: $base, child: $cam), has proposition-key "k-tf2", has wm-id "p:3",
        has tx 0.2, has ty 0.0, has tz 1.1, has qw 1.0, has qx 0.0, has qy 0.0, has qz 0.0;
      $an isa anchored-to (frame: $base, anchor: $rover), has proposition-key "k-anchor", has wm-id "p:4";
      $pos isa positioned-in (positioned: $box, frame: $cam), has proposition-key "k-pos", has wm-id "p:5",
        has x-min 1.9, has x-max 2.1, has y-min -0.1, has y-max 0.1, has z-min 0.0, has z-max 0.2;
      $cap isa has-capability (bearer: $rover, capability: $drive), has proposition-key "k-cap", has wm-id "p:6";
      $emp isa employment (employer: $acme, employee: $bob), has proposition-key "k-emp", has wm-id "p:7";
      $e1 isa pickup (picker: $bob, picked: $box), has wm-id "e1";
      $e2 isa event (actor: $rover), has wm-id "e2"; $e3 isa event (actor: $rover), has wm-id "e3";
      $c1 isa causes (cause: $e1, effect: $e2), has proposition-key "k-c1", has wm-id "p:8";
      $c2 isa causes (cause: $e2, effect: $e3), has proposition-key "k-c2", has wm-id "p:9";
      $ini isa initiates (event: $e1, outcome: $k), has proposition-key "k-ini", has wm-id "p:10";
    """ + " ".join(att(v, f"a{i}") for i, v in enumerate(
        ["$k", "$t1", "$t2", "$an", "$pos", "$cap", "$emp", "$e1", "$e2", "$e3", "$c1", "$c2", "$ini"])))
    return "inserted"


if "error" not in str(out["P1 core-0.3 + draft core + draft profile load"]):
    out["P1b scenario insert"] = attempt(scenario)
    # P2: a proposition playing a role in another proposition (initiates.outcome = a constitution proposition).
    out["P2 proposition as role player (initiates outcome)"] = attempt(lambda: [
        q.opt(r, "k") for r in read(db, """match $i isa initiates (event: $e, outcome: $o); $o isa! $t;
          $o has proposition-key $k;""")])
    # P3: role specialisation: does a query on the general role `actor` find a specialised `picker` player?
    out["P3 query by `actor` finds `pickup:picker` players"] = attempt(lambda: sorted(
        q.opt(r, "id") for r in read(db, 'match $e isa event (actor: $x); $x has wm-id $id;')))
    out["P3b `isa event` includes the profile subtype; isa! gives its label"] = attempt(lambda: sorted(
        f'{q.opt(r, "id")}:{r.get("t").get_label()}' for r in read(db, 'match $e isa event, has wm-id $id; $e isa! $t;')))
    out["P3c role label of a specialised player"] = attempt(lambda: sorted(
        r.get("r").get_label() for r in read(db, 'match $e isa pickup, has wm-id "e1"; $e links ($r: $x);')))
    # P4: frame chain by recursive function (composition of transforms stays in Python).
    out["P4 frames reachable from map"] = attempt(lambda: sorted(
        q.opt(r, "id") for r in read(db, """match $f isa spatial-frame, has wm-id "map"; $w isa world, has wm-id "actual";
          let $g in frames_reachable($f, $w); $g has wm-id $id;""")))
    # P5: causal chain by recursive function.
    out["P5 effects of e1 (transitive)"] = attempt(lambda: sorted(
        q.opt(r, "id") for r in read(db, """match $e isa event, has wm-id "e1"; $w isa world, has wm-id "actual";
          let $x in effects_of($e, $w); $x has wm-id $id;""")))
    # P6: metric range filter through attestation: things whose x range lies within [1.5, 2.5] in rover-cam.
    out["P6 positioned within a box in a frame"] = attempt(lambda: sorted(
        q.opt(r, "id") for r in read(db, """match $f isa spatial-frame, has wm-id "rover-cam";
          $p isa positioned-in (positioned: $x, frame: $f), has x-min $a, has x-max $b; $a >= 1.5; $b <= 2.5;
          attestation (content: $p); $x has wm-id $id;""")))
    # P7: capability and employment (domain relation) queries.
    out["P7 capabilities of rover"] = attempt(lambda: [q.opt(r, "id") for r in read(db, """match
          $r isa physical-object, has wm-id "rover"; has-capability (bearer: $r, capability: $c); $c has wm-id $id;""")])
    out["P7b employees of acme (profile relation, polymorphic over proposition)"] = attempt(lambda: [
        q.opt(r, "id") for r in read(db, """match $o isa organisation, has wm-id "acme"; $p isa proposition;
          $p isa employment (employer: $o, employee: $x); $x has wm-id $id;""")])
    # P8: second key on propositions is enforced.
    out["P8 duplicate proposition wm-id rejected"] = attempt(lambda: (write(db, """match
          $rock isa physical-object, has wm-id "rock"; $b isa physical-object, has wm-id "box";
          insert constitution (constituted: $b, constituent: $rock), has proposition-key "k-other", has wm-id "p:1";"""),
        "ACCEPTED (unexpected)")[1])
    # P9: removing the profile while data uses it (migration, not uninstall).
    out["P9 undefine profile subtype with data"] = attempt(lambda: (
        d.transaction(db, T.SCHEMA).__enter__().query("undefine pickup;").resolve(), "accepted")[1])

d.databases.get(db).delete() if d.databases.contains(db) else None
out["leftover"] = [x.name for x in d.databases.all() if x.name.startswith("wm-c04-")]
print(json.dumps(out, indent=1, default=str))
