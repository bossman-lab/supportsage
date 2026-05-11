# SupportSage Cura Plugin

Load SupportSage optimized support strategies directly into Cura.

## Installation

1. Copy the entire `SupportSagePlugin` folder to your Cura plugins directory:
   - Windows: `%APPDATA%\cura\[version]\plugins\`
   - macOS: `~/Library/Application Support/cura/[version]/plugins/`
   - Linux: `~/.local/share/cura/[version]/plugins/`

2. Restart Cura

3. Find it under: **Extensions → SupportSage**

## Usage

1. Run SupportSage on your STL:
   ```bash
   supportsage export model.stl -f cura-json -o strategy.json
   ```

2. In Cura: **Extensions → SupportSage → Load Strategy**

3. Select the `strategy.json` file

4. SupportSage applies optimized support settings:
   - Enables tree/organic supports where optimal
   - Sets support angles and interface layers
   - Adds support blockers where no support is needed

## Requirements

- Cura 5.x
