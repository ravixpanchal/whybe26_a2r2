"""Generate the Random Forest evaluation report."""

try:
    from ._wrapper_utils import ensure_reports
except ImportError:
    from _wrapper_utils import ensure_reports


def main() -> None:
    reports = ensure_reports()
    print(reports / "random_forest_metrics.json")


if __name__ == "__main__":
    main()
