import os
from PIL import Image, ImageChops, ImageEnhance
import numpy as np
from src.utils.logger import logger

class ELAAnalyzer:
    @staticmethod
    def generate_ela(image_path, output_path=None, quality=90, multiplier=15):
        """
        Generates an Error Level Analysis (ELA) apparent visual map.
        It locally recompresses the image and displays the magnified difference.
        """
        try:
            logger.info("   [*] Initiating Error Level Analysis (ELA)...")
            if not output_path:
                name, ext = os.path.splitext(image_path)
                output_path = f"{name}_ela.png"

            original = Image.open(image_path).convert('RGB')
            
            # Recompress at standard quality
            temp_path = f"{output_path}.temp.jpg"
            original.save(temp_path, 'JPEG', quality=quality)
            temp = Image.open(temp_path)
            
            # Calculate absolute difference
            diff = ImageChops.difference(original, temp)
            
            # Find maximum difference to scale brightness properly
            extrema = diff.getextrema()
            max_diff = max([ex[1] for ex in extrema])
            if max_diff == 0:
                max_diff = 1 # Avoid division by zero
            scale = 255.0 / max_diff
            
            # Enhance brightness for better visibility
            diff = ImageEnhance.Brightness(diff).enhance(scale * (multiplier / 10.0))
            
            diff.save(output_path)
            
            # Clean up temp
            try:
                temp.close()
                os.remove(temp_path)
            except Exception:
                pass
            
            logger.info(f"   [+] ELA Heatmap generated successfully.")
            return output_path
        except Exception as e:
            logger.error(f"   [-] ELA Analysis failed: {e}")
            return None
