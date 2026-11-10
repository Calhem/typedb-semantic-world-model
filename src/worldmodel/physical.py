"""Core 0.4 Stage A1 (LABS-1.006): physical structure on top of the v0.2 core. Mixed into WorldModel.

Writing goes through the ordinary attestation path (every fact is an attested proposition with a world, an attester,
a stance and an interval); reading goes through facts_about / value_at, so perspective, knowledge-time, world and
identity semantics are the core's. Nothing here stores answers.

Conventions (Core 0.4 plan 9.6): right-handed frames, metres, radians; unit quaternions (w, x, y, z), Hamilton,
active; a norm more than 1e-9 from 1 is rejected. frame-transform(parent P, child C) gives C's pose in P:
p_P = R(q)·p_C + t. Composing transforms into derived poses is deferred to A2.
"""

import math

from .keys import as_ids

AXES = ("x", "y", "z")
QUAT_TOLERANCE = 1e-9
SYSTEM = "system"


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
