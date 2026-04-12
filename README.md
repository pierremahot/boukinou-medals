# Bookinou 3D Medal Generator

This project automates the creation of 3D printable, multi-color custom medals based on SVG line artwork. It uses OpenSCAD and Python to handle the generation natively. 

## Features
- **Batch Processing**: Automatically reads all SVG files in the `svg/` directory.
- **Smart Generation**: Only generates medals that haven't been generated yet (use `--force` to re-generate). 
- **Auto-Sanitization**: Automatically strips out incompatible SVG elements (like transparent boundary boxes) to prevent OpenSCAD from generating solid unprintable blobs.
- **Auto-Healing**: Applies microscopic topology fixes during OpenSCAD rendering to organically repair unclosed and self-intersecting Inkscape vectors.
- **Multi-Color Splitting**: Automatically exports `_front`, `_back`, `_front_base`, and `_front_drawing` variations to allow extremely easy multi-color 3D printing in modern slicing parameter logic.

## Directory Structure
- `svg/`: Place all of your Inkscape/Illustrator `.svg` files here.
  - `dummy.svg` is included as an example.
- `generated/`: Output directory structure where `.stl` models are automatically organized. Each SVG file gets its own cleanly named subfolder!

## How to Prepare Your Vector Files (SVGs)
1. Ensure your drawing rests safely inside a roughly matching `86x86mm` boundary.
2. In Inkscape (or illustrator), make sure to convert all thick native drawn strokes to physical closed fill shapes (e.g. `Path -> Stroke to Path` in Inkscape). OpenSCAD only responds to physical geometry.
3. Because the `bookinou.scad` library naturally adds the raised border boundary, you should not add physical geometric circles serving as boundaries yourself, as it could conflict. (The pipeline currently automatically attempts to scrub these out for you anyway).

## How to Run
Requirement: You must have Python 3 and OpenSCAD installed on your system.
Just execute the Python script:

```bash
# Standard generation
python3 generate_medal.py

# Force regeneration of everything
python3 generate_medal.py --force
```

## How to Print Multi-Color using Anycubic Slicer Next (or OrcaSlicer / PrusaSlicer)
If you want the base and the drawing to be different colors:
1. Open your slicer and drag/drop **both** the `[Name]_front_base.stl` and `[Name]_front_drawing.stl` files together onto the buildplate.
2. The slicer will ask: _"These files seem to be part of a multi-part object, load as a single object with multiple parts?"_ -> **Click Yes.**
3. Look at your object view list on the sidebar pane. Select the `_front_drawing` subcomponent and assign it your secondary extruder filament. 
4. Hit Slice! Both the line-drawing **and** the circular border will perfectly print in the new color.
