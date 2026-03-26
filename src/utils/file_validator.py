import os

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'psd'}
MAX_FILE_SIZE_MB = 50

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_upload(file_obj):
    """
    Validates uploaded file against security constraints (size, type).
    Returns (True, None) if safe.
    Returns (False, Error Message) if unsafe.
    """
    if not file_obj or file_obj.filename == '':
        return False, "[-] Error: No file provided."
        
    if not allowed_file(file_obj.filename):
        return False, f"[-] Error: File format not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        
    try:
        file_obj.seek(0, os.SEEK_END)
        file_length = file_obj.tell()
        file_obj.seek(0)
        
        if file_length > MAX_FILE_SIZE_MB * 1024 * 1024:
            return False, f"[-] Error: File exceeds maximum size of {MAX_FILE_SIZE_MB}MB."
    except Exception as e:
        return False, f"[-] Error: Failed to validate file size. {e}"
        
    return True, None
