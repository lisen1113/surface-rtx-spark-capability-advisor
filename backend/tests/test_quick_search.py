from fastapi.testclient import TestClient

from app import catalog
from app.main import app
from app.catalog import _lookup_item


client = TestClient(app)

def test_power_supply_marks_follow_user_configuration_codes():
    for raw, expected in [
        ('Pro12inSD1EP/16/1TBCMxP SC ChnSimp China Comm Platinum', '不带电源'),
        ('Pro12inSD1EP/16/1TBCM SC ChnSimp China Comm Platinum', ''),
        ('Misawa / K / 16GB / 256GB / No-PSU / Wi-Fi', '不带电源'),
        ('Pro 13 xP Platinum', '不带电源'),
        ('Fernvale / K / 16GB / Wilkeson 45W', ''),
    ]:
        item = _lookup_item({'product_type': 'Surface 设备', 'raw_description': raw})
        assert item['power_supply'] == expected
    assert _lookup_item({'product_type': 'Surface 设备', 'raw_description': 'K / 16GB', 'power_supply': 'Wilkeson 45W'})['power_supply'] == ''


def test_surface_mobile_pdf_ticket_preserves_sku_filename_and_single_use(monkeypatch, tmp_path):
    from app.auth import now, iso
    from app.advisor_access import require_advisor_user as require_entitled_user
    from datetime import timedelta
    monkeypatch.delenv('CAPABILITY_AUTH_DATABASE_URL', raising=False)
    monkeypatch.setattr(catalog, 'DB_PATH', tmp_path / 'mobile.sqlite3')
    with catalog.connection() as conn:
        _insert_lookup(conn, part_number='EP2-MOBILE', product_type='Surface 设备', series='Surface Pro',
                       family='Pro', description='CMxP', product_name='Surface Pro', match_level='A1 配置一致', price=10000)
        conn.execute("INSERT INTO organizations (id,name,status,created_at) VALUES (1,'test','approved',?)", (iso(now()),))
        conn.execute("INSERT INTO users (id,organization_id,email,password_hash,role,status,email_verified,created_at) VALUES (1,1,'mobile@example.invalid','unused','member','approved',1,?)", (iso(now()),))
        conn.execute("INSERT INTO licenses VALUES (1,1,?,'active',?)", (iso(now()+timedelta(days=1)), iso(now())))
        conn.commit()
    app.dependency_overrides[require_entitled_user] = lambda: {'id': 1}
    try:
        issued = client.post('/api/reports/mobile-ticket', json={'part_number':'EP2-MOBILE','report_kind':'surface'})
        assert issued.status_code == 200
        assert issued.json()['filename'] == 'Surface-Product-EP2-MOBILE.pdf'
        path = '/api/reports/mobile-download/' + issued.json()['ticket']
        pdf = client.get(path)
        assert pdf.status_code == 200 and pdf.content.startswith(b'%PDF-')
        assert 'Surface-Product-EP2-MOBILE.pdf' in pdf.headers['content-disposition']
        assert client.get(path).status_code == 404
    finally:
        app.dependency_overrides.pop(require_entitled_user, None)


