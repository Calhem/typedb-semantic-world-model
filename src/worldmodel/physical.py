"""Core 0.4 Stage A1 (LABS-1.006): physical structure on top of the v0.2 core. Mixed into WorldModel.

Writing goes through the ordinary attestation path (every fact is an attested proposition with a world, an attester,
a stance and an interval); reading goes through facts_about / value_at, so perspective, knowledge-time, world and
identity semantics are the core's. Nothing here stores answers.

Conventions (Core 0.4 plan 9.6): right-handed frames, metres, radians; unit quaternions (w, x, y, z), Hamilton,
active; a norm more than 1e-9 from 1 is rejected. frame-transform(parent P, child C) gives C's pose in P:
p_P = R(q)·p_C + t. A2 (LABS-1.007) composes transforms (spatial.py): derived positions are INFERRED and cite the
position and every transform used (rule frame-transform/v1); several chains must agree within 1e-9 m.
"""

import math

from .keys import as_ids
from .semantics import Identity, Status
from .spatial import AXES as _AXES, Transform, boxes_overlap, map_box, qmul, same_rotation

AXES = _AXES
QUAT_TOLERANCE = 1e-9
SYSTEM = "system"
MAX_HOPS = 8                 # longest frame chain searched
RULE = "frame-transform/v1"


def _range(axis, value):
    """A number (exact) or a (lower, upper) pair, as finite floats with lower <= upper."""
    lo, hi = (value, value) if isinstance(value, (int, float)) else value
    lo, hi = float(lo), float(hi)
    if not (math.isfinite(lo) and math.isfinite(hi)) or lo > hi:
        raise ValueError(f"{axis}: need finite lower <= upper, got {value!r}")
    return lo, hi


def _quaternion(q):
    """A unit quaternion (w, x, y, z); a norm more than 1e-9 from 1 is rejected (plan 9.6)."""
    if len(q) != 4:
        raise ValueError(f"a rotation is a quaternion (w, x, y, z), got {q!r}")
    w, x, y, z = (float(c) for c in q)
    norm = math.sqrt(w * w + x * x + y * y + z * z)
    if not all(math.isfinite(c) for c in (w, x, y, z)) or abs(norm - 1.0) > QUAT_TOLERANCE:
        raise ValueError(f"not a unit quaternion (norm {norm!r}): {q!r}")
    return w, x, y, z


def yaw(radians):
    """The unit quaternion for a rotation by `radians` about +z (a convenience for level frames)."""
    return (math.cos(radians / 2), 0.0, 0.0, math.sin(radians / 2))


