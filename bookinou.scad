part = "front"; // Overridden by CLI
svg_file = "dummy.svg"; // Overridden by CLI
svg_name_text = "dummy"; // Overridden by CLI

// Global Parameters
svg_scale = 1.0; // Overridden by CLI
diameter = 86;
radius = diameter / 2;

// Front Half Parameters
front_base_thickness = 1.0; // 5 layers at 0.2mm (was 0.4)
extrusion_height = 0.6; // 3 layers at 0.2mm
border_thickness = 2; // 2mm wide raised border

// Back Half Parameters
back_base_thickness = 1.6; // 8 layers at 0.2mm (was 1.0)
cutout_diameter = 39;
cutout_radius = cutout_diameter / 2;
cutout_depth = 0.4; // 2 layers at 0.2mm
text_depth = 0.6; // 3 layers at 0.2mm
font_size = 5;

// Rendering Smoothness
$fn = 120;

module circular_text(txt, r, font_size, angle_spread) {
    n = len(txt);
    if (n > 0) {
        step = n > 1 ? angle_spread / (n - 1) : 0;
        start_angle = angle_spread / 2;
        for (i = [0 : n - 1]) {
            angle = start_angle - i * step;
            rotate([0, 0, angle])
            translate([0, r, 0])
            text(txt[i], size=font_size, halign="center", valign="center");
        }
    }
}

module front_base() {
    // Flat Base
    cylinder(h=front_base_thickness, r=radius);
}

module front_drawing() {
    // Raised Border Layer
    translate([0, 0, front_base_thickness]) {
        difference() {
            cylinder(h=extrusion_height, r=radius);
            // Slightly deeper cut for a clean subtraction
            translate([0, 0, -1]) 
                cylinder(h=extrusion_height + 2, r=radius - border_thickness);
        }
    }

    // Extruded SVG (Placed on top of the base layer)
    if (svg_file != "") {
         translate([0, 0, front_base_thickness]) {
             linear_extrude(height=extrusion_height) {
                 // Scale dynamically based on Python processing to fill the circle gracefully
                 scale([svg_scale, svg_scale])
                     // Add a microscopic offset to automatically fix unclosed/self-intersecting paths inside the SVG during CGAL conversion
                     // We use a default delta of 0.2mm to artificially thicken the lines, ensuring they are comfortably printable with a standard 0.4mm 3D printer nozzle.
                     offset(delta=0.2) import(svg_file, center=true);
             }
         }
    }
}

if (part == "front") {
    union() {
        front_base();
        front_drawing();
    }
}

if (part == "front_base") {
    front_base();
}

if (part == "front_drawing") {
    front_drawing();
}

if (part == "back") {
    difference() {
        // Flat Base
        cylinder(h=back_base_thickness, r=radius);
        
        // Cutout for sticker on the "inner"/front side (Z = back_base_thickness - cutout_depth upwards)
        translate([0, 0, back_base_thickness - cutout_depth]) {
            cylinder(h=cutout_depth + 1, r=cutout_radius);
        }
        
        // Engraved Circular Text on the flat back (Z = 0)
        // Cut upwards into the base
        translate([0, 0, -0.1]) {
            linear_extrude(height=text_depth + 0.1) {
                // Mirror horizontally so it reads correctly when looking directly at the flat bottom
                mirror([1, 0, 0]) {
                    // Top arc: "bookinou"
                    circular_text("bookinou", r=radius - 12, font_size=font_size, angle_spread=100);
                    
                    // Bottom arc: svg_name_text
                    // We rotate 180 degrees so it's at the bottom
                    rotate([0, 0, 180])
                        // Note: Because it's at the bottom, pointing away from center, the text will be "upside down" relative to the whole model's UP,
                        // which is correct for reading it sequentially when rotating the medal.
                        circular_text(svg_name_text, r=radius - 12, font_size=font_size, angle_spread=min(120, len(svg_name_text) * 12));
                }
            }
        }
    }
}
