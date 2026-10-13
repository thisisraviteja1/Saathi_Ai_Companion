"""
Everything Saathi SAYS from the backend, in English, Hindi and Telugu.
UI labels live in frontend/i18n.js. Use: t("AMOUNT_MISMATCH", "te", bill="₹840", site="₹8,400")
"""
LANGS = ("en", "hi", "te")

_MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
    "hi": ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त",
           "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"],
    "te": ["జనవరి", "ఫిబ్రవరి", "మార్చి", "ఏప్రిల్", "మే", "జూన్", "జూలై", "ఆగస్టు",
           "సెప్టెంబర్", "అక్టోబర్", "నవంబర్", "డిసెంబర్"],
}

_THINGS = {  # what the agent must never type
    "otp": {"en": "OTP", "hi": "OTP", "te": "OTP"},
    "pin": {"en": "PIN", "hi": "PIN", "te": "PIN"},
    "password": {"en": "password", "hi": "पासवर्ड", "te": "పాస్‌వర్డ్"},
    "captcha": {"en": "captcha check", "hi": "कैप्चा", "te": "క్యాప్చా"},
    "biometric": {"en": "fingerprint", "hi": "फ़िंगरप्रिंट", "te": "వేలిముద్ర"},
}

M = {
    # ---------------- intent replies ----------------
    "REPLY_PAY": {
        "en": "Sure. Please show me the bill.",
        "hi": "ज़रूर। कृपया मुझे बिल दिखाइए।",
        "te": "తప్పకుండా. దయచేసి బిల్లు చూపించండి."},
    "REPLY_READ": {
        "en": "Okay. Show me the bill and I will read it for you.",
        "hi": "ठीक है। बिल दिखाइए, मैं पढ़कर सुनाता हूँ।",
        "te": "సరే. బిల్లు చూపించండి, నేను చదివి చెబుతాను."},
    "REPLY_EXPLAIN": {
        "en": "Okay. Show me the paper and I will explain it simply.",
        "hi": "ठीक है। काग़ज़ दिखाइए, मैं आसान भाषा में समझाता हूँ।",
        "te": "సరే. ఆ కాగితం చూపించండి, నేను సులభంగా వివరిస్తాను."},
    "REPLY_STATUS": {
        "en": "Let me check your last task.",
        "hi": "मैं आपका पिछला काम देखता हूँ।",
        "te": "మీ చివరి పనిని చూస్తాను."},
    "REPLY_UNKNOWN": {
        "en": "Sorry, I did not understand. You can say: pay my electricity bill.",
        "hi": "माफ़ कीजिए, मैं समझ नहीं पाया। आप कह सकते हैं: मेरा बिजली का बिल भर दो।",
        "te": "క్షమించండి, నాకు అర్థం కాలేదు. మీరు ఇలా చెప్పవచ్చు: నా కరెంట్ బిల్లు కట్టు."},

    # ---------------- bill reading ----------------
    "BILL_SUMMARY": {
        "en": "Your electricity bill is {amount}, due on {due}.",
        "hi": "आपका बिजली का बिल {amount} है, आख़िरी तारीख़ {due} है।",
        "te": "మీ కరెంట్ బిల్లు {amount}, చెల్లించాల్సిన చివరి తేదీ {due}."},
    "UNREADABLE": {
        "en": "I couldn't read it clearly. Please take another picture in good light.",
        "hi": "मैं साफ़ नहीं पढ़ पाया। कृपया अच्छी रोशनी में दोबारा फ़ोटो लीजिए।",
        "te": "స్పష్టంగా చదవలేకపోయాను. దయచేసి మంచి వెలుతురులో మళ్ళీ ఫోటో తీయండి."},

    # ---------------- safety engine ----------------
    "OFFLINE": {
        "en": "There is no internet right now. I can still explain your bill, but I cannot pay it until the connection is back.",
        "hi": "अभी इंटरनेट नहीं है। मैं बिल समझा सकता हूँ, लेकिन इंटरनेट आने तक भुगतान नहीं कर सकता।",
        "te": "ఇప్పుడు ఇంటర్నెట్ లేదు. బిల్లు వివరించగలను, కానీ కనెక్షన్ వచ్చే వరకు చెల్లించలేను."},
    "ACTION_NOT_ALLOWED": {
        "en": "I am not allowed to do that, so I stopped.",
        "hi": "मुझे यह करने की अनुमति नहीं है, इसलिए मैं रुक गया।",
        "te": "అది చేయడానికి నాకు అనుమతి లేదు, అందుకే ఆగిపోయాను."},
    "AUTH_HANDOFF": {
        "en": "This needs your {thing}. Please enter it yourself — I never handle your {thing}.",
        "hi": "इसके लिए आपका {thing} चाहिए। कृपया इसे ख़ुद डालिए — यह काम मैं कभी नहीं करता।",
        "te": "దీనికి మీ {thing} కావాలి. దయచేసి మీరే నమోదు చేయండి — అది నేను ఎప్పుడూ చేయను."},
    "VALUE_NOT_FROM_BILL": {
        "en": "I was about to type a number that is not on your bill, so I stopped.",
        "hi": "मैं ऐसा नंबर डालने वाला था जो आपके बिल पर नहीं है, इसलिए रुक गया।",
        "te": "మీ బిల్లులో లేని నంబర్ టైప్ చేయబోయాను, అందుకే ఆగిపోయాను."},
    "AMOUNT_LIMIT": {
        "en": "{amount} is more than I am allowed to pay. Please ask a family member to help.",
        "hi": "{amount} मेरी भुगतान सीमा से ज़्यादा है। कृपया परिवार के किसी सदस्य से मदद लीजिए।",
        "te": "{amount} నేను చెల్లించగల పరిమితి కంటే ఎక్కువ. దయచేసి కుటుంబ సభ్యుల సహాయం తీసుకోండి."},
    "PAYMENT_APPROVAL": {
        "en": "I am about to pay {amount} to {provider}. Do you approve?",
        "hi": "मैं {provider} को {amount} का भुगतान करने वाला हूँ। क्या आप अनुमति देते हैं?",
        "te": "నేను {provider} కి {amount} చెల్లించబోతున్నాను. మీరు అనుమతిస్తారా?"},
    "GUARDIAN_NEEDED": {
        "en": "This is a large amount, so I will also ask your family to approve.",
        "hi": "यह बड़ी रकम है, इसलिए मैं आपके परिवार से भी मंज़ूरी लूँगा।",
        "te": "ఇది పెద్ద మొత్తం, అందుకే మీ కుటుంబ సభ్యుల అనుమతి కూడా తీసుకుంటాను."},
    "NO_CONFIRMATION": {
        "en": "I need your approval before paying.",
        "hi": "भुगतान से पहले मुझे आपकी अनुमति चाहिए।",
        "te": "చెల్లించే ముందు మీ అనుమతి కావాలి."},
    "UNTRUSTED_SITE": {
        "en": "I cannot verify '{domain}'. It may not be the real service. I have stopped and will not enter any details here.",
        "hi": "मैं '{domain}' की पुष्टि नहीं कर पा रहा। यह असली सेवा नहीं हो सकती। मैं रुक गया हूँ और यहाँ कोई जानकारी नहीं डालूँगा।",
        "te": "'{domain}' ని నేను ధృవీకరించలేను. ఇది అసలైన సేవ కాకపోవచ్చు. నేను ఆగిపోయాను, ఇక్కడ ఎలాంటి వివరాలు నమోదు చేయను."},
    "AMOUNT_MISMATCH": {
        "en": "Careful: your bill says {bill} but this website is asking for {site}. The amounts do not match, so I have stopped.",
        "hi": "सावधान: आपके बिल पर {bill} लिखा है, लेकिन यह वेबसाइट {site} माँग रही है। रकम मेल नहीं खाती, इसलिए मैं रुक गया।",
        "te": "జాగ్రత్త: మీ బిల్లులో {bill} ఉంది, కానీ ఈ వెబ్‌సైట్ {site} అడుగుతోంది. మొత్తాలు సరిపోలలేదు, అందుకే ఆగిపోయాను."},
    "ACCOUNT_MISMATCH": {
        "en": "The account number on the website is different from your bill. I have stopped.",
        "hi": "वेबसाइट पर खाता नंबर आपके बिल से अलग है। मैं रुक गया हूँ।",
        "te": "వెబ్‌సైట్‌లోని ఖాతా నంబర్ మీ బిల్లుతో సరిపోలలేదు. నేను ఆగిపోయాను."},
    "VERIFY_FAILED": {
        "en": "I could not confirm the payment went through. Please do not pay again until we check.",
        "hi": "मैं पुष्टि नहीं कर पाया कि भुगतान हुआ या नहीं। जाँच होने तक दोबारा भुगतान मत कीजिए।",
        "te": "చెల్లింపు జరిగిందో లేదో నిర్ధారించలేకపోయాను. తనిఖీ చేసే వరకు మళ్ళీ చెల్లించవద్దు."},
    "USER_DECLINED": {
        "en": "Okay, I did not pay anything.",
        "hi": "ठीक है, मैंने कुछ भुगतान नहीं किया।",
        "te": "సరే, నేను ఏమీ చెల్లించలేదు."},
    "GUARDIAN_DECLINED": {
        "en": "Your family member did not approve this payment, so I did not pay.",
        "hi": "आपके परिवार के सदस्य ने इस भुगतान को मंज़ूरी नहीं दी, इसलिए मैंने भुगतान नहीं किया।",
        "te": "మీ కుటుంబ సభ్యులు ఈ చెల్లింపును ఆమోదించలేదు, అందుకే చెల్లించలేదు."},
    "USER_CANCELLED": {
        "en": "Okay, I have stopped. Nothing more will happen.",
        "hi": "ठीक है, मैं रुक गया हूँ। आगे कुछ नहीं होगा।",
        "te": "సరే, ఆగిపోయాను. ఇంకేమీ జరగదు."},

    # ---------------- task status (voice: "did my payment go through?") ----------------
    "STATUS_NONE": {
        "en": "You have no tasks yet.",
        "hi": "आपका अभी कोई काम नहीं है।",
        "te": "మీకు ఇంకా పనులు లేవు."},
    "STATUS_DONE": {
        "en": "Yes. Your {amount} bill payment is complete. The transaction number is {txn}.",
        "hi": "हाँ। आपका {amount} का बिल भुगतान पूरा हो गया है। लेन-देन नंबर {txn} है।",
        "te": "అవును. మీ {amount} బిల్లు చెల్లింపు పూర్తయింది. లావాదేవీ నంబర్ {txn}."},
    "STATUS_EXPLAINED": {
        "en": "Last time I read your {amount} bill for you. It is not paid yet.",
        "hi": "पिछली बार मैंने आपका {amount} का बिल पढ़कर सुनाया था। वह अभी भरा नहीं गया है।",
        "te": "గతసారి మీ {amount} బిల్లును చదివి చెప్పాను. అది ఇంకా చెల్లించలేదు."},
    "STATUS_STOPPED": {
        "en": "Your last task did not finish, so no money was paid. {reason}",
        "hi": "आपका पिछला काम पूरा नहीं हुआ, इसलिए कोई पैसा नहीं गया। {reason}",
        "te": "మీ చివరి పని పూర్తి కాలేదు, కాబట్టి డబ్బు ఏమీ చెల్లించలేదు. {reason}"},
    "STATUS_WAITING": {
        "en": "Your last task is still waiting for approval.",
        "hi": "आपका पिछला काम अभी मंज़ूरी का इंतज़ार कर रहा है।",
        "te": "మీ చివరి పని ఇంకా అనుమతి కోసం వేచి ఉంది."},

    # ---------------- plan: what Saathi says / what Learn Mode teaches ----------------
    "S1": {"en": "Opening the {provider} payment service.",
           "hi": "{provider} की भुगतान सेवा खोल रहा हूँ।",
           "te": "{provider} చెల్లింపు సేవను తెరుస్తున్నాను."},
    "L1": {"en": "Open your electricity company's app or website.",
           "hi": "अपनी बिजली कंपनी का ऐप या वेबसाइट खोलिए।",
           "te": "మీ కరెంట్ కంపెనీ యాప్ లేదా వెబ్‌సైట్ తెరవండి."},
    "S2": {"en": "Checking that this is the real service.",
           "hi": "जाँच रहा हूँ कि यह असली सेवा है।",
           "te": "ఇది అసలైన సేవేనా అని చూస్తున్నాను."},
    "L2": {"en": "Check the website name is correct before typing anything.",
           "hi": "कुछ भी लिखने से पहले देखिए कि वेबसाइट का नाम सही है।",
           "te": "ఏదైనా టైప్ చేసే ముందు వెబ్‌సైట్ పేరు సరైనదో చూసుకోండి."},
    "S3": {"en": "Typing your consumer number from the bill.",
           "hi": "बिल से आपका उपभोक्ता नंबर लिख रहा हूँ।",
           "te": "బిల్లులోని మీ కన్స్యూమర్ నంబర్ టైప్ చేస్తున్నాను."},
    "L3": {"en": "Type your consumer number. It is printed on your bill: {cid}.",
           "hi": "अपना उपभोक्ता नंबर लिखिए। यह आपके बिल पर छपा है: {cid}।",
           "te": "మీ కన్స్యూమర్ నంబర్ టైప్ చేయండి. అది మీ బిల్లుపై ఉంటుంది: {cid}."},
    "S4": {"en": "Getting your bill from the service.",
           "hi": "सेवा से आपका बिल ला रहा हूँ।",
           "te": "సేవ నుండి మీ బిల్లును తెస్తున్నాను."},
    "L4": {"en": "Tap 'Get bill'.", "hi": "'Get bill' दबाइए।", "te": "'Get bill' నొక్కండి."},
    "S5": {"en": "Matching the amount with your paper bill.",
           "hi": "रकम को आपके काग़ज़ी बिल से मिला रहा हूँ।",
           "te": "మొత్తాన్ని మీ కాగితపు బిల్లుతో సరిపోలుస్తున్నాను."},
    "L5": {"en": "Check the amount on screen is the same as your bill: {amount}.",
           "hi": "देखिए कि स्क्रीन पर रकम आपके बिल जितनी ही है: {amount}।",
           "te": "స్క్రీన్‌పై మొత్తం మీ బిల్లులో ఉన్నదే అని చూడండి: {amount}."},
    "S6": {"en": "I need your approval.", "hi": "मुझे आपकी अनुमति चाहिए।", "te": "నాకు మీ అనుమతి కావాలి."},
    "L6": {"en": "Only continue if the amount and name are correct.",
           "hi": "रकम और नाम सही हों तभी आगे बढ़िए।",
           "te": "మొత్తం, పేరు సరిగ్గా ఉంటేనే ముందుకు వెళ్ళండి."},
    "S7": {"en": "Making the payment.", "hi": "भुगतान कर रहा हूँ।", "te": "చెల్లింపు చేస్తున్నాను."},
    "L7": {"en": "Tap 'Pay now'. If it asks for an OTP, type the OTP from your SMS yourself.",
           "hi": "'Pay now' दबाइए। अगर OTP माँगे, तो SMS वाला OTP ख़ुद डालिए।",
           "te": "'Pay now' నొక్కండి. OTP అడిగితే, SMS లో వచ్చిన OTP ని మీరే టైప్ చేయండి."},
    "S8": {"en": "Checking the payment went through.",
           "hi": "जाँच रहा हूँ कि भुगतान हो गया।",
           "te": "చెల్లింపు పూర్తయిందో చూస్తున్నాను."},
    "L8": {"en": "Wait for the green success screen and note the transaction number.",
           "hi": "हरी 'सफल' स्क्रीन आने तक रुकिए और लेन-देन नंबर लिख लीजिए।",
           "te": "ఆకుపచ్చ విజయ స్క్రీన్ వచ్చే వరకు వేచి ఉండి, లావాదేవీ నంబర్ రాసుకోండి."},
}

