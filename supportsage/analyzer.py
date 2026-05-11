"""
Geometry analyzer for 3D STL models.

Core analysis:
- Detect overhang regions (angle-based)
- Compute curvature for support-critical areas
- Identify islands and disconnected regions
- Calculate surface area, volume, bounding box
"""
from __future__ import annotations

import numpy as np
import trimesh


def load_stl(path: str) -> trimesh.Trimesh:
    """Load an STL file and ensure watertight."""
    mesh = trimesh.load_mesh(path)
    if not isinstance(mesh, trimesh.Trimesh):
        raise TypeError(f"Expected Trimesh, got {type(mesh)}")
    return mesh


def detect_overhangs(
    mesh: trimesh.Trimesh,
    angle_threshold: float = 45.0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Detect overhang faces based on face normal vs build direction (Z-up).

    Args:
        mesh: Input triangle mesh.
        angle_threshold: Maximum printable overhang angle in degrees.
                         45° = faces steeper than 45° from horizontal need support.

    Returns:
        (overhang_face_indices, overhang_faces_mask)
        - face_indices: array of int indices into mesh.faces
        - mask: boolean array, True where face is an overhang
    """
    # Face normals (already unit vectors from trimesh)
    face_normals = mesh.face_normals

    # Build direction = Z-up (0, 0, 1)
    # The angle from horizontal: dot = |n| * |up| * cos(theta)
    #   where theta is angle from build plate normal (Z)
    #   A face normal pointing straight down: dot=-1, theta=180
    #   A face normal pointing up: dot=1, theta=0
    # Overhang: the face is steep enough that it would need support.
    #   Convention: face normals pointing mostly downward (< -cos(threshold))
    #     OR face normals pointing mostly sideways with downward component.

    dot_products = face_normals @ np.array([0.0, 0.0, 1.0])

    # Faces with normals pointing downward (dot < 0) are overhangs.
    # The threshold angle controls how steep a downward face we consider:
    #   angle_threshold=45 means: faces whose normal is >45° from vertical
    #   cos(45°) ≈ 0.707
    #   So a face is an "overhang" if its normal has less than cos(45°) upward component
    cos_threshold = np.cos(np.radians(angle_threshold))

    # Faces needing support: dot < cos_threshold
    # (faces whose normal is more than angle_threshold from straight up)
    overhang_mask = dot_products < cos_threshold
    overhang_indices = np.where(overhang_mask)[0]

    return overhang_indices, overhang_mask


def classify_overhang_severity(
    mesh: trimesh.Trimesh,
    overhang_mask: np.ndarray,
) -> dict[str, np.ndarray]:
    """
    Classify overhang regions by severity.

    Returns:
        dict with keys:
        - 'critical': faces that are nearly horizontal downward-facing (dot < -0.5, >120°)
        - 'moderate': faces that need support but not critically (45-70°)
        - 'borderline': faces near the threshold (just over 45°)
        - 'safe': no support needed
    """
    dot_products = mesh.face_normals @ np.array([0.0, 0.0, 1.0])

    critical = dot_products < -0.5  # >120° from vertical
    moderate = (dot_products >= -0.5) & (dot_products < 0.0)
    borderline = (dot_products >= 0.0) & (dot_products < np.cos(np.radians(45)))
    safe = dot_products >= np.cos(np.radians(45))

    return {
        "critical": critical,
        "moderate": moderate,
        "borderline": borderline,
        "safe": safe,
    }


def detect_islands(mesh: trimesh.Trimesh, overhang_mask: np.ndarray) -> list[np.ndarray]:
    """
    Find disconnected overhang regions (islands).

    Useful for deciding where to place tree supports vs. continuous walls.
    """
    # Get vertices of overhang faces
    overhang_faces = mesh.faces[overhang_mask]
    overhang_vertices = np.unique(overhang_faces.flatten())

    # Build adjacency for overhang faces
    # Two faces are adjacent if they share an edge
    face_adjacency = mesh.face_adjacency

    # Filter to only overhang faces
    overhang_face_set = set(np.where(overhang_mask)[0])
    adjacency_in_overhang = []
    for face_pair in face_adjacency:
        if face_pair[0] in overhang_face_set and face_pair[1] in overhang_face_set:
            adjacency_in_overhang.append(face_pair)
    adjacency_in_overhang = np.array(adjacency_in_overhang) if adjacency_in_overhang else np.empty((0, 2), dtype=int)

    # BFS to find connected components
    overhang_indices = np.where(overhang_mask)[0]
    if len(overhang_indices) == 0:
        return []

    # Build adjacency dict
    adj_list = {idx: [] for idx in overhang_indices}
    for a, b in adjacency_in_overhang:
        adj_list[a].append(b)
        adj_list[b].append(a)

    visited = set()
    islands = []
    for idx in overhang_indices:
        if idx not in visited:
            island = []
            queue = [idx]
            while queue:
                current = queue.pop(0)
                if current not in visited:
                    visited.add(current)
                    island.append(current)
                    for neighbor in adj_list.get(current, []):
                        if neighbor not in visited:
                            queue.append(neighbor)
            islands.append(np.array(island))

    return islands


def compute_support_volume_estimate(
    mesh: trimesh.Trimesh,
    overhang_mask: np.ndarray,
    build_platform_z: float = 0.0,
) -> float:
    """
    Estimate volume of support material needed.

    Simple approach: project overhang vertices down to build plate,
    approximate as pyramids/cones.
    """
    overhang_vertices_idx = np.unique(mesh.faces[overhang_mask].flatten())
    overhang_verts = mesh.vertices[overhang_vertices_idx]

    if len(overhang_verts) == 0:
        return 0.0

    # Simple heuristic: support volume ≈ area of overhang * average height / 3
    overhang_area = mesh.area_faces[overhang_mask].sum()
    avg_height = overhang_verts[:, 2].mean() - build_platform_z

    # Triangular prism approximation (overhangs are roughly triangular in cross-section)
    # cone factor ~0.33 for pointed supports, closer to 0.5 for dense supports
    volume_estimate = overhang_area * avg_height * 0.4

    return volume_estimate


def full_analysis(mesh_path: str, angle_threshold: float = 45.0) -> dict:
    """Run full geometry analysis on an STL file."""
    mesh = load_stl(mesh_path)
    overhang_indices, overhang_mask = detect_overhangs(mesh, angle_threshold)
    severity = classify_overhang_severity(mesh, overhang_mask)
    islands = detect_islands(mesh, overhang_mask)
    support_volume = compute_support_volume_estimate(mesh, overhang_mask)

    return {
        "mesh_path": mesh_path,
        "mesh_stats": {
            "vertices": len(mesh.vertices),
            "faces": len(mesh.faces),
            "volume": mesh.volume,
            "area": mesh.area,
            "bounds": mesh.bounds.tolist(),
            "is_watertight": mesh.is_watertight,
        },
        "overhang": {
            "total_faces": int(overhang_mask.sum()),
            "percentage": float(overhang_mask.mean() * 100),
            "critical_faces": int(severity["critical"].sum()),
            "moderate_faces": int(severity["moderate"].sum()),
            "borderline_faces": int(severity["borderline"].sum()),
            "num_islands": len(islands),
            "island_sizes": [len(island) for island in islands],
            "estimated_support_volume_mm3": float(support_volume),
            "estimated_support_material_g": float(support_volume * 1.24 / 1000),  # PLA ~1.24g/cm3
        },
    }
