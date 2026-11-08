import pytest
from fastapi.testclient import TestClient

from backend.src.market_platform.api.main import app
from backend.src.market_platform.data import storage

pytestmark = pytest.mark.integration


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    for section in ("raw", "processed"):
        (tmp_path / section).mkdir()
    (tmp_path / "raw" / "GOOGL_1d.csv").write_text("x", encoding="utf-8")
    (tmp_path / "processed" / "GOOGL_daily.csv").write_text("x", encoding="utf-8")
    (tmp_path / "processed" / "GOOGL_weekly.csv").write_text("x", encoding="utf-8")
    monkeypatch.setattr(storage, "url_database", lambda: str(tmp_path) + "/")
    return tmp_path


def test_post_deletes_the_downloaded_files_and_reports_the_counts(data_dir):
    response = TestClient(app).post("/data-cache/clear")

    assert response.status_code == 200
    assert response.json() == {"deleted_raw": 1, "deleted_processed": 2, "failed": []}
    assert list((data_dir / "raw").iterdir()) == []
    assert list((data_dir / "processed").iterdir()) == []


def test_deleting_data_needs_a_post_request(data_dir):
    response = TestClient(app).get("/data-cache/clear")

    assert response.status_code == 405
    assert len(list((data_dir / "raw").iterdir())) == 1
