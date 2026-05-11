"""
SupportSage CLI - AI-optimized support structures for 3D printing.

Usage:
    supportsage analyze model.stl
    supportsage optimize model.stl -o output.stl --strategy balanced
    supportsage export model.stl -f cura-json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .analyzer import full_analysis
from .optimizer import generate_support_strategy, generate_support_geometry


def main():
    parser = argparse.ArgumentParser(
        prog="supportsage",
        description="AI-optimized support structures for 3D printing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  supportsage analyze model.stl
      Analyze overhangs and estimate support material needed.

  supportsage optimize model.stl -o output.stl --strategy balanced
      Generate optimized support structures for the model.

  supportsage analyze model.stl --json
      Output analysis as JSON for programmatic use.
        """,
    )

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # analyze
    analyze_parser = subparsers.add_parser("analyze", help="Analyze STL overhangs")
    analyze_parser.add_argument("model", type=str, help="Path to STL file")
    analyze_parser.add_argument(
        "--angle", type=float, default=45.0, help="Overhang angle threshold (default: 45)"
    )
    analyze_parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )

    # optimize
    optimize_parser = subparsers.add_parser("optimize", help="Generate optimized supports")
    optimize_parser.add_argument("model", type=str, help="Path to STL file")
    optimize_parser.add_argument(
        "-o", "--output", type=str, default="model_with_supports.stl",
        help="Output STL path"
    )
    optimize_parser.add_argument(
        "--angle", type=float, default=45.0, help="Overhang angle threshold"
    )
    optimize_parser.add_argument(
        "--strategy", choices=["light", "balanced", "heavy"],
        default="balanced", help="Support density strategy"
    )

    # export
    export_parser = subparsers.add_parser("export", help="Export support strategy")
    export_parser.add_argument("model", type=str, help="Path to STL file")
    export_parser.add_argument(
        "-f", "--format", choices=["json", "cura-json", "orca-config"],
        default="json", help="Export format"
    )
    export_parser.add_argument(
        "-o", "--output", type=str, default=None,
        help="Output file path (default: stdout)"
    )

    args = parser.parse_args()

    if args.command == "analyze":
        _cmd_analyze(args)
    elif args.command == "optimize":
        _cmd_optimize(args)
    elif args.command == "export":
        _cmd_export(args)
    else:
        parser.print_help()
        sys.exit(1)


def _cmd_analyze(args):
    try:
        result = full_analysis(args.model, args.angle)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result, indent=2))
        return

    oh = result["overhang"]
    ms = result["mesh_stats"]

    print(f"\n{'='*50}")
    print(f"  SupportSage Analysis")
    print(f"  {result['mesh_path']}")
    print(f"{'='*50}")
    print(f"\n  📐 Model Stats:")
    print(f"     Vertices: {ms['vertices']:,}")
    print(f"     Faces:    {ms['faces']:,}")
    print(f"     Volume:   {ms['volume']:.1f} mm³")
    print(f"     Area:     {ms['area']:.1f} mm²")
    print(f"     Watertight: {'✅' if ms['is_watertight'] else '❌'}")

    print(f"\n  ⚠️ Overhang Analysis (threshold: {args.angle}°):")
    print(f"     Total overhang faces: {oh['total_faces']:,} ({oh['percentage']:.1f}%)")
    print(f"     🔴 Critical:  {oh['critical_faces']:,}")
    print(f"     🟡 Moderate:  {oh['moderate_faces']:,}")
    print(f"     🟢 Borderline: {oh['borderline_faces']:,}")
    print(f"     Islands:       {oh['num_islands']}")

    print(f"\n  💰 Support Material Estimate:")
    print(f"     Volume: {oh['estimated_support_volume_mm3']:.0f} mm³")
    print(f"     Weight: {oh['estimated_support_material_g']:.1f} g (PLA)")
    print(f"\n  💡 Run 'supportsage optimize {Path(args.model).name}'")
    print(f"     to generate optimized support structures.\n")


def _cmd_optimize(args):
    try:
        strategy = generate_support_strategy(
            args.model, args.angle, args.strategy
        )
        output_path = generate_support_geometry(strategy, args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"  SupportSage Optimization Complete")
    print(f"{'='*50}")
    print(f"\n  📊 Strategy: {args.strategy}")
    print(f"  🏝️ Overhang islands: {strategy['analysis']['num_islands']}")
    print(f"  📦 Estimated support: {strategy['analysis']['estimated_support_volume_mm3']:.0f} mm³")
    print(f"  💾 Saved: ~{strategy['savings_estimate']['material_saved_vs_uniform']}")
    print(f"\n  ✅ Output: {output_path}")
    print()


def _cmd_export(args):
    try:
        strategy = generate_support_strategy(args.model)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        output = json.dumps(strategy, indent=2)
    elif args.format == "cura-json":
        # Cura plugin format - simplified
        output = json.dumps({
            "type": "custom_support",
            "name": "SupportSage Optimized",
            "settings": {
                "support_angle": strategy["config"]["angle_threshold"],
                "support_density": strategy["config"]["density"],
                "support_type": strategy["config"]["support_type"],
                "support_interface_enable": strategy["config"]["interface_layers"],
            },
            "islands": [
                {
                    "id": s["island_id"],
                    "strategy": s["strategy"],
                    "center": s["center"],
                }
                for s in strategy["island_strategies"]
            ],
        }, indent=2)
    elif args.format == "orca-config":
        output = json.dumps({
            "support": {
                "enabled": True,
                "type": strategy["config"]["support_type"],
                "threshold_angle": strategy["config"]["angle_threshold"],
                "density": strategy["config"]["density"],
            },
        }, indent=2)
    else:
        output = json.dumps(strategy, indent=2)

    if args.output:
        Path(args.output).write_text(output)
        print(f"✅ Exported to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
