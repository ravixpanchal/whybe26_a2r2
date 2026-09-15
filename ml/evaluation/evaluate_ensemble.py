"""Generate the soft-voting ensemble evaluation report."""

try:
    from ._wrapper_utils import ensure_reports
except ImportError:
    from _wrapper_utils import ensure_reports


def main() -> None:
    reports = ensure_reports()
    print(reports / "ensemble_metrics.json")


if __name__ == "__main__":
    main()
