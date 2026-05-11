"""
Tree support generator — branching organic support structures.

Algorithm inspired by the tree support approach used in PrusaSlicer
and Cura, but with AI-guided optimization per-overhang-island.

How it works:
1. Sample overhang islands → support points
2. From each point, grow branches downward toward build plate
3. Merge nearby branches into trunks (like real trees)
4. Enforce printability constraints (max branch angle, min thickness)
5. Generate 3D mesh geometry
"""
from __future__ import annotations

import math
import numpy as np
import trimesh
from typing import List, Tuple, Optional

from . import analyzer


# ─── Data Structures ───────────────────────────────────────────────

class SupportPoint:
    """A single point that needs support, on the underside of an overhang."""
    def __init__(self, position: np.ndarray, island_id: int, severity: str):
        self.pos = np.array(position, dtype=float)
        self.island_id = island_id
        self.severity = severity  # 'critical', 'moderate', 'borderline'
        self.branch: Optional["Branch"] = None


class BranchNode:
    """A node in the branching tree structure."""
    def __init__(self, pos: np.ndarray, radius: float, parent: Optional["BranchNode"] = None):
        self.pos = np.array(pos, dtype=float)
        self.radius = radius
        self.parent = parent
        self.children: List["BranchNode"] = []


class BranchTree:
    """A complete branching support tree from build plate to one or more support points."""
    def __init__(self, root: BranchNode):
        self.root = root

    def all_nodes(self) -> List[BranchNode]:
        """BFS to collect all nodes."""
        nodes = []
        queue = [self.root]
        while queue:
            node = queue.pop(0)
            nodes.append(node)
            queue.extend(node.children)
        return nodes


# ─── Constants ────────────────────────────────────────────────────

# Maximum angle from vertical for a printed branch (degrees)
# Steeper = more printable but uses more material
MAX_BRANCH_ANGLE_DEG = 60.0
MAX_BRANCH_ANGLE_RAD = math.radians(MAX_BRANCH_ANGLE_DEG)

# Minimum branch radius at the tip
MIN_BRANCH_RADIUS = 0.6  # mm

# Base branch radius multiplier (critical islands get thicker branches)
BASE_RADIUS = {
    "critical": 1.5,
    "moderate": 1.0,
    "borderline": 0.8,
}

# Distance threshold for merging two branches (mm)
MERGE_DISTANCE = 5.0

# Segments for cylindrical approximation
CYLINDER_SEGMENTS = 8

# Build plate Z
BUILD_PLATE_Z = 0.0


# ─── Core Algorithm ───────────────────────────────────────────────

def sample_support_points(
    mesh: trimesh.Trimesh,
    islands: List[np.ndarray],
    overhang_mask: np.ndarray,
    severity: dict,
    density: float = 1.0,
) -> List[List[SupportPoint]]:
    """
    Sample support points from each overhang island.

    Returns a list of island-support-point-groups (one list per island).
    density=1.0 samples the centroid of every face.
    density=0.5 samples every other face (fewer points, less material).
    """
    island_groups = []
    for i, island in enumerate(islands):
        faces = mesh.faces[island]
        verts = mesh.vertices[faces]

        # Determine severity for this island
        n_critical = int(severity["critical"][island].sum())
        n_moderate = int(severity["moderate"][island].sum())
        if n_critical > 0:
            sev = "critical"
            step = max(1, int(1 / max(density, 0.1)))
        elif n_moderate > 0:
            sev = "moderate"
            step = max(1, int(2 / max(density, 0.1)))
        else:
            sev = "borderline"
            step = max(1, int(4 / max(density, 0.1)))

        points = []
        for idx in range(0, len(island), step):
            face_verts = verts[idx]
            centroid = face_verts.mean(axis=0)

            # Only add support points for downward-facing regions
            # (bottom face of overhang vs. top face that doesn't need support)
            normal = mesh.face_normals[island[idx]]
            if normal[2] < 0:  # normal points downward
                # Offset slightly below the surface
                centroid = centroid - normal * 0.1
                points.append(SupportPoint(centroid, i, sev))

        # If the island is large and we got too few points, force at least one
        if len(points) == 0 and len(island) > 0:
            face_verts = verts[0]
            centroid = face_verts.mean(axis=0)
            normal = mesh.face_normals[island[0]]
            if normal[2] < 0:
                centroid = centroid - normal * 0.1
            points.append(SupportPoint(centroid, i, "moderate"))

        island_groups.append(points)

    return island_groups


def _ray_intersect_plate(
    point: np.ndarray,
    direction: np.ndarray,
) -> float:
    """Find intersection distance from point along direction to build plate (z=0)."""
    if direction[2] >= 0:
        return -1  # pointing away from plate
    t = (BUILD_PLATE_Z - point[2]) / direction[2]
    return t


