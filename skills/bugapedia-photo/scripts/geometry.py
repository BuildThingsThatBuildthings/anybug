"""Original parametric surfaces. Coordinates are in millimetres, with Y up."""
from math import sin, cos, pi, sqrt


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def unit(v):
    length = sqrt(sum(x*x for x in v))
    if length < 1e-10:
        raise ValueError("Degenerate direction in shape or rotation")
    return [x / length for x in v]


def stitch(rings):
    """Each adjacent pair forms a closed band. Single-vertex rings are end caps."""
    vertices, triangles, previous = [], [], []
    for ring in rings:
        current = list(range(len(vertices), len(vertices) + len(ring)))
        vertices.extend(ring)
        if previous:
            for i in range(max(len(current), len(previous))):
                a, b = previous[i % len(previous)], previous[(i+1) % len(previous)]
                c, d = current[i % len(current)], current[(i+1) % len(current)]
                if a != b:
                    triangles.append([a, b, c])
                if c != d:
                    triangles.append([b, d, c])
        previous = current
    return vertices, triangles


def ellipsoid(shape):
    center, radii = shape["center"], shape["radii"]
    if min(radii) <= 0:
        raise ValueError("Ellipsoid radii must be positive")
    def point(lat, lon):
        direction = [cos(lat)*cos(lon), sin(lat), -cos(lat)*sin(lon)]
        return [x+s*v for x, s, v in zip(center, radii, direction)]
    rings = [[point(-pi/2, 0)]]
    for j in range(1, 14):
        rings.append([point(-pi/2+pi*j/14, 2*pi*i/24) for i in range(24)])
    rings.append([point(pi/2, 0)])
    return stitch(rings)


def tube(shape):
    points, radii = shape["points"], shape["radii"]
    if len(points) < 2 or len(points) != len(radii) or min(radii) <= 0:
        raise ValueError("A tube needs a positive radius at every path vertex")
    rings, prior = [[points[0]]], None
    for j, (p, radius) in enumerate(zip(points, radii)):
        tangent = unit(sub(points[min(j+1, len(points)-1)], points[max(0,j-1)]))
        # Parallel transport the previous rim axis to avoid twists at elbows.
        ref = prior or min(([1,0,0],[0,1,0],[0,0,1]), key=lambda a: abs(sum(x*y for x,y in zip(a,tangent))))
        axis_b = unit(cross(tangent, ref))
        axis_a = unit(cross(axis_b, tangent))
        prior = axis_a
        ring = []
        for i in range(12):
            angle = 2*pi*i/12
            ring.append([v + radius*(a*cos(angle)+b*sin(angle)) for v,a,b in zip(p,axis_a,axis_b)])
        rings.append(ring)
    rings.append([points[-1]])
    return stitch(rings)


def surface(shape, pivot):
    kind = shape["kind"]
    if kind == "mesh":
        vertices, faces = shape["vertices"], shape["faces"]
    elif kind == "ellipsoid":
        vertices, faces = ellipsoid(shape)
    elif kind == "tube":
        vertices, faces = tube(shape)
    elif kind == "loft":
        rings = shape["rings"]
        if len(rings) < 2 or len({len(r) for r in rings}) != 1 or len(rings[0]) < 3:
            raise ValueError("Loft needs at least two equal polygon rings")
        center = lambda r: [sum(axis)/len(r) for axis in zip(*r)]
        vertices, faces = stitch([[center(rings[0])], *rings, [center(rings[-1])]])
    else:
        raise ValueError("Unknown geometry " + kind)
    if not vertices or not faces or any(len(p) != 3 for p in vertices):
        raise ValueError("Invalid mesh")
    normals = [[0.,0.,0.] for _ in vertices]
    for f in faces:
        if len(f) != 3 or any(type(i) is not int or not 0 <= i < len(vertices) for i in f):
            raise ValueError("Invalid triangle")
        a,b,c = [vertices[i] for i in f]
        normal = cross(sub(b,a),sub(c,a))
        for i in f:
            normals[i] = [x+y for x,y in zip(normals[i],normal)]
    return [sub(v,pivot) for v in vertices], [unit(n) for n in normals], faces
