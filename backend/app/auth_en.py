"""Faithful English UI wording for account, admin and policy pages."""

import json
import re


LABELS = {
    '用户服务协议': 'Terms of Service',
    '隐私政策': 'Privacy Policy',
    '账号与登录': 'Account',
    '管理员控制台': 'Admin Console',
    '上海以和信息技术有限公司 · 2026 年 10 月 31 日生效': 'Shanghai Yihe Information Technology Co., Ltd. · Effective October 31, 2026',
    '返回账号页': 'Back to account',
    '查看隐私政策': 'View Privacy Policy',
    '查看用户服务协议': 'View Terms of Service',
    '服务与适用范围': 'Service and scope',
    '本服务提供 Surface 产品配置查询、按需求筛选、能力说明及报告预览和下载。公开游客功能无需注册；内部工作台需完成邮箱验证、管理员审批和有效 License 授权。注册不代表自动获得内部访问权限。': 'This service provides Surface configuration search, needs-based filtering, capability information, and report preview and download. Public guest features require no registration. The internal workspace requires email verification, administrator approval, and a valid license. Registration does not automatically grant internal access.',
    '账号使用': 'Account use',
    '注册时请提供真实的组织名称和可接收验证邮件的邮箱，设置独立密码。请妥善保管账号，不与他人共享；发现异常访问时及时联系我们。管理员可因账号安全、授权到期或违规使用暂停访问。': 'When registering, provide your actual organization name and an email address that can receive verification messages, and set a unique password. Protect your account and do not share it. Contact us promptly if you notice unusual access. Administrators may suspend access for account security, expired authorization, or misuse.',
    '产品资料与报告': 'Product information and reports',
    '配置及价格以所标注的数据来源和更新时间为准，采购前应核对实际料号与报价。官方资料、实测结果、工程估算和未知信息会分别标注；推荐是筛选候选，不构成具体软件兼容性、游戏帧率或模型速度承诺。用户输入需求描述时请勿包含密码、客户机密或无关个人信息。': 'Configurations and prices are subject to the stated sources and update dates. Verify the actual Part Number and quote before purchasing. Official information, measured results, engineering estimates, and unknowns are labeled separately. Recommendations identify candidates and do not promise software compatibility, game frame rates, or model speeds. Do not include passwords, customer secrets, or unrelated personal information in needs descriptions.',
    '服务变更与联系': 'Service changes and contact',
    '我们可能因维护、安全或授权变化调整服务，并在合理范围内告知。个人信息处理遵循': 'We may adjust the service for maintenance, security, or authorization changes and provide reasonable notice. Personal information is handled under the ',
    '。有关账号或服务的问题可发送邮件至': '. For account or service questions, email ',
    '《隐私政策》': 'Privacy Policy',
    '《用户服务协议》': 'Terms of Service',
    '处理者与收集范围': 'Operator and information collected',
    '上海以和信息技术有限公司运营本服务。注册时收集组织名称、邮箱和密码；密码以不可逆散列形式保存。邮箱验证、密码重置和登录会处理一次性令牌、会话状态及必要的安全审计记录。内部报告会处理您主动提交的用途、预算、软件或模型名称和自由描述；请勿填写客户机密或无关个人信息。公开游客浏览无需提交注册信息。': 'Shanghai Yihe Information Technology Co., Ltd. operates this service. Registration collects organization name, email address, and password; passwords are stored as irreversible hashes. Email verification, password reset, and sign-in process one-time tokens, session state, and necessary security audit records. Internal reports process the uses, budget, software or model names, and free-text descriptions you choose to submit. Do not enter customer secrets or unrelated personal information. Public guest browsing does not require registration details.',
    '目的、方式与保存': 'Purposes, handling, and retention',
    '上述信息仅用于建立和验证账号、管理员审批、管理 License、提供顾问与报告服务、防止滥用及排查安全问题。非管理员在私人设备选择保持登录时，服务端会话最长约 7 天；退出、重置密码或授权失效后可撤销。我们在实现这些目的及履行法律义务所需的期限内保存相关记录，期满后删除或匿名化。报告下载票据为短时、单次使用。': 'This information is used only to create and verify accounts, support administrator approval and license management, provide advisor and report services, prevent abuse, and investigate security issues. For non-administrators choosing to stay signed in on a personal device, server sessions last up to approximately seven days and can be revoked after sign-out, password reset, or loss of authorization. We retain records for the period needed for these purposes and legal obligations, then delete or anonymize them. Report download tickets are short-lived and single-use.',
    '共享与安全': 'Sharing and security',
    '我们不会出售注册信息。提供托管、邮件发送或安全运维所必需的服务商可能按约定处理必要数据；依法要求披露时按法律规定办理。我们采用访问控制、密码散列、HTTPS、会话和审计措施，限制内部人员访问。请勿在共用设备选择保持登录。': 'We do not sell registration information. Service providers needed for hosting, email delivery, or security operations may process necessary data under agreement. Legally required disclosures are handled under applicable law. We use access controls, password hashing, HTTPS, sessions, and audit measures to limit internal access. Do not choose to stay signed in on a shared device.',
    '您的权利': 'Your rights',
    '您可申请查询、更正、删除个人信息、撤回同意或注销账号；撤回同意或注销可能使注册及内部功能无法继续使用。请通过': 'You may request access to, correction or deletion of personal information, withdraw consent, or close your account. Withdrawing consent or closing an account may make registration and internal features unavailable. Contact us at ',
    '联系我们，说明登记邮箱和请求事项；核实身份后我们会按法律要求处理。若政策有重大变化，我们会在服务内提示并按需要重新取得同意。': ' with your registered email address and request. After verifying identity, we will handle it as required by law. If this policy changes materially, we will notify you in the service and seek consent again where required.',
    '其他网站与小程序': 'Other sites and the mini program',
    '小程序可打开 yiheit.net 官网和 surfacedmp.com 顾问页；访问第三方链接时应阅读对应网站的规则。有关官网的信息处理另见': 'The mini program may open the yiheit.net corporate site and the surfacedmp.com advisor. Read the rules of other sites when following external links. For information handling on the corporate site, see its ',
    '官网隐私政策': 'privacy policy',
    '。本政策适用于本顾问的注册与使用。': '. This policy applies to registration and use of this advisor.',
    'Capability Advisor 账号': 'Capability Advisor account',
    '返回能力顾问': 'Back to advisor',
    '游客体验（无需登录）': 'Guest access (no sign-in)',
    '登录': 'Sign in',
    '邮箱': 'Email',
    '密码': 'Password',
    '管理员动态验证码（已启用 MFA 时填写）': 'Administrator one-time code (if MFA is enabled)',
    '在此设备保持登录 7 天（管理员不适用；请勿在共用设备勾选）': 'Stay signed in for seven days on this device (not available to administrators; avoid on shared devices)',
    '退出': 'Sign out',
    '进入能力顾问（请在当前标签页打开）': 'Open advisor in this tab',
    '注册': 'Register',
    '组织名称': 'Organization name',
    '密码（至少 12 位）': 'Password (at least 12 characters)',
    '我已阅读并同意': 'I have read and agree to the ',
    '，知悉注册信息的使用目的、方式和范围': ' and understand the purpose, method, and scope of registration data use',
    '提交注册': 'Submit registration',
    '邮箱验证': 'Email verification',
    '注册后输入邮件中的一次性验证码；验证码有效期为 24 小时。验证完成后，还需等待管理员审批和组织 License 授权。': 'After registering, enter the one-time code from your email. It expires after 24 hours. You must then wait for administrator approval and an organization license.',
    '登记邮箱': 'Registered email',
    '邮箱验证码': 'Email verification code',
    '确认邮箱': 'Verify email',
    '重发验证码': 'Resend code',
    '重置密码': 'Reset password',
    '申请后请从已配置的邮件通道获取 30 分钟有效的一次性令牌。本地开发仅在显式开启开发令牌时显示令牌。': 'Request a one-time token through the configured email channel. It is valid for 30 minutes. Local development shows a token only when development tokens are explicitly enabled.',
    '申请重置': 'Request reset',
    '重置令牌': 'Reset token',
    '新密码（至少 12 位）': 'New password (at least 12 characters)',
    '更新密码并撤销旧会话': 'Update password and revoke old sessions',
    '当前账号': 'Current account',
    '尚未登录': 'Not signed in',
    '账号页': 'Account page',
    '能力顾问': 'Capability advisor',
    '使用账号页登录管理员后刷新。': 'Sign in as an administrator on the account page, then refresh.',
    '管理员动态验证码（MFA）': 'Administrator one-time code (MFA)',
    '受保护部署必须先启用 MFA 才能审批用户或管理 License。请在安全设备上的验证器应用手动添加下述密钥；不要截图、转发或记录在工单中。启用后所有旧会话会失效。': 'Protected deployments require MFA before user approval or license management. Add the key below manually to an authenticator on a secure device. Do not screenshot, forward, or record it in a ticket. Enabling MFA invalidates all previous sessions.',
    '再次输入管理员密码': 'Re-enter administrator password',
    '获取验证器密钥': 'Get authenticator key',
    '验证器当前 6 位动态码': 'Current six-digit authenticator code',
    '启用 MFA': 'Enable MFA',
    '用户审批': 'User approval',
    'License 设置': 'License settings',
    '组织': 'Organization',
    '请选择组织': 'Select an organization',
    '席位': 'Seats',
    '到期时间': 'Expiry',
    '保存 License': 'Save license',
    '最近审计': 'Recent audit',
    '© 2026 上海以和信息技术有限公司 ·': '© 2026 Shanghai Yihe Information Technology Co., Ltd. ·',
}


