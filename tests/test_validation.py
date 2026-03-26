import pytest
import os
from unittest.mock import MagicMock
from src.utils.file_validator import allowed_file, validate_upload

def test_allowed_file():
    assert allowed_file('image.jpg') is True
    assert allowed_file('image.PNG') is True
    assert allowed_file('document.pdf') is False
    assert allowed_file('malware.exe') is False
    assert allowed_file('no_extension_file') is False

def test_validate_upload_empty_obj():
    valid, err = validate_upload(None)
    assert valid is False
    assert "No file provided" in err

def test_validate_upload_empty_filename():
    mock_file = MagicMock()
    mock_file.filename = ""
    valid, err = validate_upload(mock_file)
    assert valid is False
    assert "No file provided" in err

def test_validate_upload_invalid_extension():
    mock_file = MagicMock()
    mock_file.filename = "script.sh"
    valid, err = validate_upload(mock_file)
    assert valid is False
    assert "File format not supported" in err

def test_validate_upload_valid_file_mock():
    mock_file = MagicMock()
    mock_file.filename = "legit.jpg"
    mock_file.tell.return_value = 1024 * 1024 * 5 # 5 MB
    
    valid, err = validate_upload(mock_file)
    assert valid is True
    assert err is None

def test_validate_upload_file_too_large():
    mock_file = MagicMock()
    mock_file.filename = "huge_file.psd"
    mock_file.tell.return_value = 1024 * 1024 * 100 # 100 MB > 50 MB limit
    
    valid, err = validate_upload(mock_file)
    assert valid is False
    assert "exceeds maximum size" in err