def grow_branch(
    support_point: SupportPoint,
    existing_trunks: List[List[np.ndarray]],
) -> BranchTree:
    """
    Grow a branching support from a support point down to the build plate.

    The algorithm:
    1. Start at the support point
    2. Cast a ray straight down toward build plate
    3. Check if this ray passes close to any existing trunk
    4. If close enough, merge (branch into the existing trunk)
    5. Otherwise, grow all the way to the build plate
    6. Apply angle constraints to keep branches printable
    """
    pos = support_point.pos.copy()
    radius = BASE_RADIUS.get(support_point.severity, 1.0)

    # Start node at support point
    tip_node = BranchNode(pos, radius)

    # Direction: straight down, then check for merge opportunities
    down = np.array([0, 0, -1.0])

    # Check merge distance against existing trunks
    merged = False
    parent_node = None

    for trunk in existing_trunks:
        for trunk_point in trunk:
            # Distance in XY only (Z doesn't matter for merge)
            dist_xy = np.linalg.norm(pos[:2] - trunk_point[:2])
            if dist_xy < MERGE_DISTANCE and trunk_point[2] < pos[2]:
                # Found a merge point! This trunk is below us and close enough.
                # Branch to this merge point instead of going all the way down.
                branch_end = trunk_point.copy()
                branch_end[2] = min(branch_end[2], pos[2] - 2.0)  # merge slightly below
                parent_pos = branch_end
                merged = True
                break
        if merged:
            break

    if not merged:
        # Grow straight down to build plate
        t = _ray_intersect_plate(pos, down)
        if t > 0:
            parent_pos = pos + down * t
        else:
            parent_pos = pos.copy()
            parent_pos[2] = BUILD_PLATE_Z

    # Apply angle constraint: the branch can't be too steep
    delta = parent_pos - pos
    horizontal_dist = np.linalg.norm(delta[:2])
    vertical_dist = abs(delta[2])

    if vertical_dist > 0 and horizontal_dist / vertical_dist > math.tan(MAX_BRANCH_ANGLE_RAD):
        # Too steep! Add an intermediate node to break the angle
        max_h = vertical_dist * math.tan(MAX_BRANCH_ANGLE_RAD)
        intermediate_pos = pos.copy()
        if horizontal_dist > 0:
            direction_xy = delta[:2] / horizontal_dist
            intermediate_pos[:2] = pos[:2] + direction_xy * max_h
        intermediate_pos[2] = pos[2] - vertical_dist * 0.5

        intermediate_node = BranchNode(
            intermediate_pos, radius * 0.8, tip_node
        )
        tip_node.children.append(intermediate_node)

        # Continue from intermediate node
        parent_node = BranchNode(parent_pos, MIN_BRANCH_RADIUS, intermediate_node)
        intermediate_node.children.append(parent_node)
    else:
        parent_node = BranchNode(parent_pos, MIN_BRANCH_RADIUS, tip_node)
        tip_node.children.append(parent_node)

    return BranchTree(tip_node)


def tree_to_mesh(tree: BranchTree) -> trimesh.Trimesh:
    """
    Convert a branch tree into a printable 3D mesh.

    Each branch segment becomes a tapered cylinder (cone frustum).
    """
    all_nodes = tree.all_nodes()
    meshes = []

    for node in all_nodes:
        if not node.parent and not node.children:
            continue

        # Connect this node to its parent
        if node.parent:
            parent = node.parent
            segment = _make_tapered_cylinder(
                node.pos, node.radius,
                parent.pos, parent.radius,
            )
            meshes.append(segment)

        # Connect this node to its children
        for child in node.children:
            segment = _make_tapered_cylinder(
                child.pos, child.radius,
                node.pos, node.radius,
            )
            meshes.append(segment)

    if not meshes:
        return trimesh.Trimesh()

    return trimesh.util.concatenate(meshes)


