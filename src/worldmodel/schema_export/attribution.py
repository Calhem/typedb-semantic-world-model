"""Core and profile attribution by verified replay (LABS-1.024 E-2, as approved under LABS-1.032 and LABS-1.033).

The database records which modules are installed (schema-module records) but not what each one added. The replay
installs those modules, from this repository's code, into temporary databases (always deleted):

1. the recorded core modules, one at a time in their canonical order, noting the facts each step adds;
2. for each recorded profile, the core and then that profile alone, noting the facts it adds;
3. the core and every recorded profile together: the **complete replay**.

**Verification** passes only if every recorded module is known to this code at the recorded version, every replay
step succeeds, and the complete replay's schema facts (every declaration, annotation and function text) and module
records equal the target's exactly. Each fact then gets one status (section 10 of the design):

- `attributed`: verified, and exactly one module adds it;
- `shared`: verified, and more than one profile adds it (each is replayed on its own, so sharing is proven);
- `consistent_unverified`: verification failed, but some replay step adds it (the candidates are listed);
- `unresolved`: no replay step adds it, or the attribution cannot be established.

A partial replay never produces `attributed` or `shared`.

**Reproducibility, not history.** A verified attribution says the schema is reproducible from the recorded modules,
and which module adds each declaration in that reproduction. It is not the database's installation history (install
order, in-place upgrades, changes later undone), which TypeDB does not keep and the export never claims.

**What replay cannot see.** TypeDB accepts a declaration that repeats one already in the schema, without change. A
fact a later module repeats is attributed to the module that first adds it; the repeat, found in the later module's
source text, is reported separately as a `repository` note (`also_declared_in_source`), never as ownership.

Module data (E-5) is attributed the same way: the concept and functional-slot records each replay step writes.
"""

from dataclasses import dataclass, field
from pathlib import Path

from ..model import MODULES, SCHEMA_DIR, SYSTEM, WorldModel
from ..profiles import PROFILE_PREFIX, PROFILES
from .crosscheck import temporary_name
from .introspect import READ, read_module_data, read_modules
from .parse import facts, parse_schema
from .sourcescan import scan

SETUP = "WorldModel.create"      # the step after the core modules: the system agent and the core functional slots


@dataclass
class Step:
    module: str
    added: set                   # fact ids added (or whose payload changed) by this step
    removed: set
    data_added: set


@dataclass
class Attribution:
    verified: bool
    problems: list
    modules: list                # one row per recorded module (and the setup step)
    facts: dict                  # fact id -> {"status", "modules", "also_declared_in_source"?}
    data: dict                   # module-data record -> {"status", "modules", "in_database"}
    data_verified: bool
    data_problems: list
    source: dict                 # module -> {"files", "statements", "unread", "missing_from_scan"} (repository)
    steps: list = field(default_factory=list)


def classify(verified, modules):
    """The status of one fact or record, from the verification result and the replay steps that add it."""
    if verified:
        return "shared" if len(modules) > 1 else "attributed" if modules else "unresolved"
    return "consistent_unverified" if modules else "unresolved"


def registry(profiles=None):
    """module name -> {"kind", "version", "files"} for every module this code can replay."""
    reg = {name: {"kind": "core", "version": v, "files": [SCHEMA_DIR / f for f in files], "profile": None}
           for name, (v, files) in MODULES.items()}
    for p in (PROFILES if profiles is None else profiles).values():
        reg[p.module] = {"kind": "profile", "version": p.version, "files": [Path(f) for f in p.schema], "profile": p}
    return reg


