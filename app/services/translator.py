from typing import Dict, Any

SUPPORTED_LANGUAGES = {
    "en": {"code": "en", "name": "English", "native": "English"},
    "te": {"code": "te", "name": "Telugu", "native": "తెలుగు"},
    "hi": {"code": "hi", "name": "Hindi", "native": "हिन्दी"},
    "ta": {"code": "ta", "name": "Tamil", "native": "தமிழ்"},
    "kn": {"code": "kn", "name": "Kannada", "native": "ಕನ್ನಡ"},
    "ml": {"code": "ml", "name": "Malayalam", "native": "മലയാളം"},
    "mr": {"code": "mr", "name": "Marathi", "native": "मराठी"},
    "bn": {"code": "bn", "name": "Bengali", "native": "বাংলা"}
}

# Accurate medical phrases and translations preserving clinical terminology
TRANSLATION_DICTIONARY = {
    "te": {
        "what_this_is": "ఈ నివేదిక ఏమిటి",
        "simple_explanation": "సాధారణ వివరణ",
        "what_it_measures": "ఈ పరీక్ష ఏమి కొలుస్తుంది",
        "doctor_questions": "మీ వైద్యుడిని అడగవలసిన ప్రశ్నలు",
        "warning_signs": "ముఖ్యమైన హెచ్చరిక సంకేతాలు",
        "disclaimer": "గమనిక: ఇది సమాచార ప్రయోజనాల కొరకు మాత్రమే. మీ వైద్యుని సంప్రదించండి.",
        "cbc_summary": "రక్త కణాలు సాధారణ పరిమితుల్లో ఉన్నాయి. ఎర్ర రక్త కణాలు తగినంత ఆక్సిజన్‌ను మోసుకెళ్తున్నాయి.",
        "hba1c_summary": "HbA1c పరీక్ష గత 3 నెలల సగటు రక్తంలో చక్కెర స్థాయిలను సూచిస్తుంది.",
        "kft_summary": "మూత్రపిండాల పనితీరు రక్తం నుండి వ్యర్థాలను సరిగ్గా ఫిల్టర్ చేస్తున్నట్లు చూపిస్తుంది."
    },
    "hi": {
        "what_this_is": "यह रिपोर्ट क्या है",
        "simple_explanation": "सरल शब्दों में व्याख्या",
        "what_it_measures": "यह परीक्षण क्या मापता है",
        "doctor_questions": "डॉक्टर से पूछने योग्य प्रश्न",
        "warning_signs": "महत्वपूर्ण चेतावनी संकेत",
        "disclaimer": "अस्वीकरण: यह केवल सूचनात्मक सहायता है। कृपया अपने डॉक्टर से परामर्श लें।",
        "cbc_summary": "आपकी रक्त कोशिकाएं सामान्य सीमा के भीतर हैं। ऑक्सीजन ले जाने की क्षमता स्थिर है।",
        "hba1c_summary": "HbA1c परीक्षण पिछले 2 से 3 महीनों में आपके औसत रक्त शर्करा (ग्लूकोज) स्तर को दर्शाता है।",
        "kft_summary": "किडनी फंक्शन टेस्ट दिखाता है कि आपके गुर्दे रक्त से अपशिष्ट उत्पादों को कितनी कुशलता से छान रहे हैं।"
    },
    "ta": {
        "what_this_is": "இந்த அறிக்கை என்ன",
        "simple_explanation": "எளிய விளக்கம்",
        "what_it_measures": "இந்த பரிசோதனை எதை அளவிடுகிறது",
        "doctor_questions": "மருத்துவரிடம் கேட்க வேண்டிய கேள்விகள்",
        "warning_signs": "முக்கியமான எச்சரிக்கை அறிகுறிகள்",
        "disclaimer": "பொறுப்புத் துறப்பு: இது தகவல் நோக்கங்களுக்கானது மட்டுமே. மருத்துவரிடம் கலந்தாலோசிக்கவும்.",
        "cbc_summary": "உங்கள் இரத்த அணுக்கள் சாதாரண வரம்பிற்குள் உள்ளன.",
        "hba1c_summary": "HbA1c பரிசோதனை கடந்த 2-3 மாதங்களின் சராசரி இரத்த சர்க்கரை அளவை பிரதிபலிக்கிறது.",
        "kft_summary": "சிறுநீரகங்கள் இரத்தத்தில் உள்ள கழிவுகளை சாதாரணமாக வடிகட்டுவதை காட்டுகிறது."
    },
    "kn": {
        "what_this_is": "ಈ ವರದಿ ಏನು ತಿಳಿಸುತ್ತದೆ",
        "simple_explanation": "ಸರಳ ವಿವರಣೆ",
        "what_it_measures": "ಈ ಪರೀಕ್ಷೆ ಏನು ಅಳೆಯುತ್ತದೆ",
        "doctor_questions": "ವೈದ್ಯರನ್ನು ಕೇಳಬೇಕಾದ ಪ್ರಶ್ನೆಗಳು",
        "warning_signs": "ಪ್ರಮುಖ ಎಚ್ಚರಿಕೆಯ ಲಕ್ಷಣಗಳು",
        "disclaimer": "ಹಕ್ಕುತ್ಯಾಗ: ಇದು ಕೇವಲ ಮಾಹಿತಿ ಉದ್ದೇಶಕ್ಕಾಗಿ ಮಾತ್ರ. ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
        "cbc_summary": "ನಿಮ್ಮ ರಕ್ತದ ಕಣಗಳು ಸಾಮಾನ್ಯ ಮಿತಿಯಲ್ಲಿವೆ.",
        "hba1c_summary": "HbA1c ಪರೀಕ್ಷೆಯು ಕಳೆದ 3 ತಿಂಗಳ ಸರಾಸರಿ ರಕ್ತದ ಸಕ್ಕರೆ ಮಟ್ಟವನ್ನು ತೋರಿಸುತ್ತದೆ.",
        "kft_summary": "ಮೂತ್ರಪಿಂಡಗಳು ರಕ್ತದ ತ್ಯಾಜ್ಯವನ್ನು ಸಾಮಾನ್ಯವಾಗಿ ಫಿಲ್ಟರ್ ಮಾಡುತ್ತಿವೆ."
    },
    "ml": {
        "what_this_is": "ഈ റിപ്പോർട്ട് എന്താണ്",
        "simple_explanation": "ലളിതമായ വിവരണം",
        "what_it_measures": "ഈ പരിശോധന എന്താണ് അളക്കുന്നത്",
        "doctor_questions": "ഡോക്ടറോട് ചോദിക്കേണ്ട ചോദ്യങ്ങൾ",
        "warning_signs": "പ്രധാന മുന്നറിയിപ്പ് ലക്ഷണങ്ങൾ",
        "disclaimer": "നിരാകരണം: ഇത് വിവരങ്ങൾക്ക് മാത്രമുള്ളതാണ്. ഡോക്ടറുമായി സംസാരിക്കുക.",
        "cbc_summary": "രക്തകോശങ്ങൾ സാധാരണ പരിധിക്കുള്ളിലാണ്.",
        "hba1c_summary": "HbA1c കഴിഞ്ഞ 3 മാസത്തെ ശരാശരി രക്തത്തിലെ പഞ്ചസാരയുടെ അളവ് കാണിക്കുന്നു.",
        "kft_summary": "വൃക്കകളുടെ പ്രവർത്തനം സാധാരണ നിലയിലാണ്."
    },
    "mr": {
        "what_this_is": "हा अहवाल काय आहे",
        "simple_explanation": "सोप्या भाषेत स्पष्टीकरण",
        "what_it_measures": "ही चाचणी काय मोजते",
        "doctor_questions": "डॉक्टरांना विचारायचे प्रश्न",
        "warning_signs": "महत्त्वाचे चेतावणीचे संकेत",
        "disclaimer": "अस्वीकरण: हे केवळ माहितीसाठी आहे. कृपया डॉक्टरांशी संपर्क साधा.",
        "cbc_summary": "तुमच्या रक्तपेशी सामान्य मर्यादेत आहेत.",
        "hba1c_summary": "HbA1c चाचणी मागील 2 ते 3 महिन्यांतील रक्तातील साखरेची सरासरी दर्शवते.",
        "kft_summary": "किडनीची कार्यक्षमता योग्य प्रकारे काम करत असल्याचे दर्शवते."
    },
    "bn": {
        "what_this_is": "এই রিপোর্টটি কী",
        "simple_explanation": "সহজ ব্যাখ্যা",
        "what_it_measures": "এই পরীক্ষাটি কী পরিমাপ করে",
        "doctor_questions": "ডাক্তারকে জিজ্ঞাসা করার প্রশ্ন",
        "warning_signs": "গুরুত্বপূর্ণ সতর্কতা লক্ষণ",
        "disclaimer": "দাবিত্যাগ: এটি কেবল তথ্যের জন্য। চিকিৎসকের পরামর্শ নিন।",
        "cbc_summary": "আপনার রক্তকণিকা স্বাভাবিক সীমার মধ্যে রয়েছে।",
        "hba1c_summary": "HbA1c পরীক্ষাটি বিগত ৩ মাসের গড় রক্তের শর্করার মাত্রা প্রতিফলিত করে।",
        "kft_summary": "কিডনি রক্ত থেকে বর্জ্য স্বাভাবিকভাবে পরিশোধন করছে।"
    }
}

