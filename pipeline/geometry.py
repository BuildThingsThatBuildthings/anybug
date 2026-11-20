"""Small Blender authoring helpers. Species builders specify dimensions in millimetres."""

import math
import bpy
from mathutils import Vector


def linear(channel):
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def material(name, hex_color, roughness=0.45, metallic=0):
    value = hex_color.strip("#")
    rgba = tuple(linear(int(value[i : i + 2], 16) / 255) for i in (0, 2, 4)) + (1,)
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = rgba
    mat.use_nodes = True
    bs = mat.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = rgba
    bs.inputs["Roughness"].default_value = roughness
    bs.inputs["Metallic"].default_value = metallic
    return mat


def group(name, parent=None, origin=(0, 0, 0)):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.location = origin
    obj.empty_display_size = 0.12
    return obj


def mesh(name, parent, vertices, faces, mat, smooth=True):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(mat)
    for face in data.polygons:
        face.use_smooth = smooth
    return obj


def oval(name, parent, center, scale, mat, segments=24, rings=14):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings)
    obj = bpy.context.object
    obj.name = name
    obj.parent = parent
    obj.location = center
    obj.scale = scale
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def tube(name, parent, points, radii, mat, sides=8):
    """Parallel-transport rings around a tapered centre line."""
    pts = [Vector(p) for p in points]
    if isinstance(radii, (int, float)):
        radii = [radii] * len(pts)
    vertices, faces = [], []
    normal = None
    for i, point in enumerate(pts):
        tangent = (pts[min(i + 1, len(pts) - 1)] - pts[max(0, i - 1)]).normalized()
        if normal is None:
            normal = tangent.orthogonal().normalized()
        normal = (normal - tangent * normal.dot(tangent)).normalized()
        binormal = tangent.cross(normal)
        for j in range(sides):
            angle = 2 * math.pi * j / sides
            vertices.append(
                tuple(
                    point
                    + radii[i] * (normal * math.cos(angle) + binormal * math.sin(angle))
                )
            )
            if i:
                a = (i - 1) * sides + j
                b = (i - 1) * sides + (j + 1) % sides
                faces.append((a, b, b + sides, a + sides))
    faces.extend(
        [
            tuple(reversed(range(sides))),
            tuple(range(len(vertices) - sides, len(vertices))),
        ]
    )
    return mesh(name, parent, vertices, faces, mat)


def smooth_path(name, parent, points, radius, mat, sides=8):
    """Catmull-Rom interpolation through anatomical landmarks."""
    pts = [Vector(p) for p in points]
    samples = []
    for i in range(len(pts) - 1):
        a, b, c, d = (
            pts[max(0, i - 1)],
            pts[i],
            pts[i + 1],
            pts[min(i + 2, len(pts) - 1)],
        )
        for j in range(7):
            t = j / 7
            samples.append(
                0.5
                * (
                    2 * b
                    + (-a + c) * t
                    + (2 * a - 5 * b + 4 * c - d) * t * t
                    + (-a + 3 * b - 3 * c + d) * t * t * t
                )
            )
    return tube(name, parent, [*samples, pts[-1]], radius, mat, sides)
