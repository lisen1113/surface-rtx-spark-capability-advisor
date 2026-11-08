"""Public advisor entitlement, separate from administrative and ERP access."""
import os
from fastapi import Header, Request


def public_advisor_enabled():
    return os.getenv('CAPABILITY_PUBLIC_ADVISOR') == '1'


def public_product(item):
    if not public_advisor_enabled():
        return item
    return {key:value for key,value in item.items() if key not in {
        'erp_price_cny', 'adr_price_cny', 'source_reference', 'source_sha256',
        'raw_configuration', 'note', 'currency_note'}}


def require_advisor_user(authorization: str | None = Header(default=None)):
    from .auth import require_entitled_user
    if public_advisor_enabled():
        return None
    return require_entitled_user(authorization)


def require_catalog_user(request: Request, authorization: str | None = Header(default=None)):
    from .auth import require_entitled_user
    path = request.url.path
    if public_advisor_enabled() and (path in {'/api/catalog/imported-skus', '/api/catalog/models'}
                                    or path.startswith('/api/catalog/advisor/')):
        return None
    return require_entitled_user(authorization)
