import os
from PIL import Image

# Define the directory containing the PNG files
path = '/Users/Bi/Documents/ImageData/AquaINFRA'

# List to hold frames
frames = []

# Iterate over sorted files in the directory
for filename in sorted(os.listdir(path)):
    if filename.endswith("_owt.png"):
        # Construct the full file path
        file_path = os.path.join(path, filename)
        
        # Open the image file and append to the list of frames
        with Image.open(file_path) as img:
            frames.append(img.copy())

# Save the frames as an animated GIF
if frames:
    # Save the first frame as a GIF with additional frames appended
    gif_path = os.path.join(path, 'animated.gif')
    frames[0].save(gif_path, format='GIF', append_images=frames[1:], save_all=True, duration=200, loop=0)
    print("Animated GIF created successfully.")
else:
    print("No PNG files found to create an animation.")
