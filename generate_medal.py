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

def run_openscad(exec_path, scad_file, output_stl, part, svg_file, svg_name):
    args = [
        exec_path,
        "-o", output_stl,
        "-D", f'part="{part}"',
        "-D", f'svg_file="{svg_file}"',
        "-D", f'svg_name_text="{svg_name}"',
        scad_file
    ]
    print(f"Generating {output_stl}...")
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(f"Failed to generate {output_stl}:")
        print(result.stderr.decode('utf-8'))
    else:
        print(f"Successfully created: {output_stl}")

def main():
    parser = argparse.ArgumentParser(description="Batch Generate Bookinou Medals.")
    parser.add_argument("-f", "--force", action="store_true", help="Force regeneration of all medals even if they already exist.")
    
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
    
    if not svg_files:
        print(f"No SVG files found in {svg_dir}.")
        return

    for svg_path in svg_files:
        svg_basename = os.path.basename(svg_path)
        svg_name, _ = os.path.splitext(svg_basename)
        
        # Output directory for this specific SVG
        outdir = os.path.join(generated_dir, svg_name)
        os.makedirs(outdir, exist_ok=True)
        
        # Expected outputs
        outputs = {
            "front": os.path.join(outdir, f"{svg_name}_front.stl"),
            "front_base": os.path.join(outdir, f"{svg_name}_front_base.stl"),
            "front_drawing": os.path.join(outdir, f"{svg_name}_front_drawing.stl"),
            "back": os.path.join(outdir, f"{svg_name}_back.stl")
        }
        
        # Check if we should skip
        if not args.force:
            if all(os.path.exists(path) for path in outputs.values()):
                print(f"Skipping {svg_name}: All files already exist. Use --force to regenerate.")
                continue
                
        print(f"--- Processing {svg_name} ---")
        
        # Sanitize SVG: remove bounding boxes that break OpenSCAD
        with open(svg_path, "r", encoding="utf-8") as f:
            svg_content = f.read()
        
        svg_content = re.sub(r'<circle[^>]*?(?:fill-opacity[:=][\'"]?0|fill[:=][\'"]?none[\'"]?|r=[\'"]4[0-9][\.\d]*[\'"])[^>]*?/>', '', svg_content, flags=re.IGNORECASE)
        
        sanitized_svg_path = os.path.join(sanitized_dir, f"{svg_name}_sanitized.svg")
        with open(sanitized_svg_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
        
        # Generate components natively
        run_openscad(openscad_cmd, scad_path, outputs["front"], "front", sanitized_svg_path, svg_name)
        run_openscad(openscad_cmd, scad_path, outputs["front_base"], "front_base", sanitized_svg_path, svg_name)
        run_openscad(openscad_cmd, scad_path, outputs["front_drawing"], "front_drawing", sanitized_svg_path, svg_name)
        run_openscad(openscad_cmd, scad_path, outputs["back"], "back", sanitized_svg_path, svg_name)

if __name__ == "__main__":
    main()
