import argparse
import sys
import os
from src.core.image_stripper import ImageStripper
from src.core.psd_cleaner import PSDCleaner
from src.utils.logger import logger

def main():
    print(r"""
    =========================================================
      ____  _           _        _                 
     |  _ \| |__   ___ | |_ ___ | |__   ___  _ __  
     | |_) | '_ \ / _ \| __/ _ \| '_ \ / _ \| '_ \ 
     |  __/| | | | (_) | || (_) | | | | (_) | |_) |
     |_|   |_| |_|\___/ \__\___/|_| |_|\___/| .__/ 
                                            |_|    
       Image Anti-Forensics - Clean Photoshop Traces
    =========================================================
    """)

    parser = argparse.ArgumentParser(description="Securely strip metadata and Photoshop traces from images and PSDs.")
    parser.add_argument('input_file', type=str, help='Path to the image or PSD file to clean.')
    parser.add_argument('-o', '--output', type=str, help='Path to save the cleaned file.')
    parser.add_argument('--donor', type=str, metavar='FILE', help='Advanced: Path to an authentic image to STEAL its EXIF and Quantization Tables (DQT) to bypass Double Compression.')

    args = parser.parse_args()
    input_file = args.input_file
    output_file = args.output
    donor_file = args.donor

    if not os.path.exists(input_file):
        print(f"[-] Error: Input file '{input_file}' does not exist.")
        sys.exit(1)

    ext = input_file.lower().split('.')[-1]

    if ext in ['jpg', 'jpeg', 'png']:
        print(f"[*] Processing Standard Image format ({ext.upper()})...")
        stripper = ImageStripper(input_file)
        
        if donor_file:
            print(f"[*] Identity Cloning Strategy Selected...")
            result = stripper.clone_identity(donor_file, output_file)
        else:
            print(f"[*] Deep Wash Strategy Selected (Default Process)...")
            result = stripper.deep_wash(output_file)
            
        if result:
            print("[+] Done.")
        else:
            print("[-] Task failed.")

    elif ext == 'psd':
        print(f"[*] Processing Photoshop Document (PSD)...")
        print("[!] Note: PSDs will be flattened into sterile PNG images for maximum security.")
        cleaner = PSDCleaner(input_file)
        result = cleaner.create_clean_psd(output_file)
        if result:
            print("[+] Done.")
        else:
            print("[-] Task failed.")
    else:
        print(f"[-] Error: Unsupported file extension '.{ext}'. Supported formats: jpg, png, psd.")
        sys.exit(1)

if __name__ == "__main__":
    main()