def _make_tapered_cylinder(
    p1: np.ndarray,
    r1: float,
    p2: np.ndarray,
    r2: float,
    segments: int = CYLINDER_SEGMENTS,
) -> trimesh.Trimesh:
    """Create a tapered cylinder (cone frustum) from p1→p2 with radii r1→r2."""
    direction = p2 - p1
    length = np.linalg.norm(direction)
    if length < 0.01 or (r1 < 0.01 and r2 < 0.01):
        return trimesh.Trimesh()

    direction /= length

    # Build local coordinate system
    if abs(direction[2]) < 0.99:
        up = np.array([0, 0, 1.0])
    else:
        up = np.array([1, 0, 0.0])

    right = np.cross(direction, up)
    right /= np.linalg.norm(right)
    forward = np.cross(right, direction)

    theta = np.linspace(0, 2 * np.pi, segments, endpoint=False)

    # Vertices for bottom ring (p1) and top ring (p2)
    bottom_verts = []
    top_verts = []

    for t in theta:
        circle_vec = right * math.cos(t) + forward * math.sin(t)
        bottom_verts.append(p1 + circle_vec * r1)
        top_verts.append(p2 + circle_vec * r2)

    # Build faces (quadrilateral strips)
    verts = np.vstack(bottom_verts + top_verts)
    faces = []

    n = segments
    for i in range(n):
        i_next = (i + 1) % n
        # Two triangles per quad
        faces.append([i, i_next, i + n])
        faces.append([i_next, i_next + n, i + n])

    # Bottom cap
    bottom_center = len(verts)
    verts = np.vstack([verts, p1])
    for i in range(n):
        i_next = (i + 1) % n
        faces.append([bottom_center, i_next, i])

    # Top cap
    top_center = len(verts)
    verts = np.vstack([verts, p2])
    for i in range(n):
        i_next = (i + 1) % n
        faces.append([top_center, i + n, i_next + n])

    return trimesh.Trimesh(vertices=verts, faces=np.array(faces))


def generate_tree_supports(
    mesh_path: str,
    angle_threshold: float = 45.0,
    density: str = "balanced",
    output_path: str = "tree_supports.stl",
) -> str:
    """
    Full pipeline: analyze STL → generate tree supports → export STL.

    This is the main entry point for tree support generation.
    """
    # Step 1: Analyze
    mesh = analyzer.load_stl(mesh_path)
    _, overhang_mask = analyzer.detect_overhangs(mesh, angle_threshold)
    islands = analyzer.detect_islands(mesh, overhang_mask)
    severity = analyzer.classify_overhang_severity(mesh, overhang_mask)

    if len(islands) == 0:
        print("  No overhang islands detected — model may not need supports.")
        # Create empty mesh
        trimesh.Trimesh().export(output_path)
        return output_path

    # Step 2: Density config
    density_map = {"light": 0.5, "balanced": 1.0, "heavy": 1.5}
    density_val = density_map.get(density, 1.0)

    # Step 3: Sample support points
    island_points = sample_support_points(
        mesh, islands, overhang_mask, severity, density_val
    )

    total_points = sum(len(pts) for pts in island_points)
    print(f"  Sampled {total_points} support points across {len(islands)} islands")

    # Step 4: Grow branch trees
    existing_trunks = []
    all_meshes = []

    for island_pts in island_points:
        for sp in island_pts:
            tree = grow_branch(sp, existing_trunks)

            # Record trunk path for merge detection
            trunk_path = [sp.pos]
            current = sp.branch.root if hasattr(sp, 'branch') and sp.branch else None
            if current:
                for node in tree.all_nodes():
                    trunk_path.append(node.pos)
            existing_trunks.append(trunk_path)

            # Convert to mesh
            branch_mesh = tree_to_mesh(tree)
            if len(branch_mesh.vertices) > 0:
                all_meshes.append(branch_mesh)

    if not all_meshes:
        print("  Warning: No support geometry generated.")
        trimesh.Trimesh().export(output_path)
        return output_path

    # Step 5: Merge and export
    result = trimesh.util.concatenate(all_meshes)
    result.export(output_path)

    # Stats
    print(f"  Generated {total_points} branches -> {len(result.vertices)} vertices")
    print(f"  ✅ Output: {output_path}")

    return output_path


# ─── CLI Entry Point ──────────────────────────────────────────────

def add_tree_parser(subparsers):
    """Add the 'tree' subcommand to the CLI parser."""
    parser = subparsers.add_parser("tree", help="Generate tree (organic) supports")
    parser.add_argument("model", type=str, help="Path to STL file")
    parser.add_argument("-o", "--output", type=str, default="tree_supports.stl",
                        help="Output STL path")
    parser.add_argument("--angle", type=float, default=45.0,
                        help="Overhang angle threshold")
    parser.add_argument("--strategy", choices=["light", "balanced", "heavy"],
                        default="balanced", help="Support density strategy")
    return parser


def tree_command(args):
    """Handle 'supportsage tree' command."""
    print(f"\n  🌳 SupportSage Tree Support Generator")
    print(f"  {'=' * 40}")
    print(f"  Model: {args.model}")
    print(f"  Strategy: {args.strategy}")
    print()

    generate_tree_supports(
        args.model,
        args.angle,
        args.strategy,
        args.output,
    )