class PhysicalMixin:
    # ---- writing ---------------------------------------------------------------------------------------------------
    def position(self, world, thing, frame, x, y, z, orientation=None, **attest):
        """Attest that `thing` is positioned in `frame`: each axis an exact value or a (lower, upper) range in metres,
        optionally with an orientation (unit quaternion). Returns the attestation id."""
        params = {}
        for axis, value in zip(AXES, (x, y, z)):
            params[f"{axis}-min"], params[f"{axis}-max"] = _range(axis, value)
        if orientation is not None:
            params.update(zip(("qw", "qx", "qy", "qz"), _quaternion(orientation)))
        return self.attest(world, "positioned-in", {"positioned": thing, "frame": frame}, params=params, **attest)

    def relate_frames(self, world, parent, child, translation, rotation=(1.0, 0.0, 0.0, 0.0), **attest):
        """Attest frame-transform(parent, child): the child's origin is at `translation` (metres) in the parent and its
        axes are rotated by `rotation` (unit quaternion). Returns the attestation id."""
        if parent == child:
            raise ValueError("a frame-transform relates two different frames")
        tx, ty, tz = (float(c) for c in translation)
        if not all(math.isfinite(c) for c in (tx, ty, tz)):
            raise ValueError(f"translation must be finite, got {translation!r}")
        qw, qx, qy, qz = _quaternion(rotation)
        return self.attest(world, "frame-transform", {"parent": parent, "child": child},
                           params={"tx": tx, "ty": ty, "tz": tz, "qw": qw, "qx": qx, "qy": qy, "qz": qz}, **attest)

    def anchor_frame(self, world, frame, anchor, **attest):
        """Attest that `frame` is attached to the particular `anchor` (one anchor at a time: a functional constraint)."""
        return self.attest(world, "anchored-to", {"frame": frame, "anchor": anchor}, **attest)

    # ---- reading ---------------------------------------------------------------------------------------------------
    def _facts(self, world, subject, t, type, as_of, perspective):
        return [f for f in self.facts_about(world, subject, t, as_of, perspective) if self.is_a(f["type"], type)]

    def poses(self, world, thing, t, as_of=None, perspective=SYSTEM):
        """The thing's positions that hold at t, one per frame statement: frame, per-axis (lower, upper), orientation,
        status and supporting attestations. Several positions in one frame are all listed (conflicts between
        positions are not judged in A1)."""
        out = []
        for f in self._facts(world, thing, t, "positioned-in", as_of, perspective):
            if thing not in f["roles"].get("positioned", []):
                continue
            p = f["params"]
            out.append({"frame": f["roles"]["frame"][0],
                        **{axis: (p[f"{axis}-min"], p[f"{axis}-max"]) for axis in AXES},
                        "orientation": tuple(p[k] for k in ("qw", "qx", "qy", "qz")) if "qw" in p else None,
                        "status": f["status"], "support": f["support"]})
        return sorted(out, key=lambda e: e["frame"])

    def frame_info(self, world, frame, t, as_of=None, perspective=SYSTEM):
        """What is known about a spatial frame at t: its name, what it is attached to, its transforms to parent and
        child frames (as stored: translation and rotation), and the things positioned in it."""
        facts = self.facts_about(world, frame, t, as_of, perspective)
        info = {"frame": frame, "name": self.names([frame]).get(frame), "anchored_to": [], "parents": [],
                "children": [], "positioned": []}
        for f in facts:
            roles, p = f["roles"], f["params"]
            if self.is_a(f["type"], "anchored-to"):
                info["anchored_to"] += [{"anchor": a, "status": f["status"]} for a in roles["anchor"]]
            elif self.is_a(f["type"], "frame-transform"):
                link = {"translation": (p["tx"], p["ty"], p["tz"]), "rotation": (p["qw"], p["qx"], p["qy"], p["qz"]),
                        "status": f["status"], "support": f["support"]}
                if frame in roles["child"]:
                    info["parents"].append({"parent": roles["parent"][0], **link})
                else:
                    info["children"].append({"child": roles["child"][0], **link})
            elif self.is_a(f["type"], "positioned-in"):
                info["positioned"] += roles["positioned"]
        info["positioned"] = sorted(set(info["positioned"]))
        return info

    def composition(self, world, whole, t, as_of=None, perspective=SYSTEM):
        """The part-of tree under `whole` at t: {"id", "parts": [subtrees]} from the direct parts that hold."""
        def tree(node, seen):
            direct = sorted(x for f in self._facts(world, node, t, "part-of", as_of, perspective)
                            if node in f["roles"].get("whole", []) for x in f["roles"]["part"])
            return {"id": node, "parts": [tree(p, seen | {p}) for p in direct if p not in seen]}
        return tree(whole, {whole})

    def contents(self, world, place, t, as_of=None, perspective=SYSTEM):
        """What a place contains at t: things located at it, and places that are part of it (with their contents)."""
        located = self.value_at(world, "located-at", place, t, as_of, perspective, key_role="place",
                                value_role="located")
        subplaces = sorted(x for f in self._facts(world, place, t, "part-of", as_of, perspective)
                           if place in f["roles"].get("whole", []) for x in f["roles"]["part"])
        return {"place": place, "located": list(located.values), "status": located.status.value,
                "places": [self.contents(world, p, t, as_of, perspective) for p in subplaces]}

    def materials(self, world, thing, t, as_of=None, perspective=SYSTEM, material="material"):
        """The material categories the thing is classified under at t: classes that are themselves classified as
        `material` (decision D-A1-1). Materials are categories, not types."""
        classes = sorted({c for f in self._facts(world, thing, t, "classified-as", as_of, perspective)
                          if thing in f["roles"].get("classified", []) for c in f["roles"]["class"]})
        out = []
        for c in classes:
            marks = self._facts(world, c, t, "classified-as", as_of, perspective)
            if any(c in f["roles"].get("classified", []) and material in f["roles"]["class"] for f in marks):
                out.append(c)
        return out

    def names(self, ids):
        """{id: name} for identified things (a convenience for readable output)."""
        from . import typeql as q
        from .model import READ
        out = {}
        with self.driver.transaction(self.database, READ) as tx:
            for i in sorted(set(as_ids(ids))):
                rows = q.rows(tx, "match $x has wm-id == $id, has name $n;", {"id": i})
                if rows:
                    out[i] = q.opt(rows[0], "n")
        return out

    # ---- A2: frame chains and derived positions ------------------------------------------------------------------
    def _frame_edges(self, world, t, as_of, perspective):
        """The frame-transform contents judged for the perspective at t, as graph edges. Holding contents are usable;
        polarity-disputed ones are kept and marked, so any chain through them is DISPUTED."""
        if self.selective:
            atts = self._load(world, as_of, types=["frame-transform"], at=t, perspective=perspective)
        else:
            atts = {k: a for k, a in self.visible(world, as_of, perspective).items() if self.is_a(a.ctype, "frame-transform")}
        edges = []
        for cls, (val, support, _) in self._judge(list(atts.values()), Identity([], perspective, as_of), t,
                                                  perspective, as_of).items():
            if val is False:
                continue
            roles, p = dict(cls[1]), dict(cls[2])
            edges.append({"parent": roles["parent"][0], "child": roles["child"][0],
                          "transform": Transform((p["qw"], p["qx"], p["qy"], p["qz"]), (p["tx"], p["ty"], p["tz"])),
                          "support": sorted(a.id for a in support), "disputed": val == "disputed"})
        return sorted(edges, key=lambda e: (e["parent"], e["child"], e["support"]))

    @staticmethod
    def _chains(edges, source, target, max_hops=MAX_HOPS):
        """Every simple chain of frame-transform edges from `source` to `target` (each edge usable in either direction),
        with the composed transform mapping source coordinates to target coordinates. Shortest first."""
        found = []

        def walk(frame, visited, steps, total):
            if frame == target:
                found.append((steps, total))
                return
            if len(steps) >= max_hops:
                return
            for i, e in enumerate(edges):
                if any(s["edge"] == i for s in steps):
                    continue
                if e["child"] == frame and e["parent"] not in visited:
                    nxt, step, direction = e["parent"], e["transform"], "forward"
                elif e["parent"] == frame and e["child"] not in visited:
                    nxt, step, direction = e["child"], e["transform"].inverse(), "inverse"
                else:
                    continue
                walk(nxt, visited | {nxt}, steps + [{"edge": i, "direction": direction}], step.then(total))

        walk(source, {source}, [], Transform())
        return sorted(found, key=lambda c: (len(c[0]), [s["edge"] for s in c[0]]))

    @staticmethod
    def _has_cycle(edges, source):
        """Does the frame graph component containing `source` have a cycle (more edges than a tree)?"""
        nodes, todo = {source}, [source]
        while todo:
            f = todo.pop()
            for e in edges:
                for a, b in ((e["parent"], e["child"]), (e["child"], e["parent"])):
                    if a == f and b not in nodes:
                        nodes.add(b)
                        todo.append(b)
        inside = [e for e in edges if e["parent"] in nodes and e["child"] in nodes]
        return len(inside) > len(nodes) - 1

    @staticmethod
    def _describe(edges, chain):
        out = []
        for s in chain:
            e = edges[s["edge"]]
            out.append({"parent": e["parent"], "child": e["child"], "direction": s["direction"],
                        "translation": e["transform"].t, "rotation": e["transform"].q, "support": e["support"],
                        "disputed": e["disputed"]})
        return out

    def _resolve(self, edges, source, target):
        """(transform source->target or None, status, chains described, reason, cycle) under plan 9.6's rules."""
        if source == target:
            return Transform(), None, [], None, False
        chains = self._chains(edges, source, target)
        cycle = self._has_cycle(edges, source)
        described = [{"frames": [source] + [edges[s["edge"]]["parent"] if s["direction"] == "forward"
                                            else edges[s["edge"]]["child"] for s in steps],
                      "steps": self._describe(edges, steps), "transform": total} for steps, total in chains]
        if not chains:
            return None, Status.UNKNOWN, [], f"no frame chain from {source} to {target}", cycle
        first = chains[0][1]
        if not all(total.close_to(first) for _, total in chains):
            return first, Status.DISPUTED, described, "chains disagree (ambiguous frame relationships)", cycle
        if any(st["disputed"] for c in described for st in c["steps"]):
            return first, Status.DISPUTED, described, "a transform on the chain is disputed", cycle
        return first, Status.INFERRED, described, None, cycle

    def transform_between(self, world, source, target, t, as_of=None, perspective=SYSTEM):
        """How `source` frame coordinates map into `target` at t: {"status", "transform" (q, t) or None, "chains",
        "reason", "cycle"}. INFERRED from the transforms that hold for the perspective; DISPUTED when chains disagree
        or use a disputed transform; UNKNOWN when no chain exists."""
        edges = self._frame_edges(world, t, as_of, perspective)
        total, status, chains, reason, cycle = self._resolve(edges, source, target)
        return {"source": source, "target": target, "status": status if source != target else Status.INFERRED,
                "transform": total, "chains": chains, "reason": reason, "cycle": cycle, "rule": RULE}

    def where(self, world, thing, frame, t, as_of=None, perspective=SYSTEM):
        """The thing's position in `frame` at t, judged (A2). Every position statement that holds for the perspective
        is a candidate: stated in `frame` (direct), or mapped into it through a frame chain (derived, INFERRED, citing
        the position and every transform). Candidates are compared, never merged: overlapping ranges are compatible,
        disjoint ranges or different orientations conflict (DISPUTED). Statements whose frame has no chain to `frame`
        are listed as incomparable. Returns a dict (status, candidates, conflicts, incomparable, alternatives...)."""
        atts, _ = self._view(world, as_of, perspective, "positioned-in", [thing])
        about = [a for a in atts.values() if self.is_a(a.ctype, "positioned-in") and thing in a.roles.get("positioned", [])]
        alternatives = self._alternatives(about, t, perspective, as_of)
        poses = self.poses(world, thing, t, as_of, perspective)
        edges = self._frame_edges(world, t, as_of, perspective) if any(p["frame"] != frame for p in poses) else []
        candidates, incomparable = [], []
        for p in poses:
            box = {a: p[a] for a in AXES}
            total, status, chains, reason, cycle = self._resolve(edges, p["frame"], frame)
            if total is None:
                incomparable.append({"frame": p["frame"], "support": p["support"], "reason": reason})
                continue
            direct = p["frame"] == frame
            candidates.append({
                **map_box(total, box),
                "orientation": qmul(total.q, p["orientation"]) if p["orientation"] else None,
                "status": p["status"] if direct else status, "stated_in": p["frame"], "stated": box,
                "position_support": p["support"], "direct": direct, "rule": None if direct else RULE,
                "chain": [] if direct else chains[0]["steps"], "chains": len(chains), "cycle": cycle,
                "reason": reason})
        conflicts = sorted((i, j) for i, a in enumerate(candidates) for j, b in enumerate(candidates) if i < j and (
            not boxes_overlap(a, b) or (a["orientation"] and b["orientation"]
                                        and not same_rotation(a["orientation"], b["orientation"]))))
        if conflicts or any(c["status"] == Status.DISPUTED for c in candidates):
            status = Status.DISPUTED
        elif candidates:
            direct = {c["status"] for c in candidates if c["direct"]}
            status = next((s for s in (Status.STIPULATED, Status.ASSERTED, Status.INFERRED) if s in direct),
                          Status.INFERRED)
        elif incomparable:
            status = Status.UNKNOWN
        else:
            status = Status.UNKNOWN if about else Status.NOT_YET_KNOWN
        return {"thing": thing, "frame": frame, "status": status, "candidates": candidates, "conflicts": conflicts,
                "judgement": ("conflicting" if conflicts else "compatible" if len(candidates) > 1 else
                              "single" if candidates else None),
                "incomparable": incomparable, "alternatives": alternatives}

    def frames_linked_in_database(self, world, frame):
        """Frames connected to `frame` by frame-transform records attested in `world`, by the TypeDB function
        frames_linked (records only: time, acceptance and perspective ignored; inspection, like parts_in)."""
        from . import typeql as q
        from .model import READ
        with self.driver.transaction(self.database, READ) as tx:
            return sorted({q.opt(r, "id") for r in q.rows(tx, """match $f isa spatial-frame, has wm-id == $frame;
                $w isa world, has wm-id == $world; let $g in frames_linked($f, $w); $g has wm-id $id;""",
                {"frame": frame, "world": world})} - {frame})

