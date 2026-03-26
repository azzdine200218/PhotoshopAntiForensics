from PIL import Image
import piexif

def create_donor_image():
    # 1. Create a fake "Original Photo" from a camera
    img = Image.new('RGB', (100, 100), color = 'blue')
    
    # 2. Add rich EXIF mimicking a real camera (e.g. Nikon D850)
    exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
    
    # Make Model
    exif_dict["0th"][piexif.ImageIFD.Make] = b"NIKON CORPORATION"
    exif_dict["0th"][piexif.ImageIFD.Model] = b"NIKON D850"
    exif_dict["0th"][piexif.ImageIFD.Software] = b"Ver.1.10" # Internal Camera software
    exif_dict["0th"][piexif.ImageIFD.DateTime] = b"2023:01:01 12:00:00"
    
    exif_bytes = piexif.dump(exif_dict)
    
    # Save with specific quantization tables (q=80 for testing a non-standard pillow default)
    img.save("test_donor.jpg", format='JPEG', quality=80, exif=exif_bytes)
    print("[+] Created authentic camera donor image: 'test_donor.jpg'")

def create_doctored_image():
    # A fake "Doctored" photo by Photoshop
    img = Image.new('RGB', (100, 100), color = 'red')
    exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
    exif_dict["0th"][piexif.ImageIFD.Make] = b"Apple"
    exif_dict["0th"][piexif.ImageIFD.Software] = b"Adobe Photoshop CC 2019"
    exif_bytes = piexif.dump(exif_dict)
    
    img.save("test_doctored.jpg", format='JPEG', quality=95, exif=exif_bytes)
    print("[+] Created doctored image: 'test_doctored.jpg'")

if __name__ == "__main__":
    create_donor_image()
    create_doctored_image()
