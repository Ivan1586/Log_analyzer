import argparse
import gzip
import json
import logging
import os
import statistics
import sys
import traceback
from collections import defaultdict, namedtuple
from datetime import date, datetime
from typing import Dict, Generator, List, TypedDict, Union

import structlog

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_PATH = "config.json"

LogEntry = namedtuple("LogEntry", ["url", "request_time"])

log = structlog.get_logger()


class UrlStats(TypedDict):
    count: int
    time_sum: float
    times: List[float]


def configure_logging(base_dir: str, log_dir: str | None = None) -> None:
    """Logging configuration"""
    structlog.configure(
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    if not log_dir:
        # configuring logging for console output
        logging.basicConfig(
            format="%(message)s", stream=sys.stdout, level=logging.DEBUG
        )
        log.info("Logging to console configured.")
    else:
        path = os.path.join(base_dir, log_dir)
        log_file_path = os.path.abspath(
            os.path.join(path, f"log_file_{date.today()}.txt")
        )

        logging.basicConfig(
            format="%(message)s",
            filename=log_file_path,
            filemode="a",  # append mode
            level=logging.DEBUG,
            encoding="utf-8",
        )
        log.info("Log file configured:", file=log_file_path)


def get_last_log(log_dir: str) -> str | None:
    """Return the latest log file from the log directory"""
    log_files = [
        file
        for file in os.listdir(log_dir)
        if file.endswith(".gz") or file.endswith(".log")
    ]
    if not log_files:
        log.warning("Logs were not found in the directory", log_dir=log_dir)
        return None

    date_logs: Dict[str, datetime] = {}
    for file in log_files:
        # get the date for further search of the most recent log
        log_name_without_extension = file.split(".")
        log_date = log_name_without_extension[1].split("-")[1]
        log_date_parsed = datetime.strptime(log_date, "%Y%m%d")
        date_logs[file] = log_date_parsed

    last_log = max(date_logs, key=lambda x: date_logs[x])
    return os.path.join(log_dir, last_log)


def parse_log(file_path: str) -> Generator[LogEntry, None, None]:
    """Generator for extracting data from log's file"""
    with (
        gzip.open(file_path, "rt")
        if file_path.endswith(".gz")
        else open(file_path, "r")
    ) as file:
        for line in file:
            parts = line.split()
            url = parts[6]
            request_time = float(parts[-1])
            yield LogEntry(url, request_time)


def analyze_logs(file_path: str) -> List[Dict[str, Union[str, int, float]]]:
    """Analyze nginx_logs and return aggregated data."""
    url_stats: Dict[str, UrlStats] = defaultdict(
        lambda: {"count": 0, "time_sum": 0.0, "times": []}
    )
    total_time: float = 0.0
    total_count: int = 0

    for entry in parse_log(file_path):
        url_stats[entry.url]["count"] += 1
        url_stats[entry.url]["time_sum"] += entry.request_time
        url_stats[entry.url]["times"].append(entry.request_time)
        total_time += entry.request_time
        total_count += 1

    log.info(
        "Get data from the receipt log",
        total_count=total_count,
        total_time=total_time,
    )

    # calculate statistics for URLs
    report_data: List[Dict[str, Union[str, int, float]]] = []
    for url, stats in url_stats.items():
        time_sum: float = stats["time_sum"]
        count: int = stats["count"]
        time_avg: float = time_sum / count if count > 0 else 0
        time_max: float = max(stats["times"], default=0.0)
        time_med: float = (
            statistics.median(stats["times"]) if stats["times"] else 0.0
        )
        count_perc: float = count / total_count if total_count > 0 else 0
        time_perc: float = time_sum / total_time if total_time > 0 else 0

        report_data.append(
            {
                "url": url,
                "count": count,
                "count_perc": count_perc,
                "time_sum": time_sum,
                "time_perc": time_perc,
                "time_avg": time_avg,
                "time_max": time_max,
                "time_med": time_med,
            }
        )

    return report_data


def render_report(
    data: List[Dict[str, Union[str, int, float]]], report_dir: str
) -> str:
    """Render the HTML report with the given data"""
    # load the template
    with open("../report.html", "r") as file:
        report_template = file.read()

    report_json = json.dumps(data)
    report_content = report_template.replace("$table_json", report_json)
    report_date = datetime.now().strftime("%Y.%m.%d")
    report_path = os.path.join(report_dir, f"report-{report_date}.html")

    with open(report_path, "w") as f:
        f.write(report_content)

    return report_path


def read_config(file_path: str) -> Dict[str, Union[str, int]]:
    """Reads the configuration from the specified file"""
    if not os.path.exists(file_path):
        log.error("The configuration file is not found", file_path=file_path)
        raise FileNotFoundError

    with open(file_path, "r") as file:
        try:
            config = json.load(file)
        except json.JSONDecodeError:
            log.error(
                "Error parsing the configuration file", file_path=file_path
            )
            raise ValueError

    return config


def main() -> None:
    parser = argparse.ArgumentParser(
        description="The program with the configuration"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=DEFAULT_CONFIG_PATH,
        help="The path to the configuration file",
    )

    args = parser.parse_args()

    try:
        # reading the configuration
        config = read_config(args.config)

        log_dir = config.get("LOG_FILES_DIR")
        if log_dir is not None and not isinstance(log_dir, str):
            raise ValueError("LOG_FILES_DIR must be str type")
        configure_logging(BASE_DIR, log_dir)

        log.info("The configuration is loaded:", config=config)
        log_file_path: str | None = get_last_log(
            BASE_DIR + str(config["LOG_DIR"])
        )

        if not log_file_path:
            log.warning("There are no nginx_logs to analyze")
            return
        log.info("The last log was found", log_file_path=log_file_path)

        report_data = analyze_logs(log_file_path)
        report_path: str = render_report(
            report_data, BASE_DIR + str(config["REPORT_DIR"])
        )
        log.info("Report generated", report_path=report_path)

    except (FileNotFoundError, ValueError) as e:
        log.error("Error", error=str(e))
    except Exception as e:
        log.error(
            "Unexpected error", error=str(e), traceback=traceback.format_exc()
        )


if __name__ == "__main__":
    main()
