"""Document-defined operating lease rules; editable costs never overwrite ERP."""
from decimal import Decimal, ROUND_HALF_UP
from fastapi import HTTPException

METHOD = 'fixed-term-v1'
MULTIPLIERS = {12: Decimal('1.15'), 24: Decimal('1.30'), 36: Decimal('1.45')}
BRANDS = ('Surface', 'Apple', 'Think', 'RTX Spark')
SOURCE_SHA256 = '936e5e433f5317aa04722920afbcf4342d9ebbdf581b7065e28843d95f02c77b'


def money(value):
    return Decimal(value).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)


def is_rtx_spark(item):
    return item.get('rental_family')=='RTX Spark'


def in_scope(item):
    return is_rtx_spark(item) or ('NVIDIA' not in item.get('product_type','') and 'Spark' not in (item.get('product_name') or ''))


def brand(item):
    if is_rtx_spark(item):return 'RTX Spark'
    text = ' '.join(str(item.get(k) or '') for k in ('product_type', 'product_name', 'original_family', 'series_group', 'raw_description')).lower()
    if any(x in text for x in ('apple', '苹果', 'macbook', 'imac', 'mac mini', 'mac studio', 'mac pro', 'ipad')):
        return 'Apple'
    if any(x in text for x in ('thinkpad', 'thinkbook', 'thinkcentre', 'thinkstation', 'think 设备')):
        return 'Think'
    if 'surface' in text:
        return 'Surface'
    return None


def is_device(item):
    if is_rtx_spark(item):return True
    kind = item.get('product_type', '')
    if 'NVIDIA' in kind or 'Spark' in (item.get('product_name') or ''):
        return False
    if any(x in kind for x in ('配件', '延保', '服务')):
        return False
    return kind == 'Surface 设备' or (brand(item) is not None and any(x in kind for x in ('设备', '电脑', '笔记本', '平板')))


def policy_payload(data):
    return {**data.model_dump(mode='json'), 'calculation_method': METHOD,
            'term_multipliers': {str(n): str(v) for n, v in MULTIPLIERS.items()},
            'source_sha256': SOURCE_SHA256,
            'source_reference': '硬件租赁费用计算示例表.docx；租期计价系数固定，残值与 Surface ERP 成本折扣按用户要求调整'}


def price(item, policy, months):
    """Return exact term rent, rounded standard instalment and final adjustment."""
    if months not in MULTIPLIERS:
        raise HTTPException(422, '仅支持 12、24、36 个月租赁')
    if item.get('erp_price_cny') is None or Decimal(str(item['erp_price_cny'])) <= 0:
        raise HTTPException(409, f"{item.get('part_number', '')} 缺少有效 ERP 价格")
    erp = money(str(item['erp_price_cny']))
    product_brand = brand(item)
    factor = Decimal(policy['surface_erp_cost_factor']) if product_brand == 'Surface' else Decimal(1)
    cost = money(erp * factor)
    if cost <= 0:
        raise HTTPException(422, '折扣后的硬件成本必须大于零')
    device = is_device(item)
    confirmed=product_brand in policy['residual_by_brand']
    if device and not confirmed and product_brand!='RTX Spark':
        raise HTTPException(422, '设备品牌没有配置残值规则')
    defaults={12:Decimal('.5'),24:Decimal('.4'),36:Decimal('.3')}
    residual_rate = (Decimal(policy['residual_by_brand'][product_brand][f'months_{months}']) if confirmed else defaults[months]) if device else Decimal(0)
    residual = money(cost * residual_rate)
    multiplier = MULTIPLIERS[months]
    priced = money(cost * multiplier)
    # Apply the source formula before rounding the term total, so independently
    # rounded intermediate values cannot change the customer's rent by a cent.
    total = money(cost * (multiplier - residual_rate))
    monthly = money(total / months)
    final = total - monthly * (months - 1)
    return {'brand': product_brand, 'erp_cost': erp, 'cost_factor': factor, 'cost': cost,'residual_confirmed':confirmed,
            'residual_rate': residual_rate, 'residual': residual, 'multiplier': multiplier,
            'priced_amount': priced, 'monthly': monthly, 'final_monthly': final, 'term_total': total}