def translate_auth(page: str, section: str) -> str:
    page = page.replace('<html lang="zh-CN">', '<html lang="en">', 1)
    parts = re.split(r'(<script\b[^>]*>.*?</script>|<style\b[^>]*>.*?</style>)', page, flags=re.S | re.I)
    for position in range(0, len(parts), 2):
        for source, target in sorted(LABELS.items(), key=lambda item: len(item[0]), reverse=True):
            parts[position] = parts[position].replace(source, target)
    page = ''.join(parts)
    page = page.replace(f'href="/{section}" aria-current="page"', f'href="/{section}"', 1)
    for target in ('account', 'terms', 'privacy', 'admin'):
        page = page.replace(f'href="/{target}"', f'href="/en/{target}"')
    page = page.replace(f'href="/en/{section}">中文', f'href="/{section}">中文', 1)
    page = page.replace(f'href="/en/{section}">English', f'href="/en/{section}" aria-current="page">English', 1)
    page = page.replace('href="/"', 'href="/en"')
    page = page.replace('href="/guest"', 'href="/en"')
    if section == 'account':
        page = page.replace("return ['/surface','/workplace','/workplace/admin'].includes(next)?next:'/';",
                            "return ({'/surface':'/en/surface','/workplace':'/en/workplace','/workplace/admin':'/workplace/admin'})[next]||'/en';")
    runtime = '''<script>(function(){const labels=__LABELS__;function update(node){if(node.nodeType===3){const text=node.nodeValue,trimmed=text.trim();if(labels[trimmed])node.nodeValue=text.replace(trimmed,labels[trimmed]);return}if(node.nodeType!==1||node.closest('script,style'))return;const walker=document.createTreeWalker(node,NodeFilter.SHOW_TEXT);while(walker.nextNode())update(walker.currentNode)}const observer=new MutationObserver(records=>{for(const record of records)for(const node of record.addedNodes)update(node)});observer.observe(document.body,{childList:true,subtree:true});})();</script>'''.replace('__LABELS__', json.dumps(LABELS, ensure_ascii=False))
    return page.replace('</body>', runtime + '</body>', 1)
