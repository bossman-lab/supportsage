---
title: "I Built a Browser-Based 3D Print Overhang Analyzer — No Backend, No Uploads"
description: "Drag-and-drop an STL file, see overhangs color-coded in real time, and estimate material savings — all client-side with Three.js."
published: false
tags: webdev, 3dprinting, javascript, showdev
---

Last week I released SupportSage, a CLI tool that analyzes STL geometry and generates optimized support structures. The response was great, but there was a recurring question: "Can I try it without installing anything?"

So I built a **browser-based version**. Drop an STL file into the viewport and see the overhang analysis immediately — color-coded, interactive, and fully client-side.

## What It Does

The web demo takes your STL file and:

1. **Parses it entirely in your browser** — binary and ASCII STL both supported
2. **Computes face normals** and classifies each face by overhang severity
3. **Color-codes the model** so you can see at a glance where supports are needed:
   - 🔴 **Red** = Critical overhang (>120° from vertical)
   - 🟠 **Orange** = Moderate (70-120°)
   - 🟡 **Yellow** = Borderline (45-70°)
   - 🟢 **Green** = Safe (no support needed)
4. **Runs island detection** — finds disconnected overhang regions
5. **Estimates material savings** vs traditional uniform support
6. **Lets you inspect from any angle** — rotate, pan, zoom

All of this happens in your browser. No file uploads, no backend, no data leaves your machine.

## The Tech

The stack is refreshingly simple:

- **[Three.js](https://threejs.org/)** for 3D rendering
- **[OrbitControls](https://threejs.org/docs/#examples/en/controls/OrbitControls)** for interactive camera control
- **Custom STL parser** — reads binary and ASCII STL files
- **Direct geometry analysis** — face normals, BFS island detection, volume estimates
- **Single HTML file**, ~27KB, zero build step

The interesting part is that the overhang analysis logic is the same algorithm I wrote for the Python CLI — just ported to JavaScript. The core is the dot product between each face normal and the Z-up vector:

```javascript
// Face normal vs build direction (Z-up)
const dot = faceNormalZ;  // dot product with (0,0,1)

if (dot < -0.5) {
  severity = 'critical';      // >120° from vertical
  color = [1, 0.2, 0.2];     // 🔴 Red
} else if (dot < 0) {
  severity = 'moderate';      // 70-120°
  color = [1, 0.53, 0];      // 🟠 Orange  
} else if (dot < cos(45°)) {
  severity = 'borderline';    // 45-70°
  color = [1, 0.8, 0];       // 🟡 Yellow
} else {
  severity = 'safe';          // <45°
  color = [0.13, 0.8, 0.4];  // 🟢 Green
}
```

The island detection (finding disconnected overhang regions) uses a BFS over the face adjacency graph — the same approach as the CLI, running in JavaScript.

## Why No Backend

I considered setting up a Python backend that runs the actual SupportSage analysis, but there were two problems:

1. **I'd have to host it** — a server costs money, needs maintenance, and goes down
2. **Users would have to upload their STL files** — some models are proprietary or unreleased

A client-side approach solves both: it's free to serve (GitHub Pages), and your file never leaves your computer.

The trade-off is that the browser version only does **analysis and visualization** — it doesn't generate support geometry yet. That's the next iteration: WebAssembly port of the tree support generator.

## Try It

The demo is live (once I flip the GitHub Pages switch):

👉 **[bossman-lab.github.io/supportsage](https://bossman-lab.github.io/supportsage)**

Drag any STL file onto the viewport. Here's a quick test:

1. Download any STL from Printables or Thingiverse
2. Drop it on the page
3. Rotate the model to see the overhang coloring
4. Check the panel for island count and savings estimate

## What's Next

The browser demo is deliberately limited — analysis only, no support generation. The full CLI tool handles that. But it does something the CLI can't: **let you see the problem before you decide how to fix it.**

I'm considering a WebAssembly build of the tree support generator that would let you generate optimized supports directly in the browser. But for now, the web demo is the fastest way to answer the question "how much does my model really need?"

---

**Links:**
- Web demo: [bossman-lab.github.io/supportsage](https://bossman-lab.github.io/supportsage)
- CLI tool: [github.com/bossman-lab/supportsage](https://github.com/bossman-lab/supportsage)
- Previous posts: [dev.to/lanternproton](https://dev.to/lanternproton)
