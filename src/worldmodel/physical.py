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
from .spatial import AXES as _AXES, ANGLE_TOLERANCE, Transform, angular_separation, boxes_overlap, map_box, qmul

AXES = _AXES
QUAT_TOLERANCE = 1e-9
SYSTEM = "system"
MAX_EDGE_VISITS = 100_000    # resource limit of one frame-graph search (edge examinations); reaching it is reported
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
    def _search(edges, source, target, limit):
        """Breadth-first search of the frame graph from `source` (each edge usable forward, child -> parent, or
        inverse). No hop limit; each frame is reached once, so cycles terminate. Returns the composed transform from
        `source` to every reached frame (along shortest chains), the predecessor of each, and the search metadata.
        `limit` bounds the number of edge examinations; reaching it marks the search truncated."""
        adj = {}
        for i, e in enumerate(edges):
            adj.setdefault(e["child"], []).append((i, e["parent"], "forward"))
            adj.setdefault(e["parent"], []).append((i, e["child"], "inverse"))
        pot, pred, queue, examined, truncated = {source: Transform()}, {source: None}, [source], 0, False
        while queue and not truncated:
            frame = queue.pop(0)
            for i, nxt, direction in adj.get(frame, ()):
                examined += 1
                if examined > limit:
                    truncated = True
                    break
                if nxt in pot:
                    continue
                step = edges[i]["transform"] if direction == "forward" else edges[i]["transform"].inverse()
                pot[nxt], pred[nxt] = step.then(pot[frame]), (frame, i, direction)
                queue.append(nxt)
        return pot, pred, adj, {"complete": not truncated, "truncated": truncated, "limit": limit,
                                "edges_examined": min(examined, limit), "frames_reached": len(pot),
                                "edges_in_graph": len(edges)}

    @staticmethod
    def _blocks(nodes, adj):
        """Biconnected components (as sets of edge ids) of the multigraph restricted to `nodes`, by an iterative
        Tarjan search. Parallel edges between two frames form one block (a cycle of length 2)."""
        index, low, blocks, estack, counter = {}, {}, [], [], 0
        for root in sorted(nodes):
            if root in index:
                continue
            index[root] = low[root] = counter
            counter += 1
            stack = [(root, None, iter(adj.get(root, ())))]
            while stack:
                v, via, it = stack[-1]
                for eid, w, _ in it:
                    if eid == via or w not in nodes:
                        continue
                    if w not in index:
                        estack.append(eid)
                        index[w] = low[w] = counter
                        counter += 1
                        stack.append((w, eid, iter(adj.get(w, ()))))
                        break
                    if index[w] < index[v]:                      # a back edge (or a parallel edge), once
                        estack.append(eid)
                        low[v] = min(low[v], index[w])
                else:
                    stack.pop()
                    if stack:
                        u = stack[-1][0]
                        low[u] = min(low[u], low[v])
                        if low[v] >= index[u]:
                            block = set()
                            while True:
                                e = estack.pop()
                                block.add(e)
                                if e == via:
                                    break
                            blocks.append(block)
        return blocks

    @staticmethod
    def _relevant_edges(edges, blocks, source, target):
        """The edges that lie on at least one simple chain from source to target: the blocks on the path between
        them in the block-cut tree (a standard property of biconnected components)."""
        members = [{edges[e]["parent"] for e in b} | {edges[e]["child"] for e in b} for b in blocks]
        tree = {}
        for i, vs in enumerate(members):
            for v in vs:
                tree.setdefault(("v", v), []).append(("b", i))
                tree.setdefault(("b", i), []).append(("v", v))
        start, goal = ("v", source), ("v", target)
        back, queue = {start: None}, [start]
        while queue:
            n = queue.pop(0)
            if n == goal:
                break
            for m in tree.get(n, ()):
                if m not in back:
                    back[m] = n
                    queue.append(m)
        relevant, n = set(), goal
        while n is not None and n in back:
            if n[0] == "b":
                relevant |= blocks[n[1]]
            n = back[n]
        return relevant

    @staticmethod
    def _describe(edges, steps):
        out = []
        for frame, i, direction in steps:
            e = edges[i]
            out.append({"parent": e["parent"], "child": e["child"], "direction": direction,
                        "translation": e["transform"].t, "rotation": e["transform"].q, "support": e["support"],
                        "disputed": e["disputed"]})
        return out

    def _resolve(self, edges, source, target, limit=None):
        """Resolve how `source` coordinates map into `target` (plan 9.6, corrected in LABS-1.008).

        Completed search, no chain: UNKNOWN, search complete. Search truncated before reaching the target: UNKNOWN,
        search truncated (never a silent "no chain"). Target reached: the shortest chain gives the transform, and
        every edge on any simple source-target chain is checked against the composed transforms: all simple chains
        agree exactly when every such edge is consistent (within 1e-9 m and the angular tolerance). An inconsistent
        edge makes the answer DISPUTED with no transform chosen; a disputed transform on any such chain likewise.
        A truncated search that reached the target returns the shortest chain's transform as an unverified
        candidate: status UNKNOWN, `verified: False` (LABS-1.009)."""
        limit = MAX_EDGE_VISITS if limit is None else limit
        if source == target:
            return {"transform": Transform(), "status": None, "chain": [], "frames": [source], "reason": None,
                    "search": {"complete": True, "truncated": False, "limit": limit, "edges_examined": 0,
                               "frames_reached": 1, "edges_in_graph": len(edges), "hops": 0, "cycle": False,
                               "relevant_edges": 0, "verified": True, "inconsistent": []}}
        pot, pred, adj, search = self._search(edges, source, target, limit)
        if target not in pot:
            reason = (f"search truncated after {search['edges_examined']} edge examinations (limit {limit}) without "
                      f"reaching {target}" if search["truncated"] else f"no frame chain from {source} to {target}")
            return {"transform": None, "status": Status.UNKNOWN, "chain": [], "frames": [], "reason": reason,
                    "search": {**search, "hops": None, "cycle": None, "relevant_edges": None, "verified": False,
                               "inconsistent": []}}
        steps, n = [], target
        while pred[n] is not None:
            prev, i, direction = pred[n]
            steps.append((prev, i, direction))
            n = prev
        steps.reverse()
        frames = [source] + [edges[i]["parent"] if d == "forward" else edges[i]["child"] for _, i, d in steps]
        chain = self._describe(edges, steps)
        info = {**search, "hops": len(steps), "cycle": None, "relevant_edges": None, "verified": False,
                "inconsistent": []}
        if search["truncated"]:      # a candidate only: not authoritative until every route is checked (LABS-1.009)
            return {"transform": pot[target], "status": Status.UNKNOWN, "chain": chain, "frames": frames,
                    "reason": "verification incomplete: search truncated, other chains were not checked for agreement",
                    "search": info}
        relevant = self._relevant_edges(edges, self._blocks(set(pot), adj), source, target)
        bad = []
        for i in sorted(relevant):
            e = edges[i]
            expected = e["transform"].then(pot[e["child"]])            # source -> child -> parent
            if not expected.close_to(pot[e["parent"]]):
                dt, da = expected.gap(pot[e["parent"]])
                bad.append({"parent": e["parent"], "child": e["child"], "support": e["support"],
                            "translation_gap_m": dt, "angle_gap_rad": da})
        info.update({"cycle": len(relevant) > len(steps), "relevant_edges": len(relevant), "verified": True,
                     "inconsistent": bad})
        if bad:
            return {"transform": None, "status": Status.DISPUTED, "chain": chain, "frames": frames,
                    "reason": "chains disagree (ambiguous frame relationships)", "search": info}
        if any(edges[i]["disputed"] for i in relevant):
            return {"transform": None, "status": Status.DISPUTED, "chain": chain, "frames": frames,
                    "reason": "a transform on a chain is disputed", "search": info}
        return {"transform": pot[target], "status": Status.INFERRED, "chain": chain, "frames": frames, "reason": None,
                "search": info}

    def transform_between(self, world, source, target, t, as_of=None, perspective=SYSTEM, limit=None):
        """How `source` frame coordinates map into `target` at t: {"status", "transform" (q, t) or None, "chain" (the
        shortest chain, each step with its direction and supporting attestations), "frames", "reason", "search"}.
        INFERRED from the transforms that hold for the perspective; DISPUTED when chains disagree or use a disputed
        transform (no transform is chosen); UNKNOWN when no chain exists or the search was truncated (see `search`;
        a truncated search that reached the target returns its transform as an unverified candidate)."""
        edges = self._frame_edges(world, t, as_of, perspective)
        r = self._resolve(edges, source, target, limit)
        return {"source": source, "target": target, "status": r["status"] or Status.INFERRED, "rule": RULE, **r}

    def where(self, world, thing, frame, t, as_of=None, perspective=SYSTEM, angle_tolerance=ANGLE_TOLERANCE,
              limit=None):
        """The thing's position in `frame` at t, judged (A2, LABS-1.008). Every position statement that holds for the
        perspective is a candidate: stated in `frame` (direct), or mapped into it through the shortest frame chain
        (derived, INFERRED, citing the position and every transform). Candidates are compared, never merged:
        overlapping ranges can both be true (compatible), disjoint ranges conflict, and orientations conflict when
        their angular separation exceeds `angle_tolerance` (policy, default 1e-9 rad). A statement whose frame cannot
        be related to `frame` is listed as incomparable, with the search metadata saying whether the search completed
        or was truncated. Where chains disagree, the candidate has no position (none is chosen) and is DISPUTED."""
        atts, _ = self._view(world, as_of, perspective, "positioned-in", [thing])
        about = [a for a in atts.values() if self.is_a(a.ctype, "positioned-in") and thing in a.roles.get("positioned", [])]
        alternatives = self._alternatives(about, t, perspective, as_of)
        poses = self.poses(world, thing, t, as_of, perspective)
        edges = self._frame_edges(world, t, as_of, perspective) if any(p["frame"] != frame for p in poses) else []
        candidates, incomparable = [], []
        for p in poses:
            box = {a: p[a] for a in AXES}
            r = self._resolve(edges, p["frame"], frame, limit)
            if r["transform"] is None and r["status"] == Status.UNKNOWN:
                incomparable.append({"frame": p["frame"], "support": p["support"], "reason": r["reason"],
                                     "search": r["search"]})
                continue
            direct, total = p["frame"] == frame, r["transform"]
            mapped = map_box(total, box) if total is not None else {a: None for a in AXES}
            candidates.append({
                **mapped,
                "orientation": qmul(total.q, p["orientation"]) if p["orientation"] and total is not None else
                (p["orientation"] if direct else None),
                "status": p["status"] if direct else r["status"], "stated_in": p["frame"], "stated": box,
                "orientation_stated": p["orientation"], "position_support": p["support"], "direct": direct,
                "rule": None if direct else RULE, "chain": r["chain"], "reason": r["reason"], "search": r["search"],
                "verified": r["search"]["verified"]})
        details = []
        for i, a in enumerate(candidates):
            for j, b in enumerate(candidates):
                if i >= j or a["x"] is None or b["x"] is None:
                    continue
                unverified = not (a["verified"] and b["verified"])
                if not boxes_overlap(a, b):
                    details.append({"pair": (i, j), "kind": "disjoint ranges", "unverified": unverified})
                elif a["orientation"] and b["orientation"]:
                    sep = angular_separation(a["orientation"], b["orientation"])
                    if sep > angle_tolerance:
                        details.append({"pair": (i, j), "kind": "orientations differ", "separation_rad": sep,
                                        "tolerance_rad": angle_tolerance, "unverified": unverified})
        # Only verified candidates decide (LABS-1.009): an unverified one (truncated search) can neither create a
        # conflict nor support an authoritative answer; it keeps the whole answer UNKNOWN unless a verified conflict.
        conflicts = [d["pair"] for d in details if not d["unverified"]]
        verified = all(c["verified"] for c in candidates) and not any(i["search"]["truncated"] for i in incomparable)
        reason = None if verified else "verification incomplete: a frame search was truncated by its resource limit"
        if conflicts or any(c["status"] == Status.DISPUTED and c["verified"] for c in candidates):
            status = Status.DISPUTED
        elif not verified:
            status = Status.UNKNOWN
        elif candidates:
            direct = {c["status"] for c in candidates if c["direct"]}
            status = next((s for s in (Status.STIPULATED, Status.ASSERTED, Status.INFERRED) if s in direct),
                          Status.INFERRED)
        else:
            status = Status.UNKNOWN if about else Status.NOT_YET_KNOWN
        return {"thing": thing, "frame": frame, "status": status, "candidates": candidates, "conflicts": conflicts,
                "conflict_details": details, "angle_tolerance": angle_tolerance, "verified": verified, "reason": reason,
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

