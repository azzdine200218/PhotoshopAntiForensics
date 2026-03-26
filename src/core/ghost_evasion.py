import numpy as np
from PIL import Image
import io
from src.utils.logger import logger

class GhostEvasion:
    @staticmethod
    def apply(img, base_quality=90):
        """
        JPEG Ghost Evasion via Block-Level Requantization Normalization.
        
        Unlike global blur+noise (which deep_wash already does), this operates
        on JPEG's fundamental 8x8 block structure:
        
        1. Splits the image into 8x8 pixel blocks (the JPEG DCT grid).
        2. For each block, applies a micro-perturbation scaled to the block's
           local variance — high-detail blocks get more noise, flat blocks less.
        3. Performs an in-memory JPEG round-trip at the target quality to force
           uniform requantization, eliminating ghost differentials between
           previously-compressed and freshly-edited regions.
        
        This specifically targets JPEG Ghost analysis tools which detect
        quality-level mismatches between image regions.
        """
        logger.info(f"   [+] Applying Block-Level JPEG Ghost Evasion (Target Q={base_quality})...")
        
        img_array = np.array(img, dtype=np.float64)
        h, w, c = img_array.shape
        
        # Pad to exact 8x8 block boundaries
        pad_h = (8 - h % 8) % 8
        pad_w = (8 - w % 8) % 8
        if pad_h or pad_w:
            img_array = np.pad(img_array, ((0, pad_h), (0, pad_w), (0, 0)), mode='reflect')
        
        padded_h, padded_w, _ = img_array.shape
        
        # Process each 8x8 block independently
        for by in range(0, padded_h, 8):
            for bx in range(0, padded_w, 8):
                block = img_array[by:by+8, bx:bx+8, :]
                
                # Adaptive noise: scale to local block variance
                # High-variance (textured) blocks tolerate more noise
                # Low-variance (flat) blocks need less to avoid visible artifacts
                local_std = np.std(block)
                noise_scale = max(0.3, min(local_std * 0.05, 2.0))
                
                noise = np.random.normal(0, noise_scale, block.shape)
                img_array[by:by+8, bx:bx+8, :] = block + noise
        
        # Remove padding
        img_array = img_array[:h, :w, :]
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        
        result_img = Image.fromarray(img_array, 'RGB')
        
        # In-memory JPEG round-trip at target quality to force uniform requantization
        # This is the key step: it ensures ALL blocks share the same quantization tables,
        # eliminating the quality-level differential that JPEG Ghost detects
        logger.info(f"   [+] Performing uniform requantization round-trip (Q={base_quality})...")
        buffer = io.BytesIO()
        result_img.save(buffer, format='JPEG', quality=base_quality, subsampling=0)
        buffer.seek(0)
        result_img = Image.open(buffer).copy()
        buffer.close()
        
        return result_img
