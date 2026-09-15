"""Generate validation calibration metrics and calibration curves."""

try:
    from ._wrapper_utils import ensure_reports
except ImportError:
    from _wrapper_utils import ensure_reports


def main() -> None:
    reports = ensure_reports()
    print(reports / "calibration_report.json")


if __name__ == "__main__":
    main()
