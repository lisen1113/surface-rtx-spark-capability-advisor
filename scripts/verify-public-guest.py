"""Read-only public guest smoke check; never send credentials or print SKU data."""

from __future__ import annotations

import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


FORBIDDEN_KEYS = {
    "erp_price_cny", "price_cny", "source_reference", "raw_configuration",
    "currency_note", "source_sha256", "over_budget",
}


def request(base: str, path: str, payload: dict | None = None) -> tuple[int, bytes]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    req = Request(base + path, data=body, headers=headers, method="POST" if body else "GET")
    try:
        with urlopen(req, timeout=12) as response:
            return response.status, response.read(2_000_000)
    except HTTPError as error:
        return error.code, error.read(1024)


def assert_public_projection(value: object) -> None:
    if isinstance(value, dict):
        leaked = FORBIDDEN_KEYS.intersection(value)
        if leaked:
            raise AssertionError(f"游客响应包含受保护字段：{sorted(leaked)}")
        for child in value.values():
            assert_public_projection(child)
    elif isinstance(value, list):
        for child in value:
            assert_public_projection(child)


def verify(base: str) -> None:
    status, page = request(base, "/guest")
    assert status == 200 and b"/api/recommendations" in page, "完整游客顾问页面不可用"

    status, raw = request(base, "/api/guest/skus")
    assert status == 200, f"游客产品列表 HTTP {status}"
    listing = json.loads(raw)
    assert isinstance(listing.get("items"), list) and listing["items"], "游客产品列表为空"
    assert_public_projection(listing)

    status, raw = request(base, "/api/guest/recommendations", {
        "usages": ["ai", "productivity"], "ai_size": "32B", "work_need": "coding",
    })
    assert status == 200, f"游客推荐 HTTP {status}"
    recommendation = json.loads(raw)
    assert recommendation.get("status") == "shortlist", "游客推荐未返回候选"
    assert recommendation.get("items"), "游客候选为空"
    assert all(item.get("evidence_level", "").startswith("工程估算")
               for item in recommendation["items"]), "候选缺少工程估算标记"
    assert_public_projection(recommendation)

    status, _ = request(base, "/api/catalog/imported-skus")
    assert status == 200, f"未登录顾问目录应返回 200，实际为 {status}"
    status, _ = request(base, "/api/reports/" + quote(listing["items"][0]["part_number"], safe="") + ".pdf")
    assert status == 200, f"未登录报告应返回 200，实际为 {status}"
    for path in ("/api/admin/users", "/api/catalog/sources", "/api/catalog/imports"):
        status, _ = request(base, path)
        assert status == 401, f"管理/导入边界错误：{path} HTTP {status}"
    print("游客页面、产品列表、需求推荐、数据脱敏和授权边界均通过。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", help="例如 https://surfacedmp.com；不含尾部斜杠")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    if not base_url.startswith("https://"):
        parser.error("公网预检只接受 HTTPS URL")
    try:
        verify(base_url)
    except (AssertionError, URLError, ValueError) as error:
        raise SystemExit(f"游客公网预检失败：{error}") from error
