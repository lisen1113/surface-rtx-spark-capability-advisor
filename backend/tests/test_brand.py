from fastapi.testclient import TestClient

from app.main import app


def test_user_supplied_logo_is_served_and_referenced_in_print_views():
    client = TestClient(app)
    logo = client.get("/assets/yihe-logo.png")
    assert logo.status_code == 200
    assert logo.headers["content-type"] == "image/png"
    assert logo.content.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(logo.content) > 1000
    assert "/assets/yihe-logo.png" in client.get("/").text
    assert "/assets/yihe-logo.png" in client.get("/deployment").text
