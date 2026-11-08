from pathlib import Path

import pandas as pd
import pytest

from backend.src.market_platform import pipeline
from backend.src.market_platform.data import storage
from backend.src.market_platform.services import data_cache_service, model_training_service


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    for section in ("raw", "processed", "external"):
        (tmp_path / section).mkdir()
    monkeypatch.setattr(storage, "url_database", lambda: str(tmp_path) + "/")
    return tmp_path


def touch(*paths):
    for path in paths:
        path.write_text("x", encoding="utf-8")


@pytest.fixture
def cache_calls(monkeypatch):
    calls = []
    monkeypatch.setattr(pipeline, "clear_cache", lambda: calls.append("pipeline"))
    monkeypatch.setattr(model_training_service, "clear_cache", lambda: calls.append("models"))
    return calls


def test_csv_files_of_raw_and_processed_are_deleted_and_counted(data_dir, cache_calls):
    touch(data_dir / "raw" / "GOOGL_1d.csv", data_dir / "raw" / "GOOGL_1h.csv", data_dir / "processed" / "GOOGL_daily.csv")

    result = data_cache_service.clear_market_data()

    assert result == {"deleted_raw": 2, "deleted_processed": 1, "failed": []}
    assert list((data_dir / "raw").iterdir()) == []
    assert list((data_dir / "processed").iterdir()) == []


def test_only_csv_files_are_touched(data_dir, cache_calls):
    keep = [data_dir / "raw" / "notes.txt", data_dir / "processed" / ".gitkeep", data_dir / "external" / "macro.csv"]
    touch(*keep, data_dir / "raw" / "SP500_1d.csv")
    (data_dir / "processed" / "subfolder").mkdir()
    touch(data_dir / "processed" / "subfolder" / "inner.csv")

    data_cache_service.clear_market_data()

    assert all(path.exists() for path in keep)
    assert (data_dir / "processed" / "subfolder" / "inner.csv").exists()
    assert not (data_dir / "raw" / "SP500_1d.csv").exists()


def test_memory_caches_are_cleared_after_the_files(data_dir, monkeypatch):
    events = []
    touch(data_dir / "raw" / "GOOGL_1d.csv")
    monkeypatch.setattr(pipeline, "clear_cache", lambda: events.append(("pipeline", (data_dir / "raw" / "GOOGL_1d.csv").exists())))
    monkeypatch.setattr(model_training_service, "clear_cache", lambda: events.append(("models", None)))

    data_cache_service.clear_market_data()

    assert events == [("pipeline", False), ("models", None)]


def test_missing_folders_are_not_an_error(tmp_path, monkeypatch, cache_calls):
    monkeypatch.setattr(storage, "url_database", lambda: str(tmp_path) + "/")

    result = data_cache_service.clear_market_data()

    assert result == {"deleted_raw": 0, "deleted_processed": 0, "failed": []}
    assert cache_calls == ["pipeline", "models"]


def test_a_file_that_cannot_be_deleted_is_reported_and_the_rest_still_go(data_dir, cache_calls, monkeypatch):
    touch(data_dir / "raw" / "A_1d.csv", data_dir / "raw" / "B_1d.csv", data_dir / "processed" / "A_daily.csv")
    real_unlink = Path.unlink

    def unlink(self, *args, **kwargs):
        if self.name == "B_1d.csv":
            raise PermissionError("en uso por otro proceso")
        return real_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", unlink)

    result = data_cache_service.clear_market_data()

    assert result["deleted_raw"] == 1
    assert result["deleted_processed"] == 1
    assert result["failed"] == [{"file": "raw/B_1d.csv", "error": "en uso por otro proceso"}]
    assert (data_dir / "raw" / "B_1d.csv").exists()
    assert cache_calls == ["pipeline", "models"]


def test_pipeline_clear_cache_forces_the_csv_to_be_read_again(monkeypatch):
    reads = []

    def import_csv(name, section, parse_dates=False):
        reads.append(name)
        return pd.DataFrame({"Close": [1.0]})

    monkeypatch.setattr(pipeline.storage, "import_csv", import_csv)
    pipeline.clear_cache()

    pipeline.processedTimeframes("TESTSYM", 0)
    pipeline.processedTimeframes("TESTSYM", 0)
    reads_before = len(reads)
    pipeline.clear_cache()
    pipeline.processedTimeframes("TESTSYM", 0)

    assert reads_before == len(pipeline.timeframe_names[0])
    assert len(reads) == 2 * reads_before
    pipeline.clear_cache()


def test_model_training_clear_cache_forces_a_retrain(monkeypatch):
    trained = []
    frame = pd.DataFrame({"Close": [1.0]}, index=pd.DatetimeIndex(["2026-01-05"]))
    monkeypatch.setattr(pipeline, "processedTimeframes", lambda symbol, t: [frame, frame])
    monkeypatch.setattr(model_training_service, "build_features_ML", lambda *args: ("X", "y", "X_latest"))
    monkeypatch.setattr(model_training_service, "train_model", lambda name, X, y: trained.append(name) or name)
    model_training_service.clear_cache()

    model_training_service._train_all_models("TESTASSET")
    model_training_service._train_all_models("TESTASSET")
    trained_once = len(trained)
    model_training_service.clear_cache()
    model_training_service._train_all_models("TESTASSET")

    assert trained_once == len(model_training_service.CLASSIFIER_MODELS)
    assert len(trained) == 2 * trained_once
    model_training_service.clear_cache()
