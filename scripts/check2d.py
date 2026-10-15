"""Layer-by-layer swept clearance check of the v2 design (shapely)."""
import math, sys, itertools
from shapely.geometry import Point, Polygon, MultiPoint
from shapely.ops import unary_union
from shapely import affinity
from design import *
import parts as P

QS = 64


def shp(s):
    k = s[0]
    if k == 'circle':
        return Point(s[1]).buffer(s[2], quad_segs=QS) if s[2] > 0 else Point(s[1])
    if k == 'hull':
        return unary_union([Point(c).buffer(r, quad_segs=QS) if r > 0 else Point(c) for c, r in s[1]]).convex_hull
    if k == 'poly':
        return Polygon(s[1])
    if k == 'rect':
        _, y0, z0, y1, z1 = s
        return Polygon([(y0, z0), (y1, z0), (y1, z1), (y0, z1)])
    if k == 'wedge':
        _, c, r, a0, a1 = s
        n = max(8, int(abs(a1 - a0) / math.radians(1)))
        pts = [c] + [(c[0] + r * math.cos(a0 + (a1 - a0) * i / n), c[1] + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
        return Polygon(pts)
    if k == 'kidney':
        _, c, R, a0, a1, hw = s
        n = max(8, int(abs(a1 - a0) / math.radians(1)))
        outer = [(c[0] + (R + hw) * math.cos(a0 + (a1 - a0) * i / n), c[1] + (R + hw) * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
        inner = [(c[0] + (R - hw) * math.cos(a1 - (a1 - a0) * i / n), c[1] + (R - hw) * math.sin(a1 - (a1 - a0) * i / n)) for i in range(n + 1)]
        e0 = Point(c[0] + R * math.cos(a0), c[1] + R * math.sin(a0)).buffer(hw, quad_segs=QS)
        e1 = Point(c[0] + R * math.cos(a1), c[1] + R * math.sin(a1)).buffer(hw, quad_segs=QS)
        return unary_union([Polygon(outer + inner), e0, e1])
    if k == 'gear':
        return Polygon(gear_outline(s[1]))
    if k == 'hex':
        _, c, af, ang = s
        R = af / math.sqrt(3)
        return Polygon([(c[0] + R * math.cos(ang + math.pi / 6 + i * math.pi / 3), c[1] + R * math.sin(ang + math.pi / 6 + i * math.pi / 3)) for i in range(6)])
    raise ValueError(k)


def mirror_feats(feats):
    out = []
    for x0, x1, op, s in feats:
        out.append((-x1, -x0, op, ('__mir', s)))
    return out


def geom(s):
    if s[0] == '__mir':
        return affinity.scale(geom(s[1]), xfact=-1, yfact=1, origin=(0, 0))
    return shp(s)


def instances():
    """[(name, side, group, feats)] with right twins mirrored."""
    out = []
    for name, p in list(P.PARTS.items()) + list(P.HW.items()):
        g = p['group']
        if p.get('mirror'):
            out.append((name, 'R', g, mirror_feats(p['feats'])))
            continue
        if p.get('twin'):
            out.append((name, 'L', g if g == 'static' else g + '_L', p['feats']))
            out.append((name, 'R', g if g == 'static' else g + '_R', mirror_feats(p['feats'])))
        else:
            out.append((name, '', g, p['feats']))
    return out


def transform(g, group, q):
    side = group[-2:] if group.endswith(('_L', '_R')) else ''
    base = group[:-2] if side else group
    mir = side == '_R'

    def m(pt):
        return (-pt[0], pt[1]) if mir else pt
    if base == 'static':
        return g
    if base in ('OK',):
        o = m(O)
        return affinity.rotate(g, (q if mir else -q), origin=o, use_radians=True)
    if base == 'IK':
        return affinity.rotate(g, (q if mir else -q), origin=m(I), use_radians=True)
    if base == 'IF':
        d = sub(p1_at(q), P1)
        return affinity.translate(g, -d[0] if mir else d[0], d[1])
    if base == 'crank':
        return affinity.rotate(g, crank_angle(q) - crank_angle(0), origin=S, use_radians=True)
    if base == 'rod':
        c0, k0, c1, k1 = c_at(0), K0, c_at(q), k_at(q)
        a = math.atan2(k1[1] - c1[1], k1[0] - c1[0]) - math.atan2(k0[1] - c0[1], k0[0] - c0[0])
        g2 = affinity.rotate(g, a, origin=c0, use_radians=True)
        return affinity.translate(g2, c1[0] - c0[0], c1[1] - c0[1])
    if base == 'rodK':
        d = sub(k_at(q), K0)
        return affinity.translate(g, d[0], d[1])
    if base == 'rodC':
        d = sub(c_at(q), c_at(0))
        return affinity.translate(g, d[0], d[1])
    raise ValueError(group)


GROUP_FIX = {'OK_L': 'OK_L', 'OK_R': 'OK_R'}


def slabs(feats):
    xs = set()
    for x0, x1, _, _ in feats:
        xs.update((round(x0, 4), round(x1, 4)))
    return sorted(xs)


def shape_in_slab(feats, xa, xb, cache):
    xm = (xa + xb) / 2
    g = None
    for i, (x0, x1, op, s) in enumerate(feats):
        if not (x0 < xm < x1):
            continue
        if i not in cache:
            cache[i] = geom(s)
        gg = cache[i]
        if op == 'add':
            g = gg if g is None else g.union(gg)
        elif g is not None:
            g = g.difference(gg)
    return g


def build_layers(inst):
    out = []
    for name, side, group, feats in inst:
        cache = {}
        xs = slabs(feats)
        layers = []
        for xa, xb in zip(xs, xs[1:]):
            g = shape_in_slab(feats, xa, xb, cache)
            if g is not None and not g.is_empty:
                layers.append((xa, xb, g))
        out.append((f'{name}{"_" + side if side else ""}', group, layers))
    return out


def check(qs, tol=0.02, verbose=True, skip=()):
    inst = [i for i in instances() if i[0] not in skip]
    L = build_layers(inst)
    worst = {}
    for q in qs:
        posed = [(n, g, [(a, b, transform(s, g, q)) for a, b, s in lay]) for n, g, lay in L]
        for (n1, g1, l1), (n2, g2, l2) in itertools.combinations(posed, 2):
            if g1 == g2 and g1 != 'static':
                continue  # same rigid group: assembled together, checked separately
            if g1 == 'static' and g2 == 'static':
                pass
            for a1, b1, s1 in l1:
                for a2, b2, s2 in l2:
                    lo, hi = max(a1, a2), min(b1, b2)
                    if hi - lo <= 1e-6:
                        continue
                    if not s1.bounds or not s2.bounds:
                        continue
                    ar = s1.intersection(s2).area
                    if ar > tol:
                        key = (n1, n2)
                        if key not in worst or ar > worst[key][0]:
                            worst[key] = (ar, q, lo, hi, s1.intersection(s2).bounds)
    if verbose:
        for (n1, n2), (ar, q, lo, hi, bb) in sorted(worst.items(), key=lambda kv: -kv[1][0]):
            print(f'{n1:22s} x {n2:22s} area {ar:8.3f} mm2 at q={q:6.3f} x[{lo:.2f},{hi:.2f}] bbox {tuple(round(v,1) for v in bb)}')
    return worst


def same_group_check():
    """Rigid groups assembled from several parts (e.g. outer knuckle + outer finger): check at q=0."""
    inst = instances()
    L = build_layers(inst)
    groups = {}
    for n, g, lay in L:
        groups.setdefault(g, []).append((n, lay))
    for g, members in groups.items():
        if g == 'static' or len(members) < 2:
            continue
        for (n1, l1), (n2, l2) in itertools.combinations(members, 2):
            for a1, b1, s1 in l1:
                for a2, b2, s2 in l2:
                    if min(b1, b2) - max(a1, a2) > 1e-6:
                        ar = s1.intersection(s2).area
                        if ar > 0.02:
                            print(f'[rigid {g}] {n1} x {n2} area {ar:.3f} x[{max(a1,a2):.2f},{min(b1,b2):.2f}]')


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    qs = [Q_OPEN_STOP + (Q_CLOSE_STOP - Q_OPEN_STOP) * i / (n - 1) for i in range(n)]
    same_group_check()
    w = check(qs)
    print('pairs with interference:', len(w))
