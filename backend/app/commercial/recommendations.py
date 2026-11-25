"""Lowest published Business price that covers each requested user cohort."""
from decimal import Decimal
from fastapi import HTTPException
from . import engine, store

BASES = ('M365-BIZ-BASIC', 'M365-BIZ-STANDARD', 'M365-BIZ-PREMIUM')
BUNDLES = {'M365-BIZ-STANDARD':'BUNDLE-STANDARD-COPILOT','M365-BIZ-PREMIUM':'BUNDLE-PREMIUM-COPILOT'}
COPILOT = 'COPILOT-BUSINESS'


def recommend(data):
    note='按当前已发布 Business 美元公开标准价比较，年度承诺、年付；许可资格、市场及已有订阅需核验。'
    if data.users>300:
        return {'items':[], 'note':'团队超过 300 人，请确认 Enterprise 产品及许可路径，不套用 Business 小团队组合。'}
    with store.connection() as conn:
        prices={}
        for product in (*BASES,*BUNDLES.values(),COPILOT):
            try:
                prices[product]=store.resolve_price(conn,product,engine.today())
            except HTTPException as exc:
                if exc.status_code not in (404,409):
                    raise
        required=2 if data.security_management else (1 if data.desktop_office else 0)
        allowed=[x for x in BASES[required:] if x in prices and prices[x]['kind']=='Base']
        def line(product,seats,group):
            return {'product_id':product,'seats':seats,'user_group':group,'eligibility_confirmed':False,'eligibility_reference':''}
        options=[]
        def option(label,lines,route,tier):
            counts={}
            for value in lines:
                counts[value['product_id']]=counts.get(value['product_id'],0)+value['seats']
            if any(prices[p]['seat_limit'] and n>prices[p]['seat_limit'] for p,n in counts.items()):
                return
            monthly=sum((Decimal(prices[p]['monthly_usd'])*n for p,n in counts.items()),Decimal(0))
            options.append({'label':label,'lines':lines,'products':[{'product_id':p,'name':prices[p]['name'],'version':prices[p]['price_version_id']} for p in counts],
                            'breakdown':[{'product_id':p,'name':prices[p]['name'],'seats':n,'kind':prices[p]['kind'],
                                          'unit_monthly_usd':str(prices[p]['monthly_usd']),'monthly_usd':engine.cash(Decimal(prices[p]['monthly_usd'])*n)} for p,n in counts.items()],
                            'monthly_average_usd':engine.cash(monthly),'annual_usd':engine.cash(monthly*12),
                            'route':route,'tier':tier,'qualification':'正式订购前核验许可资格',
                            'ordinary_users':data.users-data.copilot_users,'copilot_users':data.copilot_users})
        if data.existing_qualifying_base:
            if data.copilot_users and COPILOT in prices:
                option('已有基础许可，仅增购 Copilot',[line(COPILOT,data.copilot_users,'已有许可用户')],'existing',required)
            note+=' 已有合格基础许可不重复计费；没有新增 AI 席位时无需新增订阅。'
        elif allowed or data.users==data.copilot_users:
            # Ordinary users do not need an AI licence. Choose their cheapest
            # qualifying base separately, including a higher tier if it is cheaper.
            ordinary=data.users-data.copilot_users
            def ordinary_lines(ai_lines):
                if not ordinary:
                    return []
                eligible=[]
                for p in allowed:
                    count=ordinary+sum(x['seats'] for x in ai_lines if x['product_id']==p)
                    if not prices[p]['seat_limit'] or count<=prices[p]['seat_limit']:
                        eligible.append(p)
                if not eligible:
                    return None
                base=min(eligible,key=lambda p:(Decimal(prices[p]['monthly_usd']),BASES.index(p)))
                return [line(base,ordinary,'普通办公组')]
            if not data.copilot_users:
                lines=ordinary_lines([])
                if lines:
                    option('满足办公需求的基础订阅',lines,'base',BASES.index(lines[0]['product_id']))
            else:
                for candidate in BASES[required:]:
                    tier=BASES.index(candidate)
                    if candidate in allowed and COPILOT in prices and prices[COPILOT]['kind']=='Add-on':
                        ai=[line(candidate,data.copilot_users,'AI用户组'),line(COPILOT,data.copilot_users,'AI用户组')]
                        ordinary_plan=ordinary_lines(ai)
                        if ordinary_plan is not None:
                            option('基础许可 + Copilot 单独增购',ordinary_plan+ai,'standalone',tier)
                    bundle=BUNDLES.get(candidate)
                    if bundle in prices and prices[bundle]['kind']=='Bundle' and {candidate,COPILOT}.issubset(set(prices[bundle]['components'])):
                        label='商务标准版 + Copilot 套餐' if tier==1 else '商务高级版 + Copilot 套餐'
                        ai=[line(bundle,data.copilot_users,'AI用户组')]
                        ordinary_plan=ordinary_lines(ai)
                        if ordinary_plan is not None:
                            option(label,ordinary_plan+ai,'bundle',tier)
    options.sort(key=lambda x:(Decimal(x['annual_usd']),len(x['breakdown']),x['route']!='bundle',x['tier']))
    baseline=min((Decimal(x['annual_usd']) for x in options if x['route']=='standalone'),default=None)
    for i,value in enumerate(options):
        value['is_recommended']=i==0
        value['annual_extra_usd']=engine.cash(Decimal(value['annual_usd'])-Decimal(options[0]['annual_usd']))
        value['annual_saving_usd']=engine.cash(max(Decimal(0),baseline-Decimal(value['annual_usd']))) if baseline is not None else '0.00'
        value['optional_upgrade']=i>0 and value['tier']>required
    if not options and not data.existing_qualifying_base:
        note+=' 当前已发布价格不足以覆盖所选需求，请管理员补全价格后匹配。'
    return {'items':options,'note':note,'comparison_scope':'满足所选功能及人数的已发布 Business 基础许可、Copilot 附加许可和两款 Bundle；不含促销。'}
