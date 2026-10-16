"""Guard HTML rendering of catalog and FAQ data loaded into the local UI."""

from fastapi import Response

from app.ui import index


def _page() -> str:
    return index(Response())


def test_imported_text_is_escaped_before_html_insertion():
    page = _page()
    assert "const metric=(k,v)=>" in page
    assert "${escapeHtml(k)}</span><b>${escapeHtml(v)}" in page
    for field in ("title", "result", "official", "engineering", "perf", "note"):
        assert "${escapeHtml(" + field + ")}" in page
    for field in ("data.disclaimer", "s.data_status", "s.source_reference", "s.note"):
        assert "${escapeHtml(" + field + ")}" in page
    for field in ("x.question", "x.category", "x.easy_answer", "x.expert_answer",
                  "x.misconception", "x.sales_tip"):
        assert "${escapeHtml(" + field + ")}" in page


def test_external_source_links_require_https_and_escaped_attribute():
    page = _page()
    assert "url.protocol==='https:'?url.href:null" in page
    assert 'href="${escapeHtml(sourceUrl)}"' in page
    assert 'rel="noopener noreferrer"' in page
