import numpy as np
from PIL import Image, ImageFilter
from src.utils.logger import logger

class PRNUForger:
    @staticmethod
    def _extract_noise_residual(img_array):
        """
        Extracts the high-frequency sensor noise (PRNU pattern approximation)
        by subtracting a denoised version of the image from the original.
        """
        # Convert array back to PIL to apply Pillow's optimized filters
        img = Image.fromarray(img_array, 'RGB')
        
        # Apply median filter to remove noise while preserving edges
        # This isolates the underlying image content from the sensor noise
        denoised = img.filter(ImageFilter.MedianFilter(size=3))
        denoised_array = np.array(denoised, dtype=np.float32)
        original_array = np.array(img, dtype=np.float32)
        
        # The residual is the pure sensor fingerprint (+ any JPEG blocking)
        noise_residual = original_array - denoised_array
        return noise_residual

    @staticmethod
    def clone_fingerprint(target_img, donor_img, intensity=0.7):
        """
        Extracts the exact physical silicon sensor fingerprint (PRNU) from the
        authentic donor camera image, and multiplicatively injects it into the
        forged target image.
        
        This defeats forensic tools that rely on comparing sensor noise patterns
        to verify if two images were taken by the exact same physical camera.
        """
        logger.info("   [+] Executing PRNU Sensor Fingerprint Forging...")
        
        target_array = np.array(target_img.convert('RGB'), dtype=np.float32)
        donor_array = np.array(donor_img.convert('RGB'))
        
        # Step 1: Extract true sensor noise pattern from the authentic donor
        logger.info("      -> Extracting silicon noise residual from donor camera...")
        donor_noise = PRNUForger._extract_noise_residual(donor_array)
        
        # PRNU is multiplicative in nature: the sensor imperfection scales with 
        # incoming pixel brightness (brighter areas show more pronounced PRNU).
        # We model this by evaluating the luminance of the target image.
        target_luminance = np.mean(target_array, axis=2, keepdims=True) / 255.0
        
        # We must tile or crop the donor noise to match the target image dimensions
        # because the forged image might be cropped or a different resolution.
        h, w, c = target_array.shape
        dh, dw, _ = donor_noise.shape
        
        # Tile the noise pattern if the target is larger than the donor
        # Or crop it if the target is smaller
        reps_h = int(np.ceil(h / dh))
        reps_w = int(np.ceil(w / dw))
        tiled_noise = np.tile(donor_noise, (reps_h, reps_w, 1))
        matched_noise = tiled_noise[:h, :w, :]
        
        # Step 2: Inject the extracted noise into the targeted image
        logger.info("      -> Injecting multiplicative PRNU pattern into forged image...")
        
        # Scale noise intensity based on target luminance
        adaptive_noise = matched_noise * target_luminance * intensity
        
        # Add the sensor pattern
        forged_array = target_array + adaptive_noise
        
        # Clip and convert back
        forged_array = np.clip(forged_array, 0, 255).astype(np.uint8)
        
        logger.info("   [+] PRNU Cloning complete.")
        return Image.fromarray(forged_array, 'RGB')
