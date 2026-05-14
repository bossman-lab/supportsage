---
title: "SupportSage Now Has a Desktop GUI and Cura Plugin — No CLI Required"
description: "Drag, drop, and generate optimized supports from your browser. Plus: one-click Cura integration for the two million users who don't touch a terminal."
published: false
tags: 3dprinting, python, cura, showdev
---

When I released SupportSage two weeks ago, the feedback was clear: "This is great, but I don't use the command line."

I don't blame them. There are roughly 20 million 3D printers out there, and maybe 10% of their owners are comfortable with a terminal. The other 90% just want to drag an STL onto something and see results.

So this week I built two things that close that gap:

1. **A desktop GUI** — open `http://localhost:5000`, drop your STL, and generate optimized supports without touching the command line
2. **A Cura plugin** — analyze and optimize directly inside the slicer you already use

Here's how they work.

## Desktop GUI: Drop-and-Drop Overhang Analysis

The GUI wraps the entire SupportSage CLI in a local web server. You install it with one pip command, then interact through your browser:

```bash
pip install supportsage  # or install from wheel
supportsage-gui --open
# → Opens http://localhost:5000
```

The interface is the same Three.js-powered 3D viewer from the web demo, but with two critical additions:

**1. Backend integration.** When you drop an STL, the browser sends it to a local Python server that runs the full SupportSage analysis. This means you get real CLI-grade calculations — face normals, BFS island detection, volume estimates — not just the browser approximation.

**2. One-click support generation.** Hit "Generate Tree Supports" and the backend runs `supportsage tree` with the strategy you chose (light / balanced / heavy). The result comes back as a downloadable STL you can load directly into any slicer.

The architecture is simple:

```
Browser (Three.js) ←→ Local Python Server ←→ supportsage CLI
     ↕                     ↕                    ↕
  3D view              API endpoints        Geometry engine
  Drop STL             /api/analyze         Tree supports
  Color overlay        /api/optimize        Pillar supports
  Stats panel          /api/version         JSON export
```

Everything runs locally. No data leaves your machine. No cloud dependency.

## Cura Plugin: Optimize From Inside Your Slicer

The Cura plugin is the bigger deal for everyday users. It adds a "SupportSage" menu to Cura with three commands:

- **Run SupportSage on Model...** — Picks up the STL you have loaded, runs the CLI analysis, and applies optimized support settings automatically
- **Load Strategy...** — Opens a pre-exported SupportSage JSON strategy
- **Clear SupportSage Settings** — Resets everything to defaults

The plugin detects the CLI at startup and gracefully degrades if it's not installed:

```bash
# Install CLI + plugin
pip install supportsage
cp -r cura_plugin ~/.local/share/cura/5.x/plugins/
# Restart Cura → Extensions → SupportSage → Run on Model...
```

When you run it, the plugin:
1. Calls `supportsage analyze` on your STL
2. Sets support type (tree vs standard), angle threshold, interface layers
3. Adjusts infill density based on the strategy (light=5%, balanced=12%, heavy=20%)
4. Applies support blockers where the analysis says no support is needed
5. Shows a summary: island count, estimated volume, material savings

## Why Desktop GUI Beats Cloud

I deliberately avoided building a web service. The GUI runs locally because:

- **Your files never upload** — some models are proprietary or unreleased
- **Zero hosting cost** — no server to maintain
- **Offline-first** — works without internet
- **Full CLI power** — the GUI is a UI on top of the actual engine, not a simplified approximation

The trade-off is you need Python installed. But for the target audience (print farms, engineering workshops, serious hobbyists), Python is already on their machine.

## What This Means

The browser-based web demo got 80% of the feedback I needed. The GUI and plugin handle the other 20% — the "I want a button, not a command."

The Cura plugin in particular unlocks the largest user base: Cura has ~2 million active users, and most of them have never typed `pip install` anything. They just want better supports.

## Try It

```bash
# Install
git clone https://github.com/bossman-lab/supportsage
cd supportsage && pip install -e .

# Launch GUI
supportsage-gui --open

# Or install Cura plugin
bash cura_plugin/install.sh
```

Or just use the web demo: **bossman-lab.github.io/supportsage**

Full repo: [github.com/bossman-lab/supportsage](https://github.com/bossman-lab/supportsage)

---

*Built with Python, Three.js, and the conviction that great tools should be accessible without a terminal.*
