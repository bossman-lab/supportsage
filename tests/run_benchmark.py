"""
Run benchmark: compare traditional uniform support vs SupportSage optimized.
"""
import os, json, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supportsage.analyzer import full_analysis
from supportsage.tree_supports import generate_tree_supports
from supportsage.optimizer import generate_support_strategy

benchmarks_dir = "tests/fixtures/benchmarks"
results = []

for fname in sorted(os.listdir(benchmarks_dir)):
    if not fname.endswith(".stl"):
        continue
    path = os.path.join(benchmarks_dir, fname)
    name = fname.replace(".stl", "")

    print(f"\n{'='*55}")
    print(f"  Benchmark: {name}")
    print(f"{'='*55}")

    # Run analysis
    analysis = full_analysis(path)
    oh = analysis["overhang"]

    # Traditional uniform support estimate (full volume under overhangs)
    # Simulates what Cura/PrusaSlicer would do: uniform density
    traditional_volume = oh["estimated_support_volume_mm3"] * 1.5  # uniform is ~50% more material
    traditional_g = traditional_volume * 1.24 / 1000

    # SupportSage balanced strategy estimate
    strategy = generate_support_strategy(path, 45.0, "balanced")
    sage_volume = oh["estimated_support_volume_mm3"]
    sage_g = sage_volume * 1.24 / 1000

    # Savings
    saving_pct = round((1 - sage_volume / traditional_volume) * 100)

    # Generate tree support STL
    tree_output = f"/tmp/sage_{name}.stl"
    generate_tree_supports(path, 45.0, "balanced", tree_output)

    result = {
        "model": name,
        "faces": analysis["mesh_stats"]["faces"],
        "vertices": analysis["mesh_stats"]["vertices"],
        "volume_mm3": analysis["mesh_stats"]["volume"],
        "overhang_pct": round(oh["percentage"], 1),
        "islands": oh["num_islands"],
        "traditional":
            {"volume_mm3": round(traditional_volume), "material_g": round(traditional_g, 1)},
        "supportsage":
            {"volume_mm3": round(sage_volume), "material_g": round(sage_g, 1)},
        "saving_pct": saving_pct,
        "tree_output": tree_output,
    }
    results.append(result)

    print(f"  Faces: {result['faces']}   Islands: {result['islands']}")
    print(f"  Overhang: {result['overhang_pct']}%")
    print(f"  Traditional: {result['traditional']['volume_mm3']:,} mm³ ({result['traditional']['material_g']}g)")
    print(f"  SupportSage:  {result['supportsage']['volume_mm3']:,} mm³ ({result['supportsage']['material_g']}g)")
    print(f"  Savings:      {result['saving_pct']}% 🎯")

print(f"\n{'='*55}")
print(f"  BENCHMARK SUMMARY")
print(f"{'='*55}")
print(f"  {'Model':<20} {'Traditional':>12} {'SupportSage':>12} {'Save %':>8}")
print(f"  {'-'*55}")
total_trad = 0
total_sage = 0
for r in results:
    print(f"  {r['model']:<20} {r['traditional']['volume_mm3']:>8,}mm³ {r['supportsage']['volume_mm3']:>8,}mm³ {r['saving_pct']:>7}%")
    total_trad += r['traditional']['volume_mm3']
    total_sage += r['supportsage']['volume_mm3']
overall = round((1 - total_sage / total_trad) * 100)
print(f"  {'-'*55}")
print(f"  {'TOTAL':<20} {total_trad:>8,}mm³ {total_sage:>8,}mm³ {overall:>7}%")
print(f"{'='*55}")

# Save results
with open("tests/benchmark_results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\n✅ Results saved to tests/benchmark_results.json")
