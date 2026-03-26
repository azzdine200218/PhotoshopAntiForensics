import piexif
from PIL import Image
from src.utils.logger import logger

class MetadataInspector:
    @staticmethod
    def inspect(image_path):
        """
        Extracts structured EXIF and XMP data and identifies potential 
        digital manipulation traces in headers.
        """
        technical_data = {}
        exif_results = {}
        warnings_list = []
        try:
            logger.info("   [*] Extracting EXIF and Metadata Payloads...")
            with Image.open(image_path) as img:
                technical_data["Format"] = img.format
                technical_data["Mode"] = img.mode
                technical_data["Resolution"] = f"{img.size[0]}x{img.size[1]}"
                
                # Check for standard EXIF
                exif_data = img.info.get('exif')
                if exif_data:
                    exif_dict = piexif.load(exif_data)
                    for ifd in ("0th", "Exif", "GPS", "1st"):
                        exif_results[ifd] = {}
                        for tag in exif_dict[ifd]:
                            try:
                                tag_name = piexif.TAGS[ifd][tag]["name"]
                                val = exif_dict[ifd][tag]
                                if isinstance(val, bytes):
                                    try:
                                        val = val.decode('utf-8').strip('\x00')
                                    except UnicodeDecodeError:
                                        if len(val) > 30:
                                            val = f"<Binary Blob: {len(val)} bytes>"
                                        else:
                                            val = str(val)
                                exif_results[ifd][tag_name] = val
                            except Exception:
                                pass
                else:
                    warnings_list.append("No EXIF metadata payload found.")
                    
                # Forensic Traces: Look for Photoshop/Adobe specific markers
                raw_info = str(img.info).lower()
                if 'photoshop' in raw_info or 'adobe' in raw_info or 'xmp' in raw_info:
                    warnings_list.append("CRITICAL: Adobe/Photoshop or XMP traces detected in headers.")
                
            logger.info("   [+] Metadata extraction complete.")
            return {"technical": technical_data, "exif": exif_results, "warnings": warnings_list}
        except Exception as e:
            logger.error(f"   [-] Metadata extraction failed: {e}")
            return None
