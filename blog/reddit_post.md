Hey r/3Dprinting 👋

I got tired of watching 35% of my filament go into support waste, so I built **SupportSage** — an open-source CLI tool that analyzes STL geometry and generates **AI-optimized tree supports**.

Here's the short version of how it works:

1. **Overhang severity grading** — not all overhangs need the same support. Critical (+120°) gets dense, borderline (45-70°) gets minimal. Traditional slicers treat every overhang the same.
2. **Island detection** — finds disconnected overhang regions via BFS. A bridge span only needs supports at the ends, not the whole 30mm gap.
3. **Tree support generation** — samples support points from each island, grows branching organic structures down to the build plate, merges nearby trunks to save material.

The code is pure Python + trimesh + numpy — no GPU, no heavy ML dependencies.

**Repo**: [github.com/bossman-lab/supportsage](https://github.com/bossman-lab/supportsage)

```bash
# Analyze your STL
supportsage analyze model.stl

# Generate tree supports
supportsage tree model.stl -o optimized.stl --strategy balanced
```

The technical deep-dive is on dev.to if you want the full story: [link](https://dev.to/lanternproton/i-built-an-ai-that-slices-your-3d-printing-support-waste-by-40-2hg)

I'm building this in public — would love feedback, STL torture tests, or PRs. What's the worst overhang problem you've dealt with?
