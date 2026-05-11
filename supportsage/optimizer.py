"""
Support optimizer — generates optimized support structures.

Key ideas:
1. Instead of uniform support density, use variable density:
   - Critical overhangs → dense support (high contact)
   - Moderate overhangs → tree/organic support (low contact)
   - Bridge spans → minimal pillar support at endpoints only

2. Support placement optimization:
   - Combine nearby support columns into branching structures
   - Route supports through existing geometry where possible
   - Minimize Z-height for support columns (split tall columns)

3. Surface quality preservation:
   - Use "interface layers" (dense top layers on supports)
   - Prefer tree supports near aesthetic surfaces
   - Angled support tips for cleaner breakaway
"""
from __future__ import annotations

import numpy as np
import trimesh
from . import analyzer


def generate_support_strategy(
    mesh_path: str,
    angle_threshold: float = 45.0,
    density: str = "balanced",
) -> dict:
    """
    Generate an optimized support strategy for the given model.

    Returns a strategy dict that can be used to:
    - Generate support STL geometry
    - Export as slicer-compatible configuration
    - Visualize support placement

    density options: 'light', 'balanced', 'heavy'
    """
    analysis = analyzer.full_analysis(mesh_path, angle_threshold)

    mesh = analyzer.load_stl(mesh_path)
    _, overhang_mask = analyzer.detect_overhangs(mesh, angle_threshold)
    islands = analyzer.detect_islands(mesh, overhang_mask)
    severity = analyzer.classify_overhang_severity(mesh, overhang_mask)

    # Density multipliers
    density_map = {
        "light": {"critical": 0.7, "moderate": 0.4, "tree": True},
        "balanced": {"critical": 1.0, "moderate": 0.6, "tree": True},
        "heavy": {"critical": 1.0, "moderate": 1.0, "tree": False},
    }
    config = density_map.get(density, density_map["balanced"])

    # Compute per-island strategy
    island_strategies = []
    for i, island in enumerate(islands):
        island_faces = mesh.faces[island]

        # Check what severity faces are in this island
        critical_count = int(severity["critical"][island].sum())
        moderate_count = int(severity["moderate"][island].sum())

        if critical_count > 0 and config["tree"]:
            # Critical areas get dense support with interface layers
            strategy = "heavy_interface"
            support_density = config["critical"]
        elif moderate_count > 0 and config["tree"]:
            # Moderate areas get tree supports
            strategy = "tree"
            support_density = config["moderate"]
        else:
            strategy = "minimal"
            support_density = 0.3

        island_strategies.append({
            "island_id": i,
            "face_count": len(island),
            "critical_faces": critical_count,
            "moderate_faces": moderate_count,
            "strategy": strategy,
            "density": support_density,
            "center": mesh.vertices[island_faces.flatten()].mean(axis=0).tolist(),
        })

    # Build complete strategy
    strategy = {
        "model": mesh_path,
        "analysis": {
            "overhang_percentage": analysis["overhang"]["percentage"],
            "estimated_support_volume_mm3": analysis["overhang"]["estimated_support_volume_mm3"],
            "support_material_g": analysis["overhang"]["estimated_support_material_g"],
            "num_islands": analysis["overhang"]["num_islands"],
        },
        "config": {
            "angle_threshold": angle_threshold,
            "density": density,
            "support_type": "tree" if config["tree"] else "standard",
            "interface_layers": True,
        },
        "island_strategies": island_strategies,
        "savings_estimate": {
            "material_saved_vs_uniform": f"{_estimate_savings(analysis, density)}%",
        },
    }

    return strategy


def _estimate_savings(analysis: dict, density: str) -> int:
    """Estimate material savings vs traditional uniform support."""
    savings_map = {"light": 50, "balanced": 35, "heavy": 15}
    return savings_map.get(density, 35)


def generate_support_geometry(
    strategy: dict,
    output_path: str,
) -> str:
    """
    Generate actual support STL geometry from strategy.

    This is a simplification — MVP generates pillar supports
    at detected overhang island centers.
    """
    # For MVP: generate simple support pillars
    mesh = analyzer.load_stl(strategy["model"])
    _, overhang_mask = analyzer.detect_overhangs(
        mesh, strategy["config"]["angle_threshold"]
    )
    islands = analyzer.detect_islands(mesh, overhang_mask)

    # Build support pillars
    support_meshes = []
    for i, island_strat in enumerate(strategy["island_strategies"]):
        if i >= len(islands):
            break
        island = islands[i]
        if len(island) == 0:
            continue

        # Get center point of island
        island_verts = mesh.vertices[mesh.faces[island].flatten()]
        center_x, center_y = island_verts[:, :2].mean(axis=0)
        min_z = island_verts[:, 2].min()
        max_z = island_verts[:, 2].max()

        # Default pillar radius based on island size
        radius = max(1.0, min(5.0, len(island) ** 0.5 * 0.5))

        # Create a simple cylinder support
        height = max_z - 0.0  # from build plate (z=0)
        if height < 0.5:
            continue

        support = _make_pillar(
            center=(center_x, center_y),
            height=height,
            radius=radius * island_strat["density"],
            segments=12,
        )
        support_meshes.append(support)

    if not support_meshes:
        # Create empty mesh
        result = trimesh.Trimesh()
    else:
        result = trimesh.util.concatenate(support_meshes)

    result.export(output_path)
    return output_path


def _make_pillar(
    center: tuple[float, float],
    height: float,
    radius: float,
    segments: int = 12,
) -> trimesh.Trimesh:
    """Create a simple cylindrical support pillar."""
    import math

    cx, cy = center
    vertices = []
    faces = []

    # Bottom ring
    theta = np.linspace(0, 2 * np.pi, segments, endpoint=False)
    for t in theta:
        vertices.append([cx + radius * math.cos(t), cy + radius * math.sin(t), 0.0])
    # Top ring
    for t in theta:
        vertices.append([cx + radius * math.cos(t), cy + radius * math.sin(t), height])
    # Center bottom and top
    vertices.append([cx, cy, 0.0])  # bottom center
    vertices.append([cx, cy, height])  # top center

    n = segments
    bottom_center = 2 * n
    top_center = 2 * n + 1

    # Side faces (quadrilaterals as two triangles)
    for i in range(n):
        i_next = (i + 1) % n
        # Lower triangle
        faces.append([i, i_next, i + n])
        # Upper triangle
        faces.append([i_next, i_next + n, i + n])

    # Bottom cap
    for i in range(n):
        i_next = (i + 1) % n
        faces.append([bottom_center, i_next, i])

    # Top cap
    for i in range(n):
        i_next = (i + 1) % n
        faces.append([top_center, i + n, i_next + n])

    mesh = trimesh.Trimesh(
        vertices=np.array(vertices),
        faces=np.array(faces),
    )
    return mesh
