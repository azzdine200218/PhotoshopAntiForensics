import numpy as np
from PIL import Image
from src.utils.logger import logger

class CopyMoveDefender:
    @staticmethod
    def disrupt_keypoints(img, distortion_factor=0.6):
        """
        Applies a sub-pixel elastic distortion grid to disrupt SIFT/SURF
        keypoint matching algorithms used in Copy-Move Forgery Detection (CMFD).
        
        A copied region will occupy a different phase of the sinusoidal 
        distortion grid relative to its origin, causing all keypoints and
        local gradients to become mathematically distinct while remaining
        perceptually identical.
        """
        logger.info(f"   [+] Executing Copy-Move Keypoint Disruption (Grid Elasticity: {distortion_factor})...")
        
        img_array = np.array(img)
        h, w, c = img_array.shape
        
        # Create coordinate meshgrid
        y, x = np.mgrid[0:h, 0:w]
        
        # Generate complex sinusoidal grid distortions (sub-pixel shift)
        # Using prime/offset frequencies to prevent predictable periodicity
        dx = distortion_factor * np.sin(2 * np.pi * y / 73.0) * np.cos(2 * np.pi * x / 47.0)
        dy = distortion_factor * np.sin(2 * np.pi * x / 61.0) * np.cos(2 * np.pi * y / 83.0)
        
        try:
            from scipy.ndimage import map_coordinates
            disrupted = np.zeros_like(img_array)
            # Apply distortion per channel
            coords = np.array([y + dy, x + dx])
            for i in range(c):
                disrupted[:,:,i] = map_coordinates(img_array[:,:,i], coords, order=1, mode='reflect')
        except ImportError:
            logger.warning("   [-] scipy not found. CMFD module falling back to gradient noise.")
            disrupted = img_array.copy()
            noise = np.random.normal(0, distortion_factor * 3, img_array.shape[:2])
            for i in range(c):
                disrupted[:,:,i] = np.clip(disrupted[:,:,i] + noise, 0, 255)
                
        return Image.fromarray(disrupted, 'RGB')
