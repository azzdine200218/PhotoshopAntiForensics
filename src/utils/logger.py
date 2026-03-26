import logging
import sys

def get_logger(name="PhotoStrike"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # StreamHandler to sys.stdout ensures the Web UI SSE stream can capture it
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        try:
            import os
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
            log_file = os.path.join(log_dir, "photostrike.log")
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')
            fh.setFormatter(file_formatter)
            logger.addHandler(fh)
        except Exception:
            pass
            
    return logger

logger = get_logger()
