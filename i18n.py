"""Minimal trilingual strings: EN (official), ZH, BN (differentiation)."""
from __future__ import annotations

STR = {
    "en": {
        "greet": "Hello! I am your Cross-border Student Finance Assistant. I can help with budgeting, FX, remittance, tuition and credit building.",
        "clarify_transfer": "To proceed I need: amount, currency, and recipient. Example: 'Send 5000 BDT to Mom'. Who should receive it?",
        "confirm_transfer": "Please confirm: send {amt} {cur} (~{cny} CNY) to {to} via {route}? Reply YES to execute, NO to cancel.",
        "blocked": "Blocked by security policy: {reason}. This attempt has been logged.",
        "need_confirm": "This transfer needs your explicit YES confirmation first.",
        "fallback": "Sorry, I did not fully understand. I can help with: budget summary, FX rate, remittance quote, tuition plan, recurring check. Could you rephrase?",
    },
    "zh": {
        "greet": "你好！我是你的跨境留学生金融助手，可帮你记账、查汇率、汇款、交学费、信用建设。",
        "clarify_transfer": "请补充：金额、币种和收款人。例如：‘给妈妈汇5000塔卡’。请问收款人是谁？",
        "confirm_transfer": "请确认：经由{route}向{to}汇款 {amt} {cur}（约{cny}元）？回复 YES 执行，NO 取消。",
        "blocked": "安全策略拦截：{reason}，已记录审计日志。",
        "need_confirm": "该笔转账需要你明确回复 YES 确认后才能执行。",
        "fallback": "抱歉没完全理解。我可以帮你查预算、汇率、汇款报价、学费计划、订阅检测。请换个说法？",
    },
    "bn": {
        "greet": "হ্যালো! আমি তোমার ক্রস-বর্ডার ফাইন্যান্স অ্যাসিস্ট্যান্ট। বাজেট, FX, রেমিট্যান্স, টিউশন, ক্রেডিট — সবকিছুতেই সাহায্য করব।",
        "clarify_transfer": "এগোতে হলে দরকার: পরিমাণ, কারেন্সি, প্রাপক। যেমন: 'মাকে ৫০০০ টাকা পাঠাও'। প্রাপক কে?",
        "confirm_transfer": "{to} কে {amt} {cur} (~{cny} CNY) পাঠাবো via {route}? নিশ্চিত করতে YES লিখো, বাতিল করতে NO।",
        "blocked": "সিকিউরিটি পলিসিতে ব্লকড: {reason}। লগ করা হয়েছে।",
        "need_confirm": "এই ট্রান্সফারের জন্য আগে স্পষ্ট YES কনফার্মেশন লাগবে।",
        "fallback": "দুঃখিত, পুরো বুঝিনি। আমি বাজেট, FX, রেমিট্যান্স কোট, টিউশন প্ল্যান, রেকারিং চেক করতে পারি। আবার বলো?",
    },
}

def t(lang: str, key: str) -> str:
    lang = (lang or "en").lower()
    if lang not in STR:
        lang = "en"
    return STR[lang].get(key, STR["en"].get(key, key))
