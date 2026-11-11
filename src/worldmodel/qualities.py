"""Core 0.4 Stage C1 (LABS-1.016): qualities, units and measurements. Mixed into WorldModel.

World Ontology v0.2 §3.3 and the Core 0.4 plan 9.2. A measurement is kept as three things:
- the measuring activity: an event description classified `measurement` (operator as actor, the bearer as patient,
  the instrument as instrument), with its occurrence interval on its source's attestation;
- the result record: an information-object holding what the act produced (raw value, raw unit, standard
  uncertainty u, coverage factor k, conditions, calibration reference);
- the reported content: has-quality(bearer, quality, unit: SI unit) with the range [v - k u, v + k u] converted to SI
  and its coverage level, attested by the source with basis observation.
produced(activity, result) and reports(result, content) link them. Measurement, observation basis, assertion and the
perspective's acceptance stay separate: a design value is a has-quality statement with no result record. Compatibility
is reported (possibly compatible / incompatible / incomparable, with the reason), never reconciled (v0.2
clarification B).
"""

import math
from datetime import datetime, timezone

from .keys import check_new_id
from .semantics import Status, acceptance_state, superseded, usable, verdict

SYSTEM = "system"
FAR = datetime(2200, 1, 1, tzinfo=timezone.utc)      # judgement time for timeless link contents
LEVEL_TOLERANCE = 1e-6


def coverage_level(k):
    """The coverage probability of a normal distribution within +-k standard uncertainties (k = 2: 0.9545)."""
    return math.erf(k / math.sqrt(2.0))


