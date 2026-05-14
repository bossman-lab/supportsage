# SupportSage 🧠🖨️

**AI-optimized support structures for 3D printing.**

Stop guessing. Stop wasting filament. Stop sanding support scars.

SupportSage analyzes your STL model and generates **intelligent, geometry-aware support structures** that use 30-50% less material, reduce print time, and leave smoother surfaces.

```bash
# 🎯 One-command install (all 3 tools)
bash <(curl -sL https://raw.githubusercontent.com/bossman-lab/supportsage/main/scripts/install_3d_tools.sh)

# Or from source
git clone https://github.com/bossman-lab/supportsage
cd supportsage && pip install -e .
```

---

## Features

| Feature | CLI | Web Demo | GUI | Cura Plugin |
|---------|:---:|:--------:|:---:|:-----------:|
| Overhang analysis | ✅ | ✅ | ✅ | ✅ |
| Tree support generation | ✅ | ✅ | ✅ | via CLI |
| Material savings estimate | ✅ | ✅ | ✅ | ✅ |
| Interactive 3D viewer | ❌ | ✅ | ✅ | ❌ |
| One-click optimize | ❌ | ❌ | ✅ | ✅ |
| Batch processing | ✅ | ❌ | ❌ | ❌ |
| JSON export | ✅ | ❌ | ✅ | ✅ |
| **FilamentDB integration** | ✅ | ✅ | ✅ | ❌ |
| **Print inspection** | ✅ | ✅ | ✅ | ❌ |

## Quick Start

```bash
# Analyze overhangs
supportsage analyze model.stl

# Generate optimized tree supports
supportsage tree model.stl -o optimized.stl --strategy balanced
#                      strategy: light | balanced | heavy

# Generate pillar supports
supportsage optimize model.stl -o model_with_supports.stl --strategy balanced

# Export strategy for Cura plugin
supportsage export model.stl -f json -o strategy.json
```

## Integration Suite 🔗

SupportSage integrates with two companion tools for a complete 3D printing workflow:

### FilamentDB — Smart Parameter Lookup

Pass `--filament "Brand Model"` to any command. SupportSage auto-looks up the recommended nozzle temperature, bed temperature, and other settings from the [FilamentDB](https://github.com/bossman-lab/filamentdb) open database.

```bash
# Analyze with filament-specific recommendations
supportsage analyze model.stl --filament "Bambu Lab PLA Basic"
# → Adds: 🔥 Nozzle: 220°C | Bed: 55°C | Fan: 100%

# Optimize with filament context
supportsage tree model.stl -o optimized.stl --filament "eSun PLA+"
```

### Printsight — Post-Print Quality Check

Pass `--inspect photo.jpg` to the `tree` command. After generating supports, it runs a full [Printsight](https://github.com/bossman-lab/printsight) quality inspection on your printed result.

```bash
# Generate supports → then inspect the print
supportsage tree model.stl -o optimized.stl --filament "PLA+" --inspect after_print.jpg
# → 🌳 Tree supports generated
# → 🔥 Filament: 215°C / 60°C
# → 🖨️ Printsight: Good (0.82) — No stringing, minor warping
```

### Complete Workflow — One Command

```bash
# Analyze → Print → Inspect — all in one pipeline
supportsage tree model.stl -o out.stl --filament "Bambu Lab PLA Basic" --inspect final_print.jpg
```

## Desktop GUI

```bash
supportsage-gui --open
# → Opens http://localhost:5000
```

A local web app that combines the 3D viewer with the full CLI engine. Drop STL → visualize overhangs → click "Generate Tree Supports" → download optimized STL. No terminal needed beyond the launch command.

## Cura Plugin

Adds "SupportSage" menu to Cura:
- **Run SupportSage on Model...** — analyzes the open STL and applies settings automatically
- **Load Strategy...** — imports a pre-exported JSON strategy
- **Clear SupportSage Settings** — resets to defaults

Install: `bash cura_plugin/install.sh` or copy `cura_plugin/` to Cura's plugins folder.

## Benchmarks

| Model | Traditional | SupportSage | Savings |
|-------|-------------|-------------|---------|
| Multi-bridge | 6,317mm³ | 4,211mm³ | **33%** |
| Cantilever platform | 18,440mm³ | 12,293mm³ | **33%** |
| Multi-level scaffold | 11,194mm³ | 7,463mm³ | **33%** |
| **Total** | **35,951mm³** | **23,967mm³** | **33%** |

## Architecture

```
STL input → trimesh mesh
     ↓
Overhang detection (face normal × Z-up dot product)
     ↓
Severity classification (critical / moderate / borderline / safe)
     ↓
Island detection (disconnected region BFS)
     ↓
Per-island strategy assignment
     ↓
Tree support generation (branching organic structures)
     ↓
STL / JSON / G-code export
```

## How It Works

Traditional slicers use a binary check: "Is this face >45° from vertical? Fill everything beneath with support."

SupportSage treats overhangs as a **spectrum**:

| Severity | Angle | Strategy |
|----------|-------|----------|
| 🔴 Critical | >120° from vertical | Dense interface, thick branches |
| 🟠 Moderate | 70-120° | Tree supports, medium density |
| 🟡 Borderline | 45-70° | Light touch, thin pillars |
| 🟢 Safe | <45° | No support needed |

Then it finds **disconnected overhang regions** (islands) via BFS and assigns the optimal strategy per island. A bridge span gets two small support islands at each end — not one giant block.

## Web Demo

**bossman-lab.github.io/supportsage** (enable GitHub Pages first)

A pure client-side version: drag an STL, see color-coded overhangs, rotate/zoom, no upload required. Works entirely in your browser via Three.js.

## CLI Reference

```
supportsage analyze model.stl          Analyze overhangs
supportsage analyze model.stl --filament "PLA"   + filament recommendations
supportsage tree model.stl -o out.stl  Generate tree supports
supportsage tree model.stl --filament "..." --inspect photo.jpg   full pipeline
supportsage optimize model.stl -o...   Generate pillar supports
supportsage export model.stl -f...     Export support strategy
supportsage-gui --open                 Launch desktop GUI (with filament + inspect)
```

## Related Projects

- [FilamentDB](https://github.com/bossman-lab/filamentdb) — Open-source filament parameter database. Search, compare, get AI-recommended print settings.
- [Printsight](https://github.com/bossman-lab/printsight) — 3D print quality inspection. Detect stringing, layer issues, warping from a photo.

## Blog Posts

1. [I Built an AI That Slices Your Support Waste by 40%](https://dev.to/lanternproton/i-built-an-ai-that-slices-your-3d-printing-support-waste-by-40-2hg)
2. [How Tree Support Generation Actually Works](https://dev.to/lanternproton/how-tree-support-generation-actually-works-and-why-yours-are-wasting-filament-2bg9)
3. [We Benchmarked SupportSage: Here's the Data](https://dev.to/lanternproton/we-benchmarked-supportsage-against-traditional-supports-heres-the-data-52p2)
4. [Browser-Based 3D Print Overhang Analyzer](https://dev.to/lanternproton/i-built-a-browser-based-3d-print-overhang-analyzer-no-backend-no-uploads-50m9)
5. [Desktop GUI and Cura Plugin](https://dev.to/lanternproton/supportsage-now-has-a-desktop-gui-and-cura-plugin-no-cli-required-cll)

## License

MIT
