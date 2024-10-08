from unittest.mock import mock_open, patch

import pytest

from src.log_analyzer import LogEntry, analyze_logs, parse_log

TEST_LOG_DIR = "../logs"
TEST_CONFIG = {
    "LOG_FILES_DIR": TEST_LOG_DIR,
    "LOG_DIR": "../nginx_logs",
    "REPORT_DIR": "../reports",
}


@pytest.fixture
def mock_log_file():
    """Fixture to create a mock log file."""
    mock_log_data = (
        "127.0.0.1 - - [01/Jan/2022:00:00:00 +0000] "
        "\"GET /test-url HTTP/1.1\" 200 0.123\n"
        "127.0.0.1 - - [01/Jan/2022:00:00:01 +0000] "
        "\"GET /test-url HTTP/1.1\" 200 0.456\n"
    )
    with patch("builtins.open", mock_open(read_data=mock_log_data)):
        yield


def test_parse_log(mock_log_file):
    """Test parse_log function."""
    entries = list(parse_log("mock_log_path"))
    assert len(entries) == 2
    assert entries[0] == LogEntry(url="/test-url", request_time=0.123)


def test_analyze_logs(mock_log_file):
    """Test analyze_logs function."""
    report_data = analyze_logs("mock_log_path")
    assert len(report_data) == 1
    assert report_data[0]["url"] == "/test-url"
    assert report_data[0]["count"] == 2
    assert report_data[0]["time_sum"] == 0.579
