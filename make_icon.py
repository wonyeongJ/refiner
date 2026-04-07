import os
from PIL import Image, ImageDraw

def create_gear_icon(file_path):
    # Create a 256x256 image with transparent background
    size = (256, 256)
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Gear colors (Dark theme compatible)
    gear_color = (230, 237, 243) # text_primary (white-ish)
    accent_color = (56, 139, 253) # accent_blue
    
    center = (128, 128)
    outer_radius = 100
    inner_radius = 65
    hole_radius = 35
    num_teeth = 8
    tooth_width = 40
    
    # Draw teeth
    import math
    for i in range(num_teeth):
        angle = math.radians(i * (360 / num_teeth))
        
        # Calculate tooth corners
        x1 = center[0] + (outer_radius + 20) * math.cos(angle - 0.2)
        y1 = center[1] + (outer_radius + 20) * math.sin(angle - 0.2)
        x2 = center[0] + (outer_radius + 20) * math.cos(angle + 0.2)
        y2 = center[1] + (outer_radius + 20) * math.sin(angle + 0.2)
        x3 = center[0] + (outer_radius - 10) * math.cos(angle + 0.3)
        y3 = center[1] + (outer_radius - 10) * math.sin(angle + 0.3)
        x4 = center[0] + (outer_radius - 10) * math.cos(angle - 0.3)
        y4 = center[1] + (outer_radius - 10) * math.sin(angle - 0.3)
        
        draw.polygon([(x1, y1), (x2, y2), (x3, y3), (x4, y4)], fill=gear_color)

    # Draw outer circle
    draw.ellipse([center[0]-outer_radius, center[1]-outer_radius, 
                  center[0]+outer_radius, center[1]+outer_radius], 
                 fill=gear_color)
    
    # Draw inner relief (accent)
    draw.ellipse([center[0]-inner_radius, center[1]-inner_radius, 
                  center[0]+inner_radius, center[1]+inner_radius], 
                 fill=accent_color)
                 
    # Draw center hole (transparent)
    draw.ellipse([center[0]-hole_radius, center[1]-hole_radius, 
                  center[0]+hole_radius, center[1]+hole_radius], 
                 fill=(0, 0, 0, 0))

    # Save as ICO with multiple sizes
    image.save(file_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Created high-res icon at {file_path}")

if __name__ == "__main__":
    icon_dir = "assets/images"
    if not os.path.exists(icon_dir):
        os.makedirs(icon_dir)
    create_gear_icon(os.path.join(icon_dir, "icon.ico"))
