import os
import sys
import argparse
import subprocess
import glob
import re

def check_openscad_installed():
    try:
        subprocess.run(["openscad", "-v"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return "openscad"
    except FileNotFoundError:
        windows_path = r"C:\Program Files\OpenSCAD\openscad.exe"
        if os.path.exists(windows_path):
            return windows_path
        print("Error: OpenSCAD executable not found.")
        print("Please ensure OpenSCAD is installed and 'openscad' is available in your system PATH,")
        print("or installed at 'C:\\Program Files\\OpenSCAD\\openscad.exe'.")
        sys.exit(1)

def run_openscad(exec_path, scad_file, output_stl, part, svg_file, svg_name, display_name, svg_scale, svg_w, svg_h):
    args = [
        exec_path,
        "-o", output_stl,
        "-D", f'part="{part}"',
        "-D", f'svg_file="{svg_file}"',
        "-D", f'svg_name_text="{display_name}"',
        "-D", f'svg_scale={svg_scale}',
        "-D", f'svg_width={svg_w}',
        "-D", f'svg_height={svg_h}',
        scad_file
    ]
    print(f"Generating {output_stl}...")
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(f"Failed to generate {output_stl}:")
        print(result.stderr.decode('utf-8'))
    else:
        print(f"Successfully created: {output_stl}")

def extract_svg_dimensions(svg_content):
    w, h = 86.0, 86.0
    
    # Try viewBox extraction first (format: min-x min-y width height)
    vb_match = re.search(r'viewBox=[\'"]([^\'"]+)[\'"]', svg_content, re.IGNORECASE)
    if vb_match:
        parts = vb_match.group(1).replace(",", " ").split()
        if len(parts) >= 4:
            try:
                w, h = float(parts[2]), float(parts[3])
                return w, h
            except ValueError:
                pass
                
    # If viewBox extraction failed, try explicit width/height
    w_match = re.search(r'<svg[^>]+width=[\'"]([\d\.]+)[a-zA-Z]*[\'"]', svg_content, re.IGNORECASE)
    h_match = re.search(r'<svg[^>]+height=[\'"]([\d\.]+)[a-zA-Z]*[\'"]', svg_content, re.IGNORECASE)
    if w_match and h_match:
        try:
            w = float(w_match.group(1))
            h = float(h_match.group(1))
            return w, h
        except ValueError:
            pass
            
    return w, h

def main():
    parser = argparse.ArgumentParser(description="Batch Generate Bookinou Medals.")
    parser.add_argument("-f", "--force", action="store_true", help="Force regeneration of all medals even if they already exist.")
    parser.add_argument("-s", "--select", nargs="+", help="List of specific SVG names to generate (e.g. -s La_Belle_et_le_Clochard or -s nemo.svg)")
    
    args = parser.parse_args()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    scad_path = os.path.join(base_dir, "bookinou.scad")
    if not os.path.isfile(scad_path):
        print("Error: bookinou.scad template not found in the same directory.")
        sys.exit(1)
        
    openscad_cmd = check_openscad_installed()
    
    svg_dir = os.path.join(base_dir, "svg")
    sanitized_dir = os.path.join(svg_dir, "sanitized")
    generated_dir = os.path.join(base_dir, "generated")
    
    os.makedirs(sanitized_dir, exist_ok=True)
    os.makedirs(generated_dir, exist_ok=True)
    
    # Process all svgs in the svg directory
    svg_files = [f for f in glob.glob(os.path.join(svg_dir, "*.svg")) if os.path.isfile(f)]
    
    if args.select:
        selected_names = [os.path.splitext(os.path.basename(name))[0] for name in args.select]
        svg_files = [f for f in svg_files if os.path.splitext(os.path.basename(f))[0] in selected_names]
        if not svg_files:
            print(f"None of the selected SVGs {selected_names} were found in {svg_dir}.")
            return

    if not svg_files:
        print(f"No SVG files found in {svg_dir}.")
        return

    for svg_path in svg_files:
        svg_basename = os.path.basename(svg_path)
        svg_name, _ = os.path.splitext(svg_basename)
        
        outdir = os.path.join(generated_dir, svg_name)
        os.makedirs(outdir, exist_ok=True)
        
        # Expected outputs (skip full front solo model to save generation time)
        outputs = {
            "front_base": os.path.join(outdir, f"{svg_name}_front_base.stl"),
            "front_drawing": os.path.join(outdir, f"{svg_name}_front_drawing.stl"),
            "back": os.path.join(outdir, f"{svg_name}_back.stl")
        }
        
        # Check if we should skip
        if not args.force:
            if all(os.path.exists(path) for path in outputs.values()):
                print(f"Skipping {svg_name}: All files already exist. Use --force to regenerate.")
                continue
                
        print(f"\n--- Processing {svg_name} ---")
        
        with open(svg_path, "r", encoding="utf-8") as f:
            svg_content = f.read()

        # Dynamic SVG Scale calculation
        # To perfectly fit the 86mm diameter medal base (matching original SVG scale). Target 86mm physical size
        svg_w, svg_h = extract_svg_dimensions(svg_content)
        max_dim = max(svg_w, svg_h)
        target_size = 83.0
        svg_scale = target_size / max_dim

        # Sanitize SVG: remove bounding boxes that break OpenSCAD
        svg_content = re.sub(r'<circle[^>]*?(?:fill-opacity[:=][\'"]?0|fill[:=][\'"]?none[\'"]?|r=[\'"]4[0-9][\.\d]*[\'"])[^>]*?/>', '', svg_content, flags=re.IGNORECASE)
        
        sanitized_svg_path = os.path.join(sanitized_dir, f"{svg_name}_sanitized.svg")
        with open(sanitized_svg_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        
        # Compute clean display string natively
        display_name = svg_name.replace("_", " ").replace("-", " ")
        
        # Generate components natively (ignoring combined 'front' model piece to optimize 30% execution time)
        run_openscad(openscad_cmd, scad_path, outputs["front_base"], "front_base", sanitized_svg_path, svg_name, display_name, svg_scale, svg_w, svg_h)
        run_openscad(openscad_cmd, scad_path, outputs["front_drawing"], "front_drawing", sanitized_svg_path, svg_name, display_name, svg_scale, svg_w, svg_h)
        run_openscad(openscad_cmd, scad_path, outputs["back"], "back", sanitized_svg_path, svg_name, display_name, svg_scale, svg_w, svg_h)

if __name__ == "__main__":
    main()