class QualitiesMixin:
    # ---- reference data --------------------------------------------------------------------------------------------
    def _set_attributes(self, thing, kind, attrs):
        from . import typeql as q
        from .model import WRITE
        parts, params = [], {"id": thing}
        for i, (name, value) in enumerate(attrs):
            parts.append(f"has {name} == $v{i}")
            params[f"v{i}"] = value
        if parts:
            with self.driver.transaction(self.database, WRITE) as tx:
                q.run(tx, f"match $x isa {kind}, has wm-id == $id; insert $x {', '.join(parts)};", params)
                tx.commit()

    def define_unit(self, name, dimension, si_factor=1.0, si_offset=0.0, id=None):
        """A unit of a dimension; si = raw * si_factor + si_offset. The SI unit of a dimension has factor 1, offset 0."""
        if not (math.isfinite(si_factor) and si_factor > 0 and math.isfinite(si_offset)):
            raise ValueError("si_factor must be positive and finite, si_offset finite")
        uid = self.add_entity("unit", name, id=id)
        self._set_attributes(uid, "unit", [("dimension", dimension), ("si-factor", float(si_factor)),
                                           ("si-offset", float(si_offset))])
        return uid

    def define_quality_kind(self, name, dimension=None, id=None):
        """A quality kind; numeric kinds have a dimension (mass), categorical ones need none (colour, condition)."""
        qid = self.add_entity("quality-kind", name, id=id)
        if dimension:
            self._set_attributes(qid, "quality-kind", [("dimension", dimension)])
        return qid

    def _unit(self, unit):
        from . import typeql as q
        from .model import READ
        with self.driver.transaction(self.database, READ) as tx:
            rows = q.rows(tx, """match $u isa unit, has wm-id == $id, has dimension $d, has si-factor $f,
                has si-offset $o;""", {"id": unit})
        if not rows:
            raise ValueError(f"{unit!r} is not a unit with a dimension")
        return q.opt(rows[0], "d"), q.opt(rows[0], "f"), q.opt(rows[0], "o")

    def _dimension_of(self, quality):
        from . import typeql as q
        from .model import READ
        with self.driver.transaction(self.database, READ) as tx:
            rows = q.rows(tx, "match $k isa quality-kind, has wm-id == $id, has dimension $d;", {"id": quality})
        return q.opt(rows[0], "d") if rows else None

    def si_unit(self, dimension):
        """The dimension's SI unit (si-factor 1, si-offset 0); one must be defined."""
        from . import typeql as q
        from .model import READ
        with self.driver.transaction(self.database, READ) as tx:
            rows = q.rows(tx, """match $u isa unit, has wm-id $id, has dimension == $d, has si-factor $f,
                has si-offset $o;""", {"d": dimension})
        found = sorted(q.opt(r, "id") for r in rows if q.opt(r, "f") == 1.0 and q.opt(r, "o") == 0.0)
        if not found:
            raise ValueError(f"no SI unit (factor 1, offset 0) is defined for dimension {dimension!r}")
        return found[0]

    def convert(self, value, unit, to=None):
        """A value in `unit` expressed in `to` (default: the SI unit); refused across dimensions."""
        d, f, o = self._unit(unit)
        si = value * f + o
        if to is None:
            return si
        d2, f2, o2 = self._unit(to)
        if d2 != d:
            raise ValueError(f"cannot convert {d} ({unit}) to {d2} ({to})")
        return (si - o2) / f2

    # ---- writing a measurement -------------------------------------------------------------------------------------
    def measure(self, world, bearer, quality, value, unit, uncertainty, k=2.0, start=None, end=None, instrument=None,
                operator=None, conditions=(), calibration=None, attester=SYSTEM, occurrence=None, persists=False,
                supersedes=None, id=None):
        """Record a measurement of `quality` of `bearer`: the activity (start..end), the result record (value in `unit`
        with standard uncertainty and coverage factor k, conditions, calibration reference) and the reported content
        (the SI range [v - k u, v + k u] with its coverage level), linked by produced and reports, all attested by
        `attester` (basis observation). The content attestation, the result record and rests-on(attestation, record)
        are written in one transaction (D-C-2). The content is attested over the activity's interval, or from its start until
        superseded when `persists` (the source asserts the value lasts). `supersedes`: the attestation id of an earlier
        reported content this corrects. The unit's dimension must be the quality kind's. Returns the ids."""
        dim = self._dimension_of(quality)
        udim, factor, _ = self._unit(unit)
        if dim is None or udim != dim:
            raise ValueError(f"unit {unit!r} ({udim}) does not measure {quality!r} ({dim})")
        if not (math.isfinite(value) and math.isfinite(uncertainty) and uncertainty >= 0 and k > 0):
            raise ValueError("value and uncertainty must be finite, uncertainty >= 0, k > 0")
        end = end or start
        roles = {"patient": bearer}
        if operator:
            roles["actor"] = operator
        if instrument:
            roles["instrument"] = instrument
        activity = self.account(world, roles, start, end, kind="measurement", occurrence=occurrence, attester=attester,
                                id=f"{id}-activity" if id else None)
        record = check_new_id(f"{id}-result" if id else self._mint("result"))
        lo, hi = sorted((self.convert(value - k * uncertainty, unit), self.convert(value + k * uncertainty, unit)))
        params = {"lower": lo, "upper": hi, "coverage-level": coverage_level(k)}
        content_roles = {"bearer": bearer, "quality": quality, "unit": self.si_unit(dim)}
        valid = {"start": start, "until_superseded": True} if persists else {"start": start, "end": end}
        attrs = ([("raw-value", float(value)), ("standard-uncertainty", float(uncertainty)),
                  ("coverage-factor", float(k))] + [("condition", c) for c in sorted(set(conditions))]
                 + ([("calibration-ref", calibration)] if calibration else []))

        def write_record(tx):             # inside the content attestation's transaction (D-C-2: atomic)
            from . import typeql as q
            parts = "".join(f", has {name} == $v{i}" for i, (name, _) in enumerate(attrs))
            q.run(tx, f"""match $u isa unit, has wm-id == $unit;
                insert $r isa information-object, has wm-id == $id, has name == $n{parts};
                expressed-in (record: $r, unit: $u);""",
                  {"id": record, "n": f"result of {activity}", "unit": unit,
                   **{f"v{i}": v for i, (_, v) in enumerate(attrs)}})
            return record

        content = self.attest(world, "has-quality", content_roles, params=params, basis="observation",
                              attester=attester, supersedes=supersedes, evidence=[write_record], **valid)
        produced = self.attest(world, "produced", {"activity": activity, "result": record}, until_superseded=True,
                               attester=attester)
        key = self._content_key(content)
        reports = self.attest(world, "reports", {"result": record, "content": self.proposition_id(key)},
                              until_superseded=True, attester=attester)
        return {"activity": activity, "result": record, "content": content, "produced": produced, "reports": reports,
                "range": (lo, hi), "coverage_level": params["coverage-level"]}

    def evidence_of(self, attestation):
        """The result records an attestation rests on (rests-on links; D-C-2). Structural: not judged."""
        from . import typeql as q
        from .model import READ
        with self.driver.transaction(self.database, READ) as tx:
            return sorted({q.opt(r, "rid") for r in q.rows(tx, """match $a isa attestation, has wm-id == $id;
                rests-on (attestation: $a, record: $r); $r has wm-id $rid;""", {"id": attestation})})

    def _content_key(self, attestation):
        return self._attestation(attestation)["content"]

    def _record(self, record):
        from . import typeql as q
        from .model import READ
        with self.driver.transaction(self.database, READ) as tx:
            rows = q.rows(tx, """match $r isa information-object, has wm-id == $id, has raw-value $v,
                has standard-uncertainty $u, has coverage-factor $k; expressed-in (record: $r, unit: $un);
                $un has wm-id $unit; try { $r has calibration-ref $cal; };""", {"id": record})
            conds = sorted({q.opt(r, "c") for r in q.rows(tx, """match $r isa information-object, has wm-id == $id,
                has condition $c;""", {"id": record})})
        if not rows:
            return None
        r = rows[0]
        return {"record": record, "raw_value": q.opt(r, "v"), "raw_unit": q.opt(r, "unit"),
                "standard_uncertainty": q.opt(r, "u"), "coverage_factor": q.opt(r, "k"), "conditions": conds,
                "calibration": q.opt(r, "cal")}

    # ---- reading ---------------------------------------------------------------------------------------------------
    def measurements(self, world, bearer, quality, t=None, as_of=None, perspective=SYSTEM):
        """Every stated value of `quality` of `bearer`, each with its attestation's judgement for the perspective
        (accepted, unreviewed, rejected, retracted, superseded) and its provenance. Values reported by a result record
        rest on result records (rests-on) and are measurements (with each record and the activity that produced it);
        values without one are statements, with
        their basis (a design specification by testimony, a reading noted without a record). If t is given, only
        attestations that hold at t."""
        from .keys import proposition_id
        atts, ident = self._view(world, as_of, perspective, "has-quality", [bearer])
        out = []
        for a in sorted(atts.values(), key=lambda a: a.id):
            if not (self.is_a(a.ctype, "has-quality") and bearer in a.roles.get("bearer", [])
                    and quality in a.roles.get("quality", []) and a.params.get("lower") is not None):
                continue
            if t is not None and verdict(a, t) is not True:
                continue
            records = []
            pid = proposition_id(a.content)
            # Provenance is the attestation's own rests-on links (D-C-2): never matched by source, time or content.
            for rec in self.evidence_of(a.id):
                detail = self._record(rec) or {"record": rec}
                reports = [e for e in self._claims(world, rec, ("reports",), t or FAR, as_of, perspective)
                           if pid in e["roles"].get("content", [])]
                detail["report"] = self._verdict_label(reports[0]) if reports else "none"
                acts = [x for e in self._claims(world, rec, ("produced",), t or FAR, as_of, perspective)
                        for x in e["roles"].get("activity", [])]
                detail["activities"] = []
                for act in acts:
                    span = self.interval(world, act, as_of, perspective)
                    roles = (self.content(act) or {}).get("roles", {})
                    detail["activities"].append({
                        "activity": act, "start": span[0] if span else None, "end": span[1] if span else None,
                        "operator": roles.get("actor", []), "instrument": roles.get("instrument", []),
                        "occurrences": self.occurrences_of(world, act, as_of, perspective)})
                records.append(detail)
            state = "superseded" if superseded(a, perspective, as_of) else acceptance_state(a, perspective, as_of)
            out.append({"attestation": a.id, "content": a.content, "kind": "measurement" if records else "statement",
                        "range": (a.params["lower"], a.params["upper"]), "unit": a.roles.get("unit", [None])[0],
                        "coverage_level": a.params.get("coverage-level"), "attester": a.attester, "basis": a.basis,
                        "acceptance": state, "usable": usable(a, perspective, as_of) and a.polarity,
                        "valid": (a.start, a.end), "records": records, "_record": a})
        return out

    def compare_measurements(self, world, bearer, quality, t=None, as_of=None, perspective=SYSTEM):
        """Compare the measurements the perspective accepts (v0.2 clarification B). Each pair is "possibly compatible"
        (comparable and the ranges overlap: one value could explain both, which is not agreement), "incompatible"
        (comparable and disjoint) or "incomparable" (different coverage levels, conditions or SI units, or valid
        times that do not overlap), with the reason. Nothing is combined. status: DISPUTED if any comparable pair is
        incompatible; otherwise the accepted measurements' status. Statements (no result record) are listed apart and
        never compared with measurements; unaccepted measurements are listed as alternatives."""
        from .semantics import answer_status
        everything = self.measurements(world, bearer, quality, t, as_of, perspective)
        used = [m for m in everything if m["kind"] == "measurement" and m["usable"]]
        pairs = []
        for i, a in enumerate(used):
            for j in range(i + 1, len(used)):
                b = used[j]
                reason = self._incomparable(a, b)
                if reason:
                    rel = "incomparable"
                else:
                    (al, ah), (bl, bh) = a["range"], b["range"]
                    rel = "possibly compatible" if al <= bh and bl <= ah else "incompatible"
                pairs.append({"a": a["attestation"], "b": b["attestation"], "relation": rel, "reason": reason})
        if any(p["relation"] == "incompatible" for p in pairs):
            status = Status.DISPUTED
        elif used:
            status = answer_status([m["_record"] for m in used])
        else:
            status = Status.UNKNOWN if everything else Status.NOT_YET_KNOWN
        strip = [{k: v for k, v in m.items() if k != "_record"} for m in everything]
        return {"bearer": bearer, "quality": quality, "status": status,
                "measurements": [m for m in strip if m["kind"] == "measurement" and m["usable"]],
                "pairs": pairs,
                "alternatives": [m for m in strip if m["kind"] == "measurement" and not m["usable"]],
                "statements": [m for m in strip if m["kind"] == "statement"]}

    @staticmethod
    def _incomparable(a, b):
        if a["unit"] != b["unit"]:
            return "different units (no common SI unit)"
        la, lb = a["coverage_level"], b["coverage_level"]
        if la is None or lb is None or abs(la - lb) > LEVEL_TOLERANCE:
            return f"different coverage levels ({la} vs {lb})"
        ca = {tuple(r.get("conditions", [])) for r in a["records"]}
        cb = {tuple(r.get("conditions", [])) for r in b["records"]}
        if ca != cb:
            return f"different measurement conditions ({sorted(ca)} vs {sorted(cb)})"
        (sa, ea), (sb, eb) = a["valid"], b["valid"]
        a0 = sa.earliest if sa else None
        b0 = sb.earliest if sb else None
        a1 = ea.latest if ea else None
        b1 = eb.latest if eb else None
        if (a1 is not None and b0 is not None and a1 <= b0) or (b1 is not None and a0 is not None and b1 <= a0):
            return "valid times do not overlap"
        return None
