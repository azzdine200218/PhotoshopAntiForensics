import os
from PIL import Image, ImageFilter
import piexif
import numpy as np
import io
from src.utils.logger import logger
from src.core.ghost_evasion import GhostEvasion
from src.core.dct_manipulator import DCTManipulator
from src.core.histogram_matcher import HistogramMatcher
from src.core.copy_move_defender import CopyMoveDefender
from src.core.prnu_forger import PRNUForger

class ImageStripper:
    def __init__(self, input_path):
        self.input_path = input_path
        
    def _is_supported_format(self):
        ext = self.input_path.lower().split('.')[-1]
        return ext in ['jpg', 'jpeg', 'png']

    def deep_wash(self, output_path=None, noise_intensity=2, blur_radius=0.3):
        """
        Deep Wash Strategy (Advanced Anti-Forensics):
        1. Read Image and drop metadata (Standard Wash).
        2. Micro-Noise Injection: Adds a very slight, randomized Gaussian Noise matrix 
           to the pixel values. This completely destroys any mathematically identical blocks
           created by the Clone Stamp Tool or Healing Brush.
        3. CFA Pattern Destruction & ELA Equilization: Applies a microscopic Gaussian Blur
           and then forces a uniform re-compression when saving. This normalizes Error 
           Level Analysis (ELA) across the entire image and breaks Bayer Filter inconsistencies.
        """
        if not os.path.exists(self.input_path):
            logger.error(f"[-] Error: File not found: {self.input_path}")
            return None

        if output_path is None:
            name, ext = os.path.splitext(self.input_path)
            output_path = f"{name}_deepwash{ext}"

        logger.info("[*] Initiating Deep Wash (Anti-Forensics mode)...")
        try:
            with Image.open(self.input_path) as img:
                # 1. Ensure working with RGB mode for mathematical operations
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                logger.info(f"   [+] Image loaded. Applying Micro-Blur (Radius: {blur_radius})...")
                # 2. Apply a microscopic blur to blend compression artifacts and disrupt CFA
                blurred_img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
                
                # 3. Convert image to NumPy array for fast math manipulation
                img_array = np.array(blurred_img, dtype=np.int16)
                
                logger.info(f"   [+] Injecting randomized Micro-Noise (Intensity: {noise_intensity})...")
                # 4. Generate random Gaussian noise with the specified intensity (variance)
                noise = np.random.normal(0, noise_intensity, img_array.shape)
                
                # 5. Add noise, breaking mathematical identicality from Clone Stamps
                noisy_array = img_array + noise
                
                # 6. Clip values to valid RGB range [0, 255] and convert back to uint8
                noisy_array = np.clip(noisy_array, 0, 255).astype(np.uint8)
                
                # 7. Convert back to Pillow Image
                intermediate_img = Image.fromarray(noisy_array, 'RGB')
                
                # Apply Phase 2 & 5 Advanced Anti-Forensics
                intermediate_img = CopyMoveDefender.disrupt_keypoints(intermediate_img)
                intermediate_img = GhostEvasion.apply(intermediate_img, base_quality=95)
                final_img = DCTManipulator.normalize_coefficients(intermediate_img)
                
                logger.info(f"   [+] Equalizing compression and stripping metadata (Saving as JPG)...")
                # 8. Save the final image. 
                # - Using a fixed quality (e.g., 95) uniformly recompresses the whole image,
                #   which normalizes ELA across the doctored and original regions.
                # - Skipping 'exif' drops all metadata.
                final_img.save(output_path, format='JPEG', quality=95)
                
            logger.info(f"[+] Deep Wash successful! Sterile file saved to: {output_path}")
            logger.info(f"[+] -> ELA Normalization: OK | JPEG Ghost Evasion: OK | DCT Manipulation: OK")
            return output_path
            
        except Exception as e:
            logger.error(f"[-] An error occurred during Deep Wash: {str(e)}")
            return None

    def clone_identity(self, donor_path, output_path=None):
        """
        Advanced Anti-Forensics - The Donor Image Strategy:
        This function takes a 'Donor Image' (an authentic, unedited photograph straight 
        from the camera) and clones its physical and digital identity into the modified image.
        
        1. Copies the exact EXIF metadata structure (Camera Model, Dates, GPS).
        2. Clones the Quantization Tables (DQT) of the JPEG. This defeats 'Double Compression'
           and 'Library Save' detections, making the image appear as if it was intrinsically 
           compressed by the camera's original firmware rather than a software library.
        """
        if not os.path.exists(self.input_path):
            logger.error(f"[-] Error: Target file not found: {self.input_path}")
            return None
            
        if not os.path.exists(donor_path):
            logger.error(f"[-] Error: Donor file not found: {donor_path}")
            return None

        if output_path is None:
            name, ext = os.path.splitext(self.input_path)
            output_path = f"{name}_cloned{ext}"

        logger.info(f"[*] Initiating Identity Cloning... Donor: {donor_path}")
        try:
            # Open the authentic donor image to extract its properties
            with Image.open(donor_path) as donor_img:
                if donor_img.format != 'JPEG':
                    logger.error("[-] Error: Donor image MUST be a JPEG to extract Q-Tables and EXIF.")
                    return None
                    
                # Extract Quantization tables
                dqt = getattr(donor_img, 'quantization', None)
                if not dqt:
                    logger.warning("[-] Warning: Failed to extract Q-Tables from donor. Might be stripped.")
                else:
                    logger.info(f"   [+] Successfully extracted Quantization Tables (DQT) from donor.")

                # Extract EXIF metadata
                donor_exif = donor_img.info.get('exif')
                if not donor_exif:
                    logger.warning("[-] Warning: No EXIF data found in donor image.")
                else:
                    logger.info(f"   [+] Successfully extracted EXIF payload from donor.")
                    
                # Cache RGB representation of donor for histogram matching
                donor_rgb = donor_img.convert('RGB')

            # Now, open our doctored/modified image
            with Image.open(self.input_path) as target_img:
                if target_img.mode != 'RGB':
                    target_img = target_img.convert('RGB')
                    
                logger.info(f"   [+] Preparing forged image... Applying Tier-1 Evasion Tactics...")
                
                # --- 1. Affine Regridding (BAG Destruction) ---
                logger.info(f"   [+] Executing Affine Transformation to destroy Block Artifact Grid (BAG)...")
                # A micro-rotation forces a complete recalculation of the 8x8 JPEG grid
                target_img = target_img.rotate(0.01, resample=Image.BICUBIC, expand=False)
                # Crop 1 pixel off edges to remove rotation artifacts
                w, h = target_img.size
                target_img = target_img.crop((1, 1, w-1, h-1))
                
                # --- 2. Deep Wash Physical Obfuscation (ELA & Clone Stamp destruction) ---
                logger.info(f"   [+] Applying Micro-Blur and Numpy Noise...")
                blur_radius = 0.3
                noise_intensity = 2
                
                blurred_img = target_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
                img_array = np.array(blurred_img, dtype=np.int16)
                noise = np.random.normal(0, noise_intensity, img_array.shape)
                noisy_array = img_array + noise
                noisy_array = np.clip(noisy_array, 0, 255).astype(np.uint8)
                
                forged_clean = Image.fromarray(noisy_array, 'RGB')
                
                # --- Phase 2, 5 & 6: Advanced Anti-Forensics & Profile Matching ---
                forged_clean = HistogramMatcher.exact_match(forged_clean, donor_rgb)
                forged_clean = CopyMoveDefender.disrupt_keypoints(forged_clean)
                forged_clean = PRNUForger.clone_fingerprint(forged_clean, donor_rgb)
                forged_clean = GhostEvasion.apply(forged_clean, base_quality=95)
                forged_clean = DCTManipulator.normalize_coefficients(forged_clean)
                
                # --- 3. Semantic EXIF Parsing (Thumbnail Replacement) ---
                final_exif = None
                if donor_exif:
                    logger.info(f"   [+] Parsing Donor EXIF for Semantic Injection...")
                    try:
                        exif_dict = piexif.load(donor_exif)
                        
                        # Generate a new thumbnail from our forged image
                        thumb_io = io.BytesIO()
                        # Thumbnails are usually 160x160 max in EXIF
                        thumb_img = forged_clean.copy()
                        thumb_img.thumbnail((160, 160), Image.LANCZOS)
                        thumb_img.save(thumb_io, format="JPEG", quality=75)
                        
                        # Replace the donor's thumbnail with our new forged thumbnail
                        exif_dict["thumbnail"] = thumb_io.getvalue()
                        logger.info(f"   [+] Forged Thumbnail injected into Donor's EXIF payload.")
                        
                        final_exif = piexif.dump(exif_dict)
                    except Exception as e:
                        logger.warning(f"   [-] Warning: Failed to parse/modify donor EXIF thumbnail: {e}")
                        final_exif = donor_exif # Fallback to raw copy if parsing fails
                        
                logger.info(f"   [+] Forgery Complete. Injecting Final Donor Identity (Q-Tables)...")
                
                # Save the forged image but INJECT the donor's identity (Exif + Q-Tables)
                save_kwargs = {'format': 'JPEG'}
                if dqt:
                    save_kwargs['qtables'] = dqt
                if final_exif:
                    save_kwargs['exif'] = final_exif
                # If we use donor qtables, quality parameter is generally ignored/overridden by qtables
                # but we set subsampling to match standard high-quality camera outputs (4:4:4)
                save_kwargs['subsampling'] = 0 
                
                forged_clean.save(output_path, **save_kwargs)
                logger.info(f"[+] Identity Clone successful! File saved to: {output_path}")
                logger.info(f"[+] -> EXIF Cloned: {'Yes' if donor_exif else 'No'} | Q-Tables Cloned: {'Yes' if dqt else 'No'}")
                return output_path
                
        except Exception as e:
            logger.error(f"[-] An error occurred during Identity Cloning: {str(e)}")
            return None

