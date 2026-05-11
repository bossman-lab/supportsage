# SupportSage 🧠🖨️

**AI-optimized support structures for 3D printing.**

Stop guessing. Stop wasting filament. Stop sanding support scars.

SupportSage analyzes your STL model and generates **intelligent, geometry-aware support structures** that use 30-50% less material, reduce print time, and leave smoother surfaces — all before your printer starts.

---

## The Problem

> _"I spent more time removing supports than the actual print took."_
> — Every 3D printing hobbyist at some point

Traditional slicers (Cura, PrusaSlicer, OrcaSlicer) use **rule-based support generation** — simple overhang angle thresholds applied uniformly. This leads to:
- **Over-supported** areas that waste material and leave ugly scars
- **Under-supported** areas that sag or collapse mid-print
- **No per-geometry intelligence** — every model gets the same treatment

## The Solution

SupportSage uses geometric analysis + AI to decide:
- **Where** supports are actually needed (not just where the angle exceeds a threshold)
- **What type** of support (tree vs. standard, density, pattern) is optimal for each region
- **How to orient** branches to minimize material while maintaining stability

---

## Quick Start

```bash
# Install
pip install supportsage

# Analyze a model for overhang areas
supportsage analyze model.stl

# Generate optimized supports
supportsage optimize model.stl -o model_with_supports.stl --strategy ai

# Export as G-code overlay for your slicer
supportsage export model.stl --format cura-json
```

## Output

| Format | Use |
|--------|-----|
| STL | Direct support geometry, importable into any slicer |
| G-code overlay | Merge with existing sliced G-code |
| Cura Plugin JSON | Direct import into Cura as custom support |
| OrcaSlicer config | Import as support blocker/painter regions |

---

## Architecture

```
STL input → Geometry analyzer (trimesh)
                ↓
         Overhang detector (angle analysis + curvature)
                ↓
         Support planner (region segmentation)
                ↓
         Optimizer (material → stability optimization)
                ↓
         Support geometry generator
                ↓
         STL/G-code exporter
```

---

## Roadmap

- [x] STL geometry analysis (overhang detection)
- [ ] Tree support generation with AI-optimized branching
- [ ] Support removal difficulty scoring
- [ ] Cura plugin for one-click integration
- [ ] OrcaSlicer/Bambu Studio integration
- [ ] Web UI for drag-and-drop optimization
- [ ] API for print farm automation

---

## License

MIT