class _Replayer:
    def __init__(self, driver, prefix):
        self.driver, self.prefix, self.names = driver, prefix, []

    def new(self):
        name = temporary_name(self.prefix)
        self.driver.databases.create(name)
        self.names.append(name)
        return WorldModel(self.driver, name)

    def state(self, wm):
        f = facts(parse_schema(self.driver.databases.get(wm.database).schema()))
        with self.driver.transaction(wm.database, READ) as tx:
            kinds = {v["subject"]: v["type_kind"] for v in f.values() if v["kind"] == "type"}
            return f, read_module_data(tx, kinds), read_modules(tx, kinds)

    @staticmethod
    def diff(module, before, after):
        (f0, d0, _), (f1, d1, _) = before, after
        added = {k for k, v in f1.items() if f0.get(k) != v}
        return Step(module, added, set(f0) - set(f1), set(d1) - set(d0))

    def core(self, modules):
        """A database with the recorded core modules installed one at a time, as WorldModel.create does it."""
        wm = self.new()
        steps, prev = [], ({}, frozenset(), {})
        for m in modules:
            wm.install_module(m)
            now = self.state(wm)
            steps.append(self.diff(m, prev, now))
            prev = now
        wm.add_entity("social-object", "system reasoner", id=SYSTEM)
        if wm.has_proposition_ids():
            wm._declare_core_slots()
        now = self.state(wm)
        steps.append(self.diff(SETUP, prev, now))
        return wm, steps, now

    def profile(self, wm, module, profile):
        before = self.state(wm)
        wm.install_profile(profile)
        after = self.state(wm)
        return self.diff(module, before, after), after

    def close(self):
        for n in self.names:
            if self.driver.databases.contains(n):
                self.driver.databases.get(n).delete()


