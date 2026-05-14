"""
Generate realistic benchmark models for SupportSage testing.

Creates STL models with controlled overhang complexity for
measuring support material savings.
"""
import trimesh
import numpy as np
import os


def _make_gear_like(outer_radius: float, inner_radius: float, height: float,
                     num_teeth: int, tooth_height: float) -> trimesh.Trimesh:
    """Create a gear-like model with overhang teeth."""
    # Base cylinder
    base = trimesh.creation.cylinder(radius=inner_radius, height=height * 0.3,
                                     sections=48)
    base.apply_translation([0, 0, 0])

    # Inner column
    column = trimesh.creation.cylinder(radius=inner_radius * 0.3, height=height,
                                       sections=32)
    column.apply_translation([0, 0, height * 0.15])

    # Overhang arms (these create the support challenge)
    meshes = [base, column]
    for i in range(num_teeth):
        angle = 2 * np.pi * i / num_teeth
        arm = trimesh.creation.box(extents=(tooth_height, inner_radius * 0.15, height * 0.4))
        arm.apply_translation([
            (inner_radius + tooth_height / 2) * np.cos(angle),
            (inner_radius + tooth_height / 2) * np.sin(angle),
            height * 0.6
        ])
        # Rotate to point outward
        arm.apply_transform(trimesh.transformations.rotation_matrix(
            angle, [0, 0, 1], [0, 0, 0]
        ))
        meshes.append(arm)

    # Top cap with overhang
    top_cap = trimesh.creation.cylinder(radius=outer_radius, height=height * 0.15,
                                        sections=48)
    top_cap.apply_translation([0, 0, height * 0.85])
    meshes.append(top_cap)

    return trimesh.util.concatenate(meshes)


def make_benchmark_models(output_dir: str):
    """Generate a set of benchmark models."""
    os.makedirs(output_dir, exist_ok=True)
    models = {}

    # Model 1: Multi-bridge with varying spans
    print("Generating model 1: multi-bridge...")
    base = trimesh.creation.box(extents=(60, 10, 5))
    # Three pillars of different heights
    pillar_positions = [(-20, 0), (0, 0), (20, 0)]
    pillar_heights = [8, 12, 6]
    pillars = []
    for (px, py), ph in zip(pillar_positions, pillar_heights):
        p = trimesh.creation.box(extents=(3, 3, ph))
        p.apply_translation([px, py, ph / 2])
        pillars.append(p)
    # Bridges connecting pillars (these create overhangs)
    bridges = [
        trimesh.creation.box(extents=(18, 2, 1.5)),
        trimesh.creation.box(extents=(18, 2, 1.5)),
    ]
    bridges[0].apply_translation([-10, 0, 8 + 0.75])
    bridges[1].apply_translation([10, 0, 12 + 0.75])

    model1 = trimesh.util.concatenate([base] + pillars + bridges)
    model1.export(os.path.join(output_dir, "bench_multi_bridge.stl"))
    models["multi_bridge"] = model1

    # Model 2: Cantilever + platform (realistic overhang scenario)
    print("Generating model 2: cantilever...")
    base2 = trimesh.creation.box(extents=(20, 20, 4))
    column = trimesh.creation.box(extents=(6, 6, 15))
    column.apply_translation([0, 0, 9.5])
    # Wide platform on top (significant overhang)
    platform = trimesh.creation.box(extents=(35, 35, 2))
    platform.apply_translation([0, 0, 18])
    # Angled support ring (creates split overhang islands)
    ring = trimesh.creation.cylinder(radius=12, height=1, sections=32)
    ring.apply_translation([0, 0, 10])

    model2 = trimesh.util.concatenate([base2, column, platform, ring])
    model2.export(os.path.join(output_dir, "bench_cantilever.stl"))
    models["cantilever"] = model2

    # Model 3: Scaffold with multiple levels and complex overhangs
    print("Generating model 3: scaffold...")
    # Multi-level structure with offset platforms
    levels = []
    for i in range(4):
        offset_x = (i % 2) * 8 - 4
        offset_y = ((i + 1) % 2) * 8 - 4
        z_pos = i * 8
        platform_l = trimesh.creation.box(extents=(12, 12, 1.5))
        platform_l.apply_translation([offset_x, offset_y, z_pos])
        # Support pillars
        for corner in [(-5, -5), (5, -5), (-5, 5), (5, 5)]:
            pillar = trimesh.creation.box(extents=(1.5, 1.5, 6.5))
            pillar.apply_translation([corner[0] + offset_x, corner[1] + offset_y, z_pos - 3.25])
            platform_l = trimesh.util.concatenate([platform_l, pillar])
        levels.append(platform_l)

    model3 = trimesh.util.concatenate([trimesh.creation.box(extents=(20, 20, 2))] + levels)
    model3.export(os.path.join(output_dir, "bench_scaffold.stl"))
    models["scaffold"] = model3

    print(f"\n✅ Generated {len(models)} benchmark models in {output_dir}")
    for name, m in models.items():
        print(f"   {name}: {len(m.faces)} faces, bounds={m.bounds.tolist()}")

    return models


if __name__ == "__main__":
    make_benchmark_models("tests/fixtures/benchmarks")
