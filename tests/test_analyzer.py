"""Quick test of the analyzer on all test fixtures."""
from supportsage.analyzer import full_analysis
import json
import os

fixtures_dir = "tests/fixtures"
for fname in sorted(os.listdir(fixtures_dir)):
    if not fname.endswith(".stl"):
        continue
    path = os.path.join(fixtures_dir, fname)
    name = fname.replace(".stl", "")
    print()
    print("=" * 50)
    print(f"  Analyzing: {name}")
    print("=" * 50)
    try:
        result = full_analysis(path)
        oh = result["overhang"]
        ms = result["mesh_stats"]
        print(f"  Faces: {ms['faces']}")
        print(f"  Overhang: {oh['percentage']:.1f}% ({oh['total_faces']} faces)")
        print(f"  Critical: {oh['critical_faces']}, Moderate: {oh['moderate_faces']}")
        print(f"  Islands: {oh['num_islands']}")
        print(f"  Est. support: {oh['estimated_support_volume_mm3']:.0f} mm\u00b3 ({oh['estimated_support_material_g']:.1f}g)")
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
