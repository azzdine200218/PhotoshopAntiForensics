import os
from psd_tools import PSDImage
from src.utils.logger import logger

class PSDCleaner:
    def __init__(self, input_path):
        self.input_path = input_path

    def _is_supported_format(self):
        ext = self.input_path.lower().split('.')[-1]
        return ext == 'psd'

    def create_clean_psd(self, output_path=None):
        """
        Processes a PSD file. To securely strip forensic properties like History, 
        XMP, or Exif from a PSD using Python (psd-tools), the safest known method 
        is to flatten the image (compose it to a single layer image) and save it 
        as a clean standard image format (like PNG/JPG). 
        
        Note: Modifying and saving native PSD structures while preserving layers 
        and wiping completely all XMP records without Adobe's SDK is highly 
        destructive or not natively supported by basic python tools.
        
        This method will flatten the PSD and save a clean composed copy.
        """
        if not os.path.exists(self.input_path):
            logger.error(f"[-] Error: PSD File not found: {self.input_path}")
            return None

        if not self._is_supported_format():
            logger.warning(f"[-] Warning: Expected a PSD file.")
            
        if output_path is None:
            name, _ = os.path.splitext(self.input_path)
            # Default fallback to exporting as clean PNG to assure metadata is gone
            output_path = f"{name}_flattened_clean.png"

        try:
            logger.info("[*] Loading PSD file (This might take a while for large files)...")
            psd = PSDImage.open(self.input_path)

            logger.info("[*] Flattening layers to a single solid image...")
            # composite() merges all visible layers into a single PIL Image
            composite_image = psd.composite()
            
            if composite_image is None:
                logger.error("[-] Error: Failed to composite PSD layers.")
                return None
            
            # Now we use the same technique as our ImageStripper
            logger.info("[*] Rebuilding pixels to ensure pure sterile image...")
            data = list(composite_image.getdata())
            clean_img = composite_image.__class__.new(composite_image.mode, composite_image.size)
            clean_img.putdata(data)
            
            clean_img.save(output_path, quality=100)
            
            logger.info(f"[+] Successfully converted PSD to sterile flattened image: {output_path}")
            logger.info("[!] Note: All forensic metadata, edit history, and hidden layers have been obliterated.")
            return output_path
            
        except Exception as e:
            logger.error(f"[-] An error occurred while processing the PSD: {str(e)}")
            return None

