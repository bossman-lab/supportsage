# SupportSage Web Demo

🧠 **AI-optimized support structures for 3D printing**

Drag-and-drop an STL file to visualize overhangs and estimate material savings — all in your browser, no backend needed.

## How it works

1. Drop any `.stl` file onto the viewport
2. The model renders with **color-coded overhang severity**:
   - 🔴 Red = Critical (>120° from vertical)
   - 🟠 Orange = Moderate (70-120°)
   - 🟡 Yellow = Borderline (45-70°)  
   - 🟢 Green = Safe (<45°)
3. The panel shows face count, volume, support islands, and estimated material savings vs uniform supports
4. Rotate/zoom the model with mouse drag and scroll

## Tech

- Three.js for 3D rendering
- Pure client-side STL parsing and geometric analysis
- No backend, no uploads, no data leaves your browser
- Single HTML file, zero dependencies beyond the CDN

## Links

- **Live demo**: [bossman-lab.github.io/supportsage](https://bossman-lab.github.io/supportsage)
- **CLI tool**: [github.com/bossman-lab/supportsage](https://github.com/bossman-lab/supportsage)
- **Blog**: [dev.to/lanternproton](https://dev.to/lanternproton)