# Synthetic letter for the "Read Anything" demo (used in mock mode / fallback)
DEMO_LETTER = {
    "en": {"title": "Pension office: yearly life certificate",
           "explanation": "This letter is from the pension office. You must give your yearly life certificate "
                          "by 30 November 2026. If you don't, your pension may stop for a while.",
           "actions": ["Go to your bank branch before 30 November 2026",
                       "Carry your Aadhaar card and pension (PPO) number",
                       "Ask the bank for the 'life certificate'"]},
    "hi": {"title": "पेंशन कार्यालय: सालाना जीवन प्रमाण पत्र",
           "explanation": "यह पत्र पेंशन कार्यालय से है। आपको 30 नवंबर 2026 तक अपना सालाना जीवन प्रमाण पत्र देना है। "
                          "ऐसा न करने पर आपकी पेंशन कुछ समय के लिए रुक सकती है।",
           "actions": ["30 नवंबर 2026 से पहले अपनी बैंक शाखा जाइए",
                       "अपना आधार कार्ड और पेंशन (PPO) नंबर साथ ले जाइए",
                       "बैंक में 'जीवन प्रमाण पत्र' के बारे में पूछिए"]},
    "te": {"title": "పెన్షన్ కార్యాలయం: వార్షిక జీవన ధృవీకరణ పత్రం",
           "explanation": "ఈ లేఖ పెన్షన్ కార్యాలయం నుండి వచ్చింది. 2026 నవంబర్ 30 లోపు మీ వార్షిక జీవన ధృవీకరణ "
                          "పత్రం ఇవ్వాలి. ఇవ్వకపోతే మీ పెన్షన్ కొంతకాలం ఆగిపోవచ్చు.",
           "actions": ["2026 నవంబర్ 30 లోపు మీ బ్యాంకు శాఖకు వెళ్ళండి",
                       "మీ ఆధార్ కార్డు, పెన్షన్ (PPO) నంబర్ తీసుకెళ్ళండి",
                       "బ్యాంకులో 'జీవన ధృవీకరణ పత్రం' గురించి అడగండి"]},
}


def norm(lang):
    lang = (lang or "en")[:2].lower()
    return lang if lang in LANGS else "en"


def t(key, lang="en", **kw):
    entry = M[key]
    return entry.get(norm(lang), entry["en"]).format(**kw)


def thing(field, lang):
    return _THINGS.get(field, {}).get(norm(lang), field)


def rupees(n):
    if n is None:
        return "₹—"
    n = float(n)
    return f"₹{n:,.0f}" if n == int(n) else f"₹{n:,.2f}"


def fmt_date(iso, lang="en"):
    try:
        y, m, d = (int(x) for x in str(iso).split("-"))
    except ValueError:
        return str(iso)
    month = _MONTHS[norm(lang)][m - 1]
    return f"{month} {d}" if norm(lang) == "te" else f"{d} {month}"