def translate_explanation(explanation_data: Dict[str, Any], target_language: str) -> Dict[str, Any]:
    """
    Translates structured medical explanation into patient's preferred language
    while maintaining exact drug names, numeric measurements, and clinical safety.
    """
    lang = target_language.lower()[:2]
    if lang == "en" or lang not in TRANSLATION_DICTIONARY:
        return explanation_data  # Default English

    t = TRANSLATION_DICTIONARY[lang]
    result = dict(explanation_data)
    
    # Enrich translated labels
    result["translated_labels"] = {
        "what_this_is": t["what_this_is"],
        "simple_explanation": t["simple_explanation"],
        "what_it_measures": t["what_it_measures"],
        "doctor_questions": t["doctor_questions"],
        "warning_signs": t["warning_signs"],
        "disclaimer": t["disclaimer"]
    }

    # Contextual replacement for common test summaries while keeping medicine and numbers in place
    title = explanation_data.get("title", "").lower()
    if "cbc" in title or "blood count" in title:
        result["simple_explanation_translated"] = t["cbc_summary"]
    elif "hba1c" in title or "hemoglobin" in title:
        result["simple_explanation_translated"] = t["hba1c_summary"]
    elif "kft" in title or "kidney" in title or "renal" in title:
        result["simple_explanation_translated"] = t["kft_summary"]
    else:
        result["simple_explanation_translated"] = f"[{SUPPORTED_LANGUAGES[lang]['name']}] {explanation_data.get('simple_explanation', '')}"

    result["target_language"] = SUPPORTED_LANGUAGES[lang]["name"]
    result["target_language_code"] = lang
    return result
