from ml.data_audit.dataset_audit import audit_dataset


def test_dataset_target_and_shape():
    report = audit_dataset()

    assert report["shape"] == {"rows": 10000, "columns": 41}
    assert report["target_column"] == "defaulted"
    assert report["class_mapping"] == {0: "non_default", 1: "defaulted"}
    assert report["class_distribution"]["0"] == 8499
    assert report["class_distribution"]["1"] == 1501
    assert report["duplicate_rows"] == 0


def test_dataset_leakage_and_sensitive_columns():
    report = audit_dataset()

    assert "default_probability" in report["leakage_columns"]
    assert "age" in report["sensitive_proxy_columns"]
    assert "state" in report["sensitive_proxy_columns"]
    assert "borrower_id" in report["id_columns"]
    assert report["missing_value_pct"]["ecomm_return_rate"] > 20.0
