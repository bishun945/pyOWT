import os
import glob
from PIL import Image, ImageDraw, ImageFont

# Define the directory containing the PNG files
path_root = "/Users/Bi/koflux/feederdata2/EighteenTB05/AquaINFRA/"
month_dir = ["onns_06-2023", "onns_07-2023", "onns_08-2023", "onns_09-2023"]

files_all = []

for month in month_dir:
    path = os.path.join(path_root, month, "owt_results/")
    # files_all.extend(glob.glob(os.path.join(path, "*_owt.png")))
    files_all.extend(glob.glob(os.path.join(path, "*_rgb.png")))

files_all.sort()

# List to hold frames
frames = []

# Optional: Load a font, or use default
try:
    font = ImageFont.truetype("/System/Library/Fonts/Times.ttc", 60)
except IOError:
    font = ImageFont.load_default()

# Process each file
for file_path in files_all:
    # Extract filename from the full path
    filename = os.path.basename(file_path)[16:31]

    # Open the image file
    with Image.open(file_path) as img:
        # Create a drawing context
        draw = ImageDraw.Draw(img)
        
        # Position for the text can be adjusted
        text_position = (1000, 1060)  # Top-left corner of the image
        
        # Draw the filename onto the image
        draw.text(text_position, filename, font=font, fill="white")
        
        # Append the modified frame
        frames.append(img.copy())

# Save the frames as an animated GIF
if frames:
    # Define the path for the animated GIF
    # gif_path = os.path.join(path_root, 'owt_animated.gif')
    gif_path = os.path.join(path_root, 'rgb_animated.gif')
    # Save the first frame as a GIF with additional frames appended
    frames[0].save(gif_path, format='GIF', append_images=frames[1:], save_all=True, duration=200, loop=0)
    print("Animated GIF with filenames created successfully.")
else:
    print("No PNG files found to create an animation.")