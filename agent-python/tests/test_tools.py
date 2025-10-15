import pytest
import tempfile
import os
from tools.summarize_by_ip import sanitize_name


def test_sanitize_name():
    assert sanitize_name("test-file.log") == "test-file.log"
    assert sanitize_name("test/file") == "test_file"
    assert sanitize_name("test@#$file") == "test___file"
