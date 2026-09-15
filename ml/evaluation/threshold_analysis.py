"""Generate validation-only operating-threshold analysis."""

try:
    from ._wrapper_utils import ensure_reports
except ImportError:
    from _wrapper_utils import ensure_reports


def main() -> None:
    reports = ensure_reports()
    print(reports / "threshold_analysis.json")


if __name__ == "__main__":
    main()