def _insert_lookup(conn, *, part_number, product_type, series, family, description,
                   product_name, match_level, memory=None, price=None, cpu=None):
    conn.execute(
        """INSERT INTO sku_lookup (
        part_number,source_sheet,source_row,original_family,raw_description,product_type,
        series_group,product_name,cpu_official,memory_gb,erp_price_cny,match_level,
        review_status,source_sha256
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (part_number, "test", 2, family, description, product_type, series, product_name,
         cpu, memory, price, match_level, "可查验", "quick-search-test"),
    )


def test_quick_search_filters_exact_part_number_series_and_price(monkeypatch, tmp_path):
    monkeypatch.setattr(catalog, "DB_PATH", tmp_path / "catalog.sqlite3")
    with catalog.connection() as conn:
        _insert_lookup(
            conn, part_number="EP2-FAST", product_type="Surface 设备", series="Surface Pro",
            family="SrPro 13in", description="Ultra 5 / 16GB / 256GB", product_name="Surface Pro 商用版",
            match_level="A1 配置一致", memory=16, price=10888, cpu="Intel Ultra 5",
        )
        _insert_lookup(
            conn, part_number="ACC-FAST", product_type="配件", series="配件", family="配件",
            description="Surface mouse", product_name="Surface Arc Mouse",
            match_level="U1 用户规则映射", price=588,
        )
        _insert_lookup(
            conn, part_number="NVIDIA-FAST", product_type="NVIDIA 设备（暂不纳入）", series="NVIDIA（暂不纳入）",
            family="NVIDIA", description="excluded", product_name="", match_level="N/A 不在本轮设备规格范围",
            price=99999,
        )
        conn.commit()

    exact = client.get("/api/catalog/quick-search", params={"q": "ep2-fast"}).json()
    assert exact["total"] == 1
    assert exact["items"][0]["part_number"] == "EP2-FAST"
    assert exact["items"][0]["erp_price_cny"] == 10888
    assert "用户提供" in exact["price_basis"]

    filtered = client.get("/api/catalog/quick-search", params={
        "product_type": "Surface 设备", "series": "Surface Pro", "memory_gb": 16,
        "max_erp_price_cny": 11000,
    }).json()
    assert [item["part_number"] for item in filtered["items"]] == ["EP2-FAST"]

    default_listing = client.get("/api/catalog/quick-search").json()
    assert default_listing["total"] == 2
    assert all(not item["part_number"].startswith("NVIDIA") for item in default_listing["items"])
    with catalog.connection() as conn:
        conn.execute("UPDATE sku_lookup SET storage_capacity='256GB' WHERE part_number='EP2-FAST'")
        conn.commit()
    assert client.get('/api/catalog/quick-search', params={'storage_capacity': '256GB'}).json()['total'] == 1
    assert client.get('/api/catalog/quick-search', params={'storage_capacity': '1TB'}).json()['total'] == 0
    with catalog.connection() as conn:
        conn.execute("UPDATE sku_lookup SET display='13.8 英寸 PixelSense' WHERE part_number='EP2-FAST'")
        conn.commit()
    assert client.get('/api/catalog/quick-search', params={'screen_size': '13.8'}).json()['total'] == 1
    assert client.get('/api/catalog/quick-search', params={'screen_size': '13'}).json()['total'] == 0
    with catalog.connection() as conn:
        conn.execute("UPDATE sku_lookup SET connectivity='Wi-Fi / 5G' WHERE part_number='EP2-FAST'")
        conn.commit()
    assert client.get('/api/catalog/quick-search', params={'network': '5g'}).json()['total'] == 1
    assert client.get('/api/catalog/quick-search', params={'network': 'wifi'}).json()['total'] == 0
    with catalog.connection() as conn:
        conn.execute("UPDATE sku_lookup SET connectivity='Wi-Fi' WHERE part_number='EP2-FAST'")
        conn.commit()
    assert client.get('/api/catalog/quick-search', params={'network': 'wifi'}).json()['total'] == 1
    independent = client.get('/api/catalog/quick-search', params={
        'product_type': '配件', 'q': 'no-match', 'processor': 'Intel',
        'series': 'Surface Pro', 'memory_gb': 128, 'storage_capacity': '1TB', 'max_erp_price_cny': 1, 'screen_size': '12', 'network': '5g',
    }).json()
    assert [item['part_number'] for item in independent['items']] == ['ACC-FAST']


def test_quick_search_options_and_detail_keep_source_boundary(monkeypatch, tmp_path):
    monkeypatch.setattr(catalog, "DB_PATH", tmp_path / "catalog.sqlite3")
    with catalog.connection() as conn:
        _insert_lookup(
            conn, part_number="WARRANTY-FAST", product_type="延保", series="延保", family="延保",
            description="Complete for Business", product_name="商业 Microsoft Complete",
            match_level="W1 延保独立清单", price=1458,
        )
        conn.execute(
            "UPDATE sku_lookup SET official_source_url=?, unknown_fields=? WHERE part_number=?",
            ("https://www.microsoftstore.com.cn/warranty/extended-warranty-comm", "逐 Part Number 可售状态", "WARRANTY-FAST"),
        )
        conn.commit()

    options = client.get("/api/catalog/quick-search/options").json()
    assert options["searchable_count"] == 1
    assert options["product_types"] == [{"value": "延保", "count": 1}]
    detail = client.get("/api/catalog/quick-search/WARRANTY-FAST").json()["item"]
    assert detail["product_name"] == "商业 Microsoft Complete"
    assert detail["official_source_url"].startswith("https://www.microsoftstore.com.cn/")
    assert "source_sha256" not in detail
    assert client.get("/api/catalog/quick-search/DOES-NOT-EXIST").status_code == 404
