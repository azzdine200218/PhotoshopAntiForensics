import numpy as np
from PIL import Image
from src.utils.logger import logger

class HistogramMatcher:
    @staticmethod
    def exact_match(target_img, donor_img):
        """
        Adjusts the statistical distribution (histogram) of the target image
        to exactly match the authentic donor image.
        
        Defeats forensic tools that analyze probability density functions (PDFs)
        of the RGB channels to determine authenticity or origin profile.
        """
        logger.info(f"   [+] Applying Statistical Histogram Matching to match donor PDF...")
        
        # Ensure sizes don't matter visually, we only extract histograms
        target_array = np.array(target_img.convert('RGB'))
        donor_array = np.array(donor_img.convert('RGB'))
        
        matched_array = np.zeros_like(target_array)
        
        # Match each RGB channel independently
        for c in range(3):
            # Calculate histograms and CDFs
            target_hist, _ = np.histogram(target_array[:, :, c].ravel(), 256, [0, 256])
            donor_hist, _ = np.histogram(donor_array[:, :, c].ravel(), 256, [0, 256])
            
            target_cdf = target_hist.cumsum()
            donor_cdf = donor_hist.cumsum()
            
            # Normalize CDFs to max 1.0
            target_cdf_norm = target_cdf / target_cdf[-1] if target_cdf[-1] > 0 else target_cdf
            donor_cdf_norm = donor_cdf / donor_cdf[-1] if donor_cdf[-1] > 0 else donor_cdf
            
            # Create mapping lookup table
            mapping = np.zeros(256, dtype=np.uint8)
            for i in range(256):
                # Find closest index in donor purely by CDF shape
                diff = np.abs(donor_cdf_norm - target_cdf_norm[i])
                mapping[i] = np.argmin(diff)
                
            # Apply mapping blindly
            matched_array[:, :, c] = mapping[target_array[:, :, c]]
            
        logger.info(f"   [+] Statistical histogram cloned successfully.")
        return Image.fromarray(matched_array, 'RGB')
