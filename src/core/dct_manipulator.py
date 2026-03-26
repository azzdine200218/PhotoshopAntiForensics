import numpy as np
from PIL import Image
try:
    from scipy.fftpack import dct, idct
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
from src.utils.logger import logger

class DCTManipulator:
    @staticmethod
    def _dct2(block):
        return dct(dct(block.T, norm='ortho').T, norm='ortho')

    @staticmethod
    def _idct2(block):
        return idct(idct(block.T, norm='ortho').T, norm='ortho')

    @staticmethod
    def normalize_coefficients(img):
        """
        Normalizes DCT coefficients to disrupt First-Digit (Benford's Law)
        analysis often used to detect multiple compressions.
        
        [Updated] Now operates precisely on 8x8 generic JPEG blocks.
        """
        if not SCIPY_AVAILABLE:
            logger.info("   [-] scipy not installed. Skipping advanced DCT manipulation.")
            return img
            
        logger.info("   [+] Executing 8x8 Block-Level DCT Coefficient Normalization...")
        
        # Process luminance channel (Y) usually targeted for manipulation
        img_ycbcr = img.convert('YCbCr')
        y, cb, cr = img_ycbcr.split()
        
        y_array = np.array(y, dtype=np.float32)
        h, w = y_array.shape
        
        # Pad to 8x8 boundaries
        pad_h = (8 - h % 8) % 8
        pad_w = (8 - w % 8) % 8
        if pad_h or pad_w:
            y_array = np.pad(y_array, ((0, pad_h), (0, pad_w)), mode='reflect')
            
        padded_h, padded_w = y_array.shape
        
        # Iterate over all 8x8 blocks
        for by in range(0, padded_h, 8):
            for bx in range(0, padded_w, 8):
                block = y_array[by:by+8, bx:bx+8]
                
                # Apply 2D DCT on the 8x8 block
                dct_block = DCTManipulator._dct2(block)
                
                # Add micro-perturbations to AC components (skip 0,0)
                # This breaks statistical traces of prior block artifacts
                noise_mask = np.random.normal(0, 0.4, (8, 8))
                noise_mask[0, 0] = 0  # Protect the DC component (mean brightness)
                
                dct_block += noise_mask
                
                # Apply Inverse 2D DCT
                idct_block = DCTManipulator._idct2(dct_block)
                y_array[by:by+8, bx:bx+8] = idct_block
                
        # Remove padding
        y_array = y_array[:h, :w]
        y_array = np.clip(y_array, 0, 255).astype(np.uint8)
        
        new_y = Image.fromarray(y_array, 'L')
        final_img = Image.merge('YCbCr', (new_y, cb, cr)).convert('RGB')
        
        return final_img
