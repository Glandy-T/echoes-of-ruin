"""Global UV2 coverage/overlap audit, shared by versioned Room1 bakes."""
import math
UV_EPSILON=1.0e-8

def positive_polygon_area(points):
    return abs(sum(points[i][0] * points[(i + 1) % len(points)][1] -
                   points[(i + 1) % len(points)][0] * points[i][1]
                   for i in range(len(points))) * 0.5) if points else 0.0


def cross(a, b, c):
    return ((b[0] - a[0]) * (c[1] - a[1]) -
            (b[1] - a[1]) * (c[0] - a[0]))


def segment_line_intersection(start, end, clip_a, clip_b):
    # Infinite-line intersection; caller only uses it after opposite signs.
    edge_x = end[0] - start[0]
    edge_y = end[1] - start[1]
    clip_x = clip_b[0] - clip_a[0]
    clip_y = clip_b[1] - clip_a[1]
    denominator = edge_x * clip_y - edge_y * clip_x
    if abs(denominator) <= UV_EPSILON:
        return end
    t = ((clip_a[0] - start[0]) * clip_y -
         (clip_a[1] - start[1]) * clip_x) / denominator
    return (start[0] + t * edge_x, start[1] + t * edge_y)


def triangle_overlap_area(subject, clip):
    """Positive-area overlap only; a shared edge/corner is deliberately zero."""
    orientation = 1.0 if cross(clip[0], clip[1], clip[2]) >= 0.0 else -1.0
    polygon = list(subject)
    for edge_index in range(3):
        if not polygon:
            return 0.0
        clip_a = clip[edge_index]
        clip_b = clip[(edge_index + 1) % 3]
        input_polygon = polygon
        polygon = []
        previous = input_polygon[-1]
        previous_inside = orientation * cross(clip_a, clip_b, previous) >= -UV_EPSILON
        for current in input_polygon:
            current_inside = orientation * cross(clip_a, clip_b, current) >= -UV_EPSILON
            if current_inside != previous_inside:
                polygon.append(segment_line_intersection(previous, current, clip_a, clip_b))
            if current_inside:
                polygon.append(current)
            previous = current
            previous_inside = current_inside
    return positive_polygon_area(polygon)


def collect_uv_triangles(receivers):
    triangles = []
    geometry_non_degenerate = 0
    uv_non_degenerate = 0
    uv_degenerate = 0
    out_of_atlas_vertices = []
    for obj in receivers:
        layer = obj.data.uv_layers.get('LightmapUV')
        if layer is None:
            raise RuntimeError('%s missing LightmapUV' % obj.name)
        for polygon in obj.data.polygons:
            loops = list(polygon.loop_indices)
            for index in range(1, len(loops) - 1):
                vertex_indices = (loops[0], loops[index], loops[index + 1])
                points = []
                for loop_index in vertex_indices:
                    uv = layer.data[loop_index].uv
                    points.append((float(uv.x), float(uv.y)))
                    if (uv.x < -UV_EPSILON or uv.y < -UV_EPSILON or
                            uv.x > 1.0 + UV_EPSILON or uv.y > 1.0 + UV_EPSILON):
                        if len(out_of_atlas_vertices) < 100:
                            out_of_atlas_vertices.append({
                                'object': obj.name, 'polygon': polygon.index,
                                'uv': [float(uv.x), float(uv.y)],
                            })
                vertices = [obj.data.vertices[obj.data.loops[loop_index].vertex_index].co
                            for loop_index in vertex_indices]
                geometric_area = (vertices[1] - vertices[0]).cross(vertices[2] - vertices[0]).length * 0.5
                if geometric_area <= UV_EPSILON:
                    continue
                geometry_non_degenerate += 1
                area = positive_polygon_area(points)
                if area <= 1.0e-12:
                    uv_degenerate += 1
                    continue
                uv_non_degenerate += 1
                triangles.append({
                    'object': obj.name,
                    'polygon': polygon.index,
                    'points': points,
                    'bbox': (min(point[0] for point in points), min(point[1] for point in points),
                             max(point[0] for point in points), max(point[1] for point in points)),
                })
    return triangles, {
        'geometry_non_degenerate_triangle_count': geometry_non_degenerate,
        'uv_non_degenerate_triangle_count': uv_non_degenerate,
        'uv_degenerate_triangle_count': uv_degenerate,
        'out_of_atlas_vertex_count': len(out_of_atlas_vertices),
        'out_of_atlas_vertices': out_of_atlas_vertices,
    }


def audit_uv2_layout(receivers):
    """Audit all receiver triangles, not merely the previously affected wall."""
    triangles, coverage = collect_uv_triangles(receivers)
    cells = {}
    grid_size = 64
    for index, triangle in enumerate(triangles):
        min_x, min_y, max_x, max_y = triangle['bbox']
        # Clamp exactly-atlas-edge coordinates into the final valid cell.
        x0 = max(0, min(grid_size - 1, int(math.floor(min_x * grid_size))))
        y0 = max(0, min(grid_size - 1, int(math.floor(min_y * grid_size))))
        x1 = max(0, min(grid_size - 1, int(math.floor(max_x * grid_size))))
        y1 = max(0, min(grid_size - 1, int(math.floor(max_y * grid_size))))
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                cells.setdefault((x, y), []).append(index)
    pairs = set()
    for contents in cells.values():
        for left_index in range(len(contents)):
            for right_index in range(left_index + 1, len(contents)):
                a, b = contents[left_index], contents[right_index]
                pairs.add((a, b) if a < b else (b, a))
    overlaps = []
    for a, b in pairs:
        first, second = triangles[a], triangles[b]
        a0, b0, a1, b1 = first['bbox']
        c0, d0, c1, d1 = second['bbox']
        # Strict AABB overlap makes touching bounds an accepted non-overlap.
        if max(a0, c0) >= min(a1, c1) - UV_EPSILON or max(b0, d0) >= min(b1, d1) - UV_EPSILON:
            continue
        area = triangle_overlap_area(first['points'], second['points'])
        if area > UV_EPSILON:
            overlaps.append({
                'a': {'object': first['object'], 'polygon': first['polygon']},
                'b': {'object': second['object'], 'polygon': second['polygon']},
                'uv_overlap_area': area,
            })
            if len(overlaps) >= 100:
                break
    return {
        'receiver_triangle_count': len(triangles),
        'candidate_triangle_pairs': len(pairs),
        'positive_area_overlap_count': len(overlaps),
        'positive_area_overlaps': overlaps,
        **coverage,
    }