def attribute(driver, snap, target_facts, profiles=None, prefix="wm-export-tmp-"):
    """Attribute every fact of the target (parse.facts of its schema text) to modules, by replay."""
    reg = registry(profiles)
    recorded = snap.modules
    problems, rows = [], []
    core = [m for m in MODULES if m in recorded]
    profs = sorted(m for m in recorded if m.startswith(PROFILE_PREFIX))
    other = sorted(m for m in recorded if m not in MODULES and not m.startswith(PROFILE_PREFIX))
    status = {}
    for m in core + profs + other:
        info = reg.get(m)
        if info is None:
            status[m] = "unknown"
            problems.append(f"module {m!r} (version {recorded[m]}) is recorded in the database but unknown to this code")
        elif info["version"] != recorded[m]:
            status[m] = "version-mismatch"
            problems.append(f"module {m!r}: the database records version {recorded[m]}, this code has "
                            f"{info['version']}")
        else:
            status[m] = "replayable"
    if not recorded:
        problems.append("the database records no modules, so there is nothing to replay")
    if profs and any(m not in recorded for m in MODULES):
        problems.append("profiles are recorded but the full core is not")

    steps, diffs, combined = [], {}, None
    rp = _Replayer(driver, prefix)
    try:
        core_ok = bool(core) and all(status[m] == "replayable" for m in core)
        if core_ok:
            try:
                first, steps, combined = rp.core(core)
            except Exception as e:                        # a module that no longer installs: reported, not hidden
                core_ok, combined = False, None
                problems.append(f"the core replay failed: {' '.join(str(e).split())[:300]}")
        replayable_profiles = [m for m in profs if status[m] == "replayable"]
        if core_ok and replayable_profiles:
            for i, m in enumerate(replayable_profiles):
                try:
                    wm = first if i == 0 else rp.core(core)[0]
                    diffs[m], after = rp.profile(wm, m, reg[m]["profile"])
                    if i == 0:
                        combined = after
                except Exception as e:
                    status[m] = "replay-failed"
                    problems.append(f"replaying {m!r} failed: {' '.join(str(e).split())[:300]}")
            try:
                for m in replayable_profiles[1:]:
                    if status[m] == "replayable":
                        _, combined = rp.profile(first, m, reg[m]["profile"])
            except Exception as e:
                combined = None
                problems.append(f"the complete replay failed: {' '.join(str(e).split())[:300]}")
    finally:
        rp.close()

    complete = core_ok and all(s == "replayable" for s in status.values()) and combined is not None
    if complete:
        rf, _, rmodules = combined
        missing = sorted(set(rf) - set(target_facts))
        extra = sorted(set(target_facts) - set(rf))
        changed = sorted(k for k in set(rf) & set(target_facts) if rf[k] != target_facts[k])
        problems += [f"in the replay but not in the database: {k}" for k in missing]
        problems += [f"in the database but not in the replay: {k}" for k in extra]
        problems += [f"different in the replay and the database: {k}" for k in changed]
        if rmodules != recorded:
            problems.append(f"the replay records modules {rmodules}, the database {recorded}")
    verified = complete and not problems

    # ---- per-fact status -----------------------------------------------------------------------------------------
    def contributors(fid):
        core_by = [s.module for s in steps if fid in s.added]
        if core_by:
            return core_by[-1:]          # the last core step that added (or changed) it
        return [m for m in profs if m in diffs and fid in diffs[m].added]

    out = {}
    for fid in target_facts:
        mods = contributors(fid)
        out[fid] = {"status": classify(verified, mods), "modules": mods}

    # ---- repository notes: repeats a replay cannot see, and what the scan could not read --------------------------
    source = {}
    kinds = {v["subject"]: v["type_kind"] for v in target_facts.values() if v["kind"] == "type"}
    for m in core + profs:
        if m not in reg:
            continue
        declared, unread, statements = set(), [], 0
        for f in reg[m]["files"]:
            sf = scan(Path(f).read_text(), Path(f).name, kinds)
            statements += len(sf.statements)
            unread += [f"{Path(f).name}:{line}" for line, _ in sf.unread]
            declared |= {x for st in sf.statements for x in st.facts}
        added = (next((s.added for s in steps if s.module == m), None) if m in MODULES
                 else diffs[m].added if m in diffs else None)
        source[m] = {"files": [_relative(f) for f in reg[m]["files"]], "statements": statements, "unread": unread,
                     "missing_from_scan": sorted(added - declared) if added is not None else None}
        for fid in declared & set(target_facts):
            if m not in out[fid]["modules"] and out[fid]["modules"]:
                out[fid].setdefault("also_declared_in_source", []).append(m)

    # ---- module data -----------------------------------------------------------------------------------------------
    data, data_problems = {}, []
    produced = {}
    for s in steps:
        for rec in s.data_added:
            produced.setdefault(rec, []).append(s.module)
    for m, d in diffs.items():
        for rec in d.data_added:
            if rec not in {r for s in steps for r in s.data_added}:
                produced.setdefault(rec, []).append(m)
    for rec, mods in produced.items():
        present = rec in snap.data
        if not present:
            data_problems.append(f"written by {', '.join(mods)} in the replay but not in the database: {rec}")
        data[rec] = {"modules": mods, "in_database": present}
    data_verified = verified and not data_problems
    for rec, d in data.items():
        d["status"] = classify(data_verified, d["modules"]) if d["in_database"] else "unresolved"

    for m in core + profs + other:
        counts = {}
        for v in out.values():
            if m in v["modules"]:
                counts[v["status"]] = counts.get(v["status"], 0) + 1
        info = reg.get(m)
        rows.append({"name": m, "kind": info["kind"] if info else ("profile" if m.startswith(PROFILE_PREFIX) else "unknown"),
                     "recorded_version": recorded[m], "code_version": info["version"] if info else None,
                     "replay": status[m], "facts": counts})
    if steps:
        rows.append({"name": SETUP, "kind": "setup", "recorded_version": None, "code_version": None,
                     "replay": "replayable", "facts": {}})
    return Attribution(verified, problems, rows, out, data, data_verified, data_problems, source, steps)


def _relative(path):
    path = Path(path).resolve()
    root = SCHEMA_DIR.parent
    try:
        return str(path.relative_to(root))
    except ValueError:
        return path.name
