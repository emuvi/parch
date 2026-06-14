import os
from PIL import Image

def convert_png_to_jpg():
    directory = "."
    for filename in os.listdir(directory):
        if filename.lower().endswith(".png"):
            png_path = os.path.join(directory, filename)
            jpg_filename = os.path.splitext(filename)[0] + ".jpg"
            jpg_path = os.path.join(directory, jpg_filename)

            try:
                # Open the image
                img = Image.open(png_path)
                
                # Convert to RGB, as JPEG doesn't support alpha channel (transparency)
                rgb_im = img.convert('RGB')
                
                # Save as JPG
                rgb_im.save(jpg_path, quality=95)
                print(f"Converted: {filename} -> {jpg_filename}")
            except Exception as e:
                print(f"Failed to convert {filename}: {e}")

if __name__ == "__main__":
    convert_png_to_jpg()
