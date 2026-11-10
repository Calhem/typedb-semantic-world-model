"""Rigid transforms and range propagation for Core 0.4 Stage A2 (LABS-1.007). Pure functions; no database access.

Conventions (Core 0.4 plan 9.6, unchanged):
- right-handed Cartesian frames; lengths in metres; angles in radians;
- rotations are unit quaternions q = (w, x, y, z), Hamilton product, active rotation: v' = q v q*;
- a Transform (q, t) held by frame-transform(parent P, child C) maps a point expressed in C to P: p_P = R(q) p_C + t;
- composition: T_AC = T_AB ∘ T_BC, i.e. R_AC = R_AB R_BC and t_AC = R_AB t_BC + t_AB;
- inverse: T_CP = (q*, -R(q*) t), computed, never stored;
- an axis-aligned range box is mapped by transforming its 8 corners and taking their bounding box (conservative:
  the result contains every point of the original box; it may contain more when the rotation is not axis-aligned);
- rotations are treated as exact; positions agree within TOLERANCE metres.
"""

import math
from dataclasses import dataclass
from itertools import product

TOLERANCE = 1e-9              # metres, and for quaternion comparison (1 - |q1·q2|)
AXES = ("x", "y", "z")


def qmul(a, b):
    """Hamilton product a b."""
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw)


def qconj(q):
    w, x, y, z = q
    return (w, -x, -y, -z)


def rotate(q, v):
    """R(q) v for a unit quaternion q (active rotation)."""
    w, x, y, z = qmul(qmul(q, (0.0, *v)), qconj(q))
    return (x, y, z)


def same_rotation(a, b):
    """q and -q are the same rotation."""
    return 1.0 - abs(sum(i * j for i, j in zip(a, b))) <= TOLERANCE


@dataclass(frozen=True)
class Transform:
    """Maps points from a child frame into a parent frame: p_parent = R(q) p_child + t."""
    q: tuple = (1.0, 0.0, 0.0, 0.0)
    t: tuple = (0.0, 0.0, 0.0)

    def apply(self, p):
        return tuple(r + s for r, s in zip(rotate(self.q, p), self.t))

    def then(self, inner):
        """self ∘ inner: first map by `inner` (child of child -> child), then by self (child -> parent)."""
        return Transform(qmul(self.q, inner.q), tuple(r + s for r, s in zip(rotate(self.q, inner.t), self.t)))

    def inverse(self):
        qi = qconj(self.q)
        return Transform(qi, tuple(-c for c in rotate(qi, self.t)))

    def close_to(self, other):
        return same_rotation(self.q, other.q) and all(abs(a - b) <= TOLERANCE for a, b in zip(self.t, other.t))


IDENTITY = Transform()


def map_box(transform, box):
    """Map an axis-aligned box {axis: (lower, upper)} through `transform`; returns the bounding box of the 8 mapped
    corners (conservative)."""
    corners = [transform.apply(c) for c in product(*(box[a] for a in AXES))]
    return {a: (min(c[i] for c in corners), max(c[i] for c in corners)) for i, a in enumerate(AXES)}


def boxes_overlap(a, b, tol=TOLERANCE):
    """Closed ranges on every axis intersect (within tolerance): the two position statements can both be true."""
    return all(a[ax][0] <= b[ax][1] + tol and b[ax][0] <= a[ax][1] + tol for ax in AXES)


def boxes_equal(a, b, tol=TOLERANCE):
    return all(abs(a[ax][0] - b[ax][0]) <= tol and abs(a[ax][1] - b[ax][1]) <= tol for ax in AXES)


def params_compatible(a, b, tol=TOLERANCE):
    """Can two contents' numeric parameters both be true? `*-min`/`*-max` pairs are ranges (compatible when they
    overlap); quaternions (qw..qz) are rotations (equal up to sign); other numbers (tx...) must be equal within
    tolerance. A parameter present on one side only constrains nothing."""
    a, b = dict(a), dict(b)
    for name in {n[:-4] for n in a if n.endswith("-min")} & {n[:-4] for n in b if n.endswith("-min")}:
        if not (a[f"{name}-min"] <= b[f"{name}-max"] + tol and b[f"{name}-min"] <= a[f"{name}-max"] + tol):
            return False
    quat = ("qw", "qx", "qy", "qz")
    if all(k in a and k in b for k in quat) and not same_rotation(tuple(a[k] for k in quat), tuple(b[k] for k in quat)):
        return False
    rest = (set(a) & set(b)) - set(quat) - {n for n in a if n.endswith(("-min", "-max"))}
    return all(abs(a[k] - b[k]) <= tol for k in rest)


def angle_about_z(q):
    """The rotation angle about +z for a level rotation (for readable output only)."""
    w, x, y, z = q
    return 2 * math.atan2(z, w)
