from pathlib import Path
import sqlite3
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
DB = Path(__file__).resolve().parent / "app.db"
FRONTEND.mkdir(exist_ok=True)

app = FastAPI(title="CareerSaathi - Vocational Career Counselling", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

TRADES = [
    {"id": 1, "title": "Solar PV Technician", "sector": "Green Energy", "interests": ["Electrical", "Technology"], "education": ["10th", "12th", "ITI", "Diploma"], "duration": "Depends on approved course", "skills": ["Electrical basics", "Safety", "Troubleshooting"], "pathway": "Trainee → Technician → Site Supervisor → Advanced training", "family_note": "Check certification, practical labs, electrical safety and employer links."},
    {"id": 2, "title": "Electrician", "sector": "Electrical & Infrastructure", "interests": ["Electrical", "Manufacturing"], "education": ["10th", "12th", "ITI", "Diploma"], "duration": "Depends on approved course", "skills": ["Wiring", "Testing", "Electrical safety"], "pathway": "Apprentice → Electrician → Senior Technician → Supervisor", "family_note": "Confirm workshop access, PPE, instructor qualifications and apprenticeship support."},
    {"id": 3, "title": "Computer & IT Support Technician", "sector": "IT & Digital Services", "interests": ["Technology", "Electronics", "Retail"], "education": ["10th", "12th", "ITI", "Diploma", "Graduate"], "duration": "Often 3–12 months; verify provider", "skills": ["Hardware", "Operating systems", "Customer support"], "pathway": "Helpdesk Trainee → IT Support → Network / Cloud support with more learning", "family_note": "Check hands-on troubleshooting practice and updated equipment."},
    {"id": 4, "title": "Automotive Service Technician", "sector": "Automotive", "interests": ["Automobile", "Electrical", "Technology"], "education": ["10th", "12th", "ITI", "Diploma"], "duration": "Depends on course and specialisation", "skills": ["Vehicle inspection", "Tools", "Diagnostics", "Safety"], "pathway": "Workshop Trainee → Service Technician → Diagnostic Specialist", "family_note": "Visit the workshop and ask about tools, PPE and placement records."},
    {"id": 5, "title": "Healthcare Support Assistant", "sector": "Healthcare", "interests": ["Healthcare", "Hospitality"], "education": ["10th", "12th"], "duration": "Verify recognised course requirements", "skills": ["Patient assistance", "Communication", "Hygiene", "Safety"], "pathway": "Trainee → Support role → Specialised training where eligible", "family_note": "Verify recognition, supervised practice, safeguarding and shift expectations."},
    {"id": 6, "title": "Electronics Repair Technician", "sector": "Electronics", "interests": ["Electronics", "Technology", "Manufacturing"], "education": ["10th", "12th", "ITI", "Diploma"], "duration": "Depends on course", "skills": ["Circuit basics", "Soldering", "Testing", "Fault finding"], "pathway": "Repair Trainee → Service Technician → Specialist", "family_note": "Check lab equipment, safe handling and certificate recognition."},
    {"id": 7, "title": "Welding Technician", "sector": "Manufacturing", "interests": ["Manufacturing", "Automobile", "Electrical"], "education": ["10th", "12th", "ITI"], "duration": "Depends on trade and certification", "skills": ["Welding", "Measurement", "PPE", "Quality checks"], "pathway": "Trainee → Welder → Certified specialist → Supervisor with experience", "family_note": "Inspect ventilation, protective gear and workshop supervision."},
    {"id": 8, "title": "Retail & Customer Service Associate", "sector": "Retail & Business Services", "interests": ["Retail", "Technology", "Hospitality"], "education": ["10th", "12th"], "duration": "Varies by provider", "skills": ["Communication", "Digital billing", "Teamwork"], "pathway": "Associate → Senior Associate → Store Operations", "family_note": "Ask about hours, transport, safety, internships and advancement."},
    {"id": 9, "title": "Food Production Assistant", "sector": "Hospitality & Food Services", "interests": ["Hospitality", "Retail"], "education": ["10th", "12th"], "duration": "Depends on programme", "skills": ["Food hygiene", "Preparation", "Teamwork", "Quality"], "pathway": "Trainee → Production Assistant → Section lead with experience", "family_note": "Verify hygiene standards, practical training and shift arrangements."},
    {"id": 10, "title": "Refrigeration & AC Technician", "sector": "Building Services", "interests": ["Electrical", "Technology", "Manufacturing"], "education": ["10th", "12th", "ITI", "Diploma"], "duration": "Depends on course and certification", "skills": ["Installation", "Maintenance", "Fault diagnosis", "Safety"], "pathway": "Trainee → Service Technician → Senior Technician / service business", "family_note": "Check practical hours, tools and safe refrigerant handling."},
]

INTERESTS = ["Electronics", "Electrical", "Technology", "Automobile", "Healthcare", "Manufacturing", "Retail", "Hospitality"]
CONCERNS = ["Salary", "Job security", "Career growth", "Safety", "Further education", "Training quality", "Family acceptance", "Travel and location"]


def connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS profiles(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            education TEXT NOT NULL,
            location TEXT NOT NULL,
            language TEXT NOT NULL,
            interests TEXT NOT NULL,
            concerns TEXT NOT NULL,
            created_at TEXT NOT NULL)"""
        )
        c.execute(
            """CREATE TABLE IF NOT EXISTS counsellor_requests(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            contact TEXT NOT NULL,
            preferred_language TEXT NOT NULL,
            concern TEXT NOT NULL,
            message TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT NOT NULL)"""
        )


init_db()


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Profile:
    def __init__(self, student_name: str, education: str, location: str, language: str = "English", interests: list[str] | None = None, concerns: list[str] | None = None):
        self.student_name = student_name
        self.education = education
        self.location = location
        self.language = language
        self.interests = interests or []
        self.concerns = concerns or []


class ChatRequest:
    def __init__(self, message: str, language: str = "English", trade: str | None = None):
        self.message = message
        self.language = language
        self.trade = trade


class CounsellorRequest:
    def __init__(self, student_name: str, contact: str, preferred_language: str = "English", concern: str = "", message: str = ""):
        self.student_name = student_name
        self.contact = contact
        self.preferred_language = preferred_language
        self.concern = concern
        self.message = message


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "CareerSaathi"}


@app.get("/api/trades")
def trades():
    return {"trades": TRADES, "interests": INTERESTS, "concerns": CONCERNS}


@app.post("/api/profile")
def save_profile(payload: dict):
    student_name = (payload.get("student_name") or "").strip()
    education = payload.get("education") or ""
    location = (payload.get("location") or "").strip()
    language = payload.get("language") or "English"
    interests = payload.get("interests") or []
    concerns = payload.get("concerns") or []

    if len(student_name) < 2:
        raise HTTPException(400, "Student name is required.")
    if not interests:
        raise HTTPException(400, "Choose at least one listed interest.")

    valid_interests = [x for x in interests if x in INTERESTS]
    if not valid_interests:
        raise HTTPException(400, "Choose at least one listed interest.")

    with connect() as c:
        cur = c.execute(
            "INSERT INTO profiles(student_name,education,location,language,interests,concerns,created_at) VALUES(?,?,?,?,?,?,?)",
            (student_name, education, location, language, ", ".join(valid_interests), ", ".join(concerns), now()),
        )
        profile_id = cur.lastrowid
    return {"ok": True, "profile_id": profile_id, "message": "Assessment saved in the local demo database."}


@app.post("/api/recommendations")
def recommend(payload: dict):
    selected = set(payload.get("interests") or [])
    scored = []
    for trade in TRADES:
        overlap = selected.intersection(trade["interests"])
        score = len(overlap) * 3 + (2 if payload.get("education") in trade["education"] else 0)
        score += 1 if set(payload.get("concerns") or []).intersection({"Safety", "Training quality", "Further education"}) else 0
        item = dict(trade)
        item["match_score"] = min(98, 55 + score * 5)
        item["matched_interests"] = sorted(overlap)
        item["explanation"] = "Connects with " + (", ".join(sorted(overlap)) if overlap else "your wider career exploration") + ". Check official entry requirements before enrolling."
        scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return {
        "ok": True,
        "notice": "Rule-based demo matches only. They do not guarantee admission, employment or salary. Trade details are sample data and must be verified.",
        "recommendations": [item for _, item in scored[:5]],
    }


CHAT_ANSWERS = {
    "English": {
        "salary": "Pay varies by location, skill level, certification, and employer. Check local vacancies and ask providers for verifiable placement records.",
        "safety": "Visit the provider and ask about lab or workshop safety, protective equipment, supervision, travel, work hours, and complaint procedures.",
        "education": "Some vocational routes can lead to further education. Ask for official progression rules and check whether the qualification is recognised.",
        "family": "Discuss recognition, fees, safety, travel, and progression options together before deciding.",
        "default": "Use the assessment to compare options, then verify recognition, total fees, practical training, local job evidence, safety, and further-study eligibility with the provider.",
    },
    "Telugu": {
        "salary": "జీతం ప్రాంతం, నైపుణ్యం, ధృవీకరణ మరియు ఉద్యోగదాతపై ఆధారపడి మారుతుంది. స్థానిక ఉద్యోగ ప్రకటనలు, సంస్థల ప్లేస్‌మెంట్ రికార్డులను పరిశీలించండి.",
        "safety": "సంస్థను సందర్శించి ప్రయోగశాల భద్రత, రక్షణ పరికరాలు, పర్యవేక్షణ, ప్రయాణం, పని గంటలు, ఫిర్యాదు విధానం గురించి అడగండి.",
        "education": "కొన్ని వృత్తి విద్యా మార్గాల తర్వాత మరింత చదువు సాధ్యమవుతుంది. అధికారిక అర్హతలు, గుర్తింపు వివరాలను అడగండి.",
        "family": "నిర్ణయం తీసుకునే ముందు గుర్తింపు, ఫీజులు, భద్రత, ప్రయాణం మరియు పురోగతి అవకాశాల గురించి కుటుంబంగా చర్చించండి.",
        "default": "ఎంపికలను పోల్చడానికి అంచనాను ఉపయోగించండి. గుర్తింపు, మొత్తం ఫీజులు, ప్రాయోగిక శిక్షణ, స్థానిక ఉద్యోగ ఆధారాలు, భద్రతను సంస్థతో ధృవీకరించండి.",
    },
    "Hindi": {
        "salary": "वेतन स्थान, कौशल, प्रमाणपत्र और नियोक्ता के अनुसार बदलता है। स्थानीय नौकरियों और संस्थानों के सत्यापित प्लेसमेंट रिकॉर्ड देखें।",
        "safety": "संस्थान जाकर प्रयोगशाला की सुरक्षा, सुरक्षा उपकरण, निगरानी, यात्रा, काम के घंटे और शिकायत प्रक्रिया पूछें।",
        "education": "कुछ व्यावसायिक पाठ्यक्रमों के बाद आगे की पढ़ाई संभव है। आधिकारिक पात्रता और मान्यता की जानकारी लें।",
        "family": "निर्णय से पहले परिवार के साथ मान्यता, फीस, सुरक्षा, यात्रा और आगे बढ़ने के विकल्पों पर चर्चा करें।",
        "default": "विकल्पों की तुलना के लिए आकलन का उपयोग करें। मान्यता, कुल फीस, व्यावहारिक प्रशिक्षण, स्थानीय नौकरी के प्रमाण और सुरक्षा की पुष्टि करें।",
    },
    "Marathi": {
        "salary": "वेतन ठिकाण, कौशल्य, प्रमाणपत्र आणि नियोक्त्यानुसार बदलते. स्थानिक नोकऱ्या व संस्थांचे पडताळलेले प्लेसमेंट रेकॉर्ड तपासा.",
        "safety": "संस्थेला भेट देऊन प्रयोगशाळेची सुरक्षितता, सुरक्षा साधने, देखरेख, प्रवास, कामाचे तास आणि तक्रार प्रक्रिया विचारा.",
        "education": "काही व्यावसायिक अभ्यासक्रमांनंतर पुढील शिक्षण शक्य असते. अधिकृत पात्रता आणि मान्यतेची माहिती घ्या.",
        "family": "निर्णयापूर्वी मान्यता, शुल्क, सुरक्षितता, प्रवास आणि प्रगतीच्या पर्यायांवर कुटुंबासह चर्चा करा.",
        "default": "पर्यायांची तुलना करण्यासाठी मूल्यांकन वापरा. मान्यता, एकूण शुल्क, प्रत्यक्ष प्रशिक्षण, स्थानिक नोकरीचे पुरावे आणि सुरक्षितता तपासा.",
    },
    "Kannada": {
        "salary": "ವೇತನವು ಸ್ಥಳ, ಕೌಶಲ್ಯ, ಪ್ರಮಾಣಪತ್ರ ಮತ್ತು ಉದ್ಯೋಗದಾತರ ಆಧಾರದ ಮೇಲೆ ಬದಲಾಗುತ್ತದೆ. ಸ್ಥಳೀಯ ಉದ್ಯೋಗಗಳು ಮತ್ತು ಪರಿಶೀಲಿಸಿದ ಉದ್ಯೋಗ ದಾಖಲೆಗಳನ್ನು ನೋಡಿ.",
        "safety": "ಸಂಸ್ಥೆಗೆ ಭೇಟಿ ನೀಡಿ ಪ್ರಯೋಗಾಲಯದ ಸುರಕ್ಷತೆ, ರಕ್ಷಣಾ ಸಾಧನಗಳು, ಮೇಲ್ವಿಚಾರಣೆ, ಪ್ರಯಾಣ, ಕೆಲಸದ ಸಮಯ ಮತ್ತು ದೂರು ಪ್ರಕ್ರಿಯೆ ಬಗ್ಗೆ ಕೇಳಿ.",
        "education": "ಕೆಲವು ವೃತ್ತಿಪರ ಶಿಕ್ಷಣದ ನಂತರ ಮುಂದಿನ ವಿದ್ಯಾಭ್ಯಾಸ ಸಾಧ್ಯ. ಅಧಿಕೃತ ಅರ್ಹತೆ ಮತ್ತು ಮಾನ್ಯತೆಯ ವಿವರಗಳನ್ನು ಕೇಳಿ.",
        "family": "ನಿರ್ಧಾರಕ್ಕೂ ಮೊದಲು ಮಾನ್ಯತೆ, ಶುಲ್ಕ, ಸುರಕ್ಷತೆ, ಪ್ರಯಾಣ ಮತ್ತು ಮುಂದಿನ ಅವಕಾಶಗಳ ಬಗ್ಗೆ ಕುಟುಂಬದೊಂದಿಗೆ ಚರ್ಚಿಸಿ.",
        "default": "ಆಯ್ಕೆಗಳನ್ನು ಹೋಲಿಸಲು ಮೌಲ್ಯಮಾಪನ ಬಳಸಿ. ಮಾನ್ಯತೆ, ಒಟ್ಟು ಶುಲ್ಕ, ಪ್ರಾಯೋಗಿಕ ತರಬೇತಿ, ಸ್ಥಳೀಯ ಉದ್ಯೋಗದ ಸಾಕ್ಷ್ಯ ಮತ್ತು ಸುರಕ್ಷತೆಯನ್ನು ಪರಿಶೀಲಿಸಿ.",
    },
    "Tamil": {
        "salary": "சம்பளம், இடம், திறன், சான்றிதழ் மற்றும் பணியமர்த்துபவரைப் பொறுத்து மாறும். உள்ளூர் வேலைவாய்ப்புகளையும் சரிபார்க்கப்பட்ட வேலைவாய்ப்பு பதிவுகளையும் பாருங்கள்.",
        "safety": "நிறுவனத்திற்குச் சென்று ஆய்வகப் பாதுகாப்பு, பாதுகாப்பு உபகரணங்கள், மேற்பார்வை, பயணம், வேலை நேரம் மற்றும் புகார் நடைமுறை பற்றி கேளுங்கள்.",
        "education": "சில தொழிற்கல்விப் பாதைகளுக்குப் பிறகு மேல்படிப்பு தொடரலாம். அதிகாரப்பூர்வ தகுதி மற்றும் அங்கீகார விவரங்களைக் கேளுங்கள்.",
        "family": "முடிவெடுப்பதற்கு முன் அங்கீகாரம், கட்டணம், பாதுகாப்பு, பயணம் மற்றும் முன்னேற்ற வாய்ப்புகளை குடும்பத்துடன் விவாதியுங்கள்.",
        "default": "விருப்பங்களை ஒப்பிட மதிப்பீட்டைப் பயன்படுத்துங்கள். அங்கீகாரம், மொத்தக் கட்டணம், நடைமுறைப் பயிற்சி, உள்ளூர் வேலைவாய்ப்பு ஆதாரம் மற்றும் பாதுகாப்பைச் சரிபார்க்கவும்.",
    },
    "Malayalam": {
        "salary": "ശമ്പളം സ്ഥലം, കഴിവ്, സർട്ടിഫിക്കറ്റ്, തൊഴിലുടമ എന്നിവയെ ആശ്രയിച്ച് മാറും. പ്രാദേശിക തൊഴിൽ അവസരങ്ങളും പരിശോധിച്ച പ്ലേസ്മെന്റ് രേഖകളും നോക്കുക.",
        "safety": "സ്ഥാപനം സന്ദർശിച്ച് ലാബ് സുരക്ഷ, സുരക്ഷാ ഉപകരണങ്ങൾ, മേൽനോട്ടം, യാത്ര, ജോലി സമയം, പരാതി നടപടികൾ എന്നിവ ചോദിക്കുക.",
        "education": "ചില തൊഴിൽപഠന പാതകൾക്ക് ശേഷം തുടർപഠനം സാധ്യമാണ്. ഔദ്യോഗിക യോഗ്യതയും അംഗീകാരവും ചോദിച്ച് ഉറപ്പാക്കുക.",
        "family": "തീരുമാനിക്കുന്നതിന് മുമ്പ് അംഗീകാരം, ഫീസ്, സുരക്ഷ, യാത്ര, മുന്നേറ്റ സാധ്യതകൾ എന്നിവ കുടുംബമായി ചർച്ച ചെയ്യുക.",
        "default": "ഓപ്ഷനുകൾ താരതമ്യം ചെയ്യാൻ വിലയിരുത്തൽ ഉപയോഗിക്കുക. അംഗീകാരം, ആകെ ഫീസ്, പ്രായോഗിക പരിശീലനം, പ്രാദേശിക തൊഴിൽ തെളിവ്, സുരക്ഷ എന്നിവ പരിശോധിക്കുക.",
    },
    "Bengali": {
        "salary": "বেতন অবস্থান, দক্ষতা, শংসাপত্র ও নিয়োগকর্তার উপর নির্ভর করে। স্থানীয় চাকরি এবং যাচাইকৃত প্লেসমেন্টের তথ্য দেখুন।",
        "safety": "প্রতিষ্ঠানটি ঘুরে দেখুন এবং ল্যাবের নিরাপত্তা, সুরক্ষা সরঞ্জাম, তত্ত্বাবধান, যাতায়াত, কাজের সময় ও অভিযোগের পদ্ধতি সম্পর্কে জিজ্ঞাসা করুন।",
        "education": "কিছু বৃত্তিমূলক শিক্ষার পরে আরও পড়াশোনা করা যায়। সরকারি যোগ্যতা ও স্বীকৃতির তথ্য জেনে নিন।",
        "family": "সিদ্ধান্তের আগে স্বীকৃতি, ফি, নিরাপত্তা, যাতায়াত ও উন্নতির সুযোগ নিয়ে পরিবারের সঙ্গে আলোচনা করুন।",
        "default": "বিকল্প তুলনা করতে মূল্যায়নটি ব্যবহার করুন। স্বীকৃতি, মোট ফি, হাতে-কলমে প্রশিক্ষণ, স্থানীয় চাকরির প্রমাণ ও নিরাপত্তা যাচাই করুন।",
    },
    "Urdu": {
        "salary": "تنخواہ مقام، مہارت، سند اور آجر کے مطابق بدلتی ہے۔ مقامی ملازمتوں اور تصدیق شدہ پلیسمنٹ ریکارڈ دیکھیں۔",
        "safety": "ادارے کا دورہ کریں اور لیب کی حفاظت، حفاظتی سامان، نگرانی، سفر، اوقاتِ کار اور شکایت کے طریقۂ کار کے بارے میں پوچھیں۔",
        "education": "کچھ پیشہ ورانہ راستوں کے بعد مزید تعلیم ممکن ہے۔ سرکاری اہلیت اور منظوری کی معلومات حاصل کریں۔",
        "family": "فیصلے سے پہلے منظوری، فیس، حفاظت، سفر اور ترقی کے مواقع پر خاندان کے ساتھ بات کریں۔",
        "default": "مواقع کا موازنہ کرنے کے لیے جائزہ استعمال کریں۔ منظوری، کل فیس، عملی تربیت، مقامی ملازمت کے ثبوت اور حفاظت کی تصدیق کریں۔",
    },
}


def chat_answer(message: str, language: str):
    q = message.lower()
    intent_words = {
        "salary": ["salary", "pay", "earning", "income", "వేతనం", "జీతం", "वेतन", "पगार", "ವೇತನ", "சம்பளம்", "ശമ്പളം", "বেতন", "تنخواہ"],
        "safety": ["safe", "safety", "security", "risk", "భద్రత", "सुरक्षा", "ಸುರಕ್ಷತೆ", "பாதுகாப்பு", "സുരക്ഷ", "নিরাপত্তা", "حفاظت"],
        "education": ["degree", "study", "further", "education", "చదువు", "शिक्षा", "शिक्षण", "ವಿದ್ಯಾಭ್ಯಾಸ", "கல்வி", "വിദ്യാഭ്യാസം", "শিক্ষা", "تعلیم"],
        "family": ["parent", "family", "parents", "accept", "కుటుంబ", "परिवार", "कुटुंब", "ಕುಟುಂಬ", "குடும்ப", "കുടുംബ", "পরিবার", "خاندان"],
    }
    for intent, keywords in intent_words.items():
        if any(keyword in q for keyword in keywords):
            return CHAT_ANSWERS.get(language, CHAT_ANSWERS["English"])[intent]
    return CHAT_ANSWERS.get(language, CHAT_ANSWERS["English"])["default"]

@app.post("/api/chat")
def chat(payload: dict):
    message = (payload.get("message") or "").strip()
    language = payload.get("language") or "English"
    if not message:
        raise HTTPException(400, "Message cannot be empty.")
    disclaimers = {
        "Telugu": "ఇది నియమాల ఆధారిత నమూనా సహాయకుడు; అర్హత కలిగిన మానవ సలహాదారు కాదు. ముఖ్యమైన వివరాలను అధికారిక సంస్థలతో ధృవీకరించండి.",
        "Hindi": "यह नियम-आधारित नमूना सहायक है, योग्य मानव परामर्शदाता नहीं। महत्वपूर्ण जानकारी आधिकारिक संस्थानों से जांचें।",
        "Marathi": "हा नियमाधारित नमुना सहाय्यक आहे; पात्र मानवी समुपदेशक नाही. महत्त्वाची माहिती अधिकृत संस्थांकडून तपासा.",
        "Kannada": "ಇದು ನಿಯಮಾಧಾರಿತ ಮಾದರಿ ಸಹಾಯಕ; ಅರ್ಹ ಮಾನವ ಸಲಹೆಗಾರರಲ್ಲ. ಮುಖ್ಯ ಮಾಹಿತಿಯನ್ನು ಅಧಿಕೃತ ಸಂಸ್ಥೆಗಳೊಂದಿಗೆ ಪರಿಶೀಲಿಸಿ.",
        "Tamil": "இது விதிமுறை அடிப்படையிலான மாதிரி உதவியாளர்; தகுதியான மனித ஆலோசகர் அல்ல. முக்கியத் தகவல்களை அதிகாரப்பூர்வ நிறுவனங்களிடம் சரிபார்க்கவும்.",
        "Malayalam": "ഇത് നിയമാധിഷ്ഠിത മാതൃകാ സഹായി മാത്രമാണ്; യോഗ്യതയുള്ള മനുഷ്യ കൗൺസിലറല്ല. പ്രധാന വിവരങ്ങൾ ഔദ്യോഗിക സ്ഥാപനങ്ങളുമായി പരിശോധിക്കുക.",
        "Bengali": "এটি নিয়মভিত্তিক নমুনা সহকারী, যোগ্য মানব পরামর্শদাতা নয়। গুরুত্বপূর্ণ তথ্য সরকারি প্রতিষ্ঠানের সঙ্গে যাচাই করুন।",
        "Urdu": "یہ قواعد پر مبنی نمونہ معاون ہے، اہل انسانی مشیر نہیں۔ اہم معلومات کی تصدیق سرکاری اداروں سے کریں۔",
    }
    disclaimer = disclaimers.get(
        language,
        "Rule-based prototype assistant, not a qualified human counsellor. Verify important details with official providers.",
    )
    return {"answer": chat_answer(message, language), "disclaimer": disclaimer}


@app.post("/api/counsellor")
def counsellor(payload: dict):
    student_name = (payload.get("student_name") or "").strip()
    contact = (payload.get("contact") or "").strip()
    preferred_language = payload.get("preferred_language") or "English"
    concern = (payload.get("concern") or "").strip()
    message = (payload.get("message") or "").strip()
    if len(student_name) < 2 or len(contact) < 5 or len(concern) < 2:
        raise HTTPException(400, "Please complete all required details.")
    with connect() as c:
        cur = c.execute(
            "INSERT INTO counsellor_requests(student_name,contact,preferred_language,concern,message,status,created_at) VALUES(?,?,?,?,?,'Pending',?)",
            (student_name, contact, preferred_language, concern, message, now()),
        )
        request_id = cur.lastrowid
    return {"ok": True, "request_id": request_id, "message": "Saved locally. No real counsellor has been contacted."}


@app.get("/api/admin/summary")
def summary():
    with connect() as c:
        profiles = c.execute("SELECT COUNT(*) AS n FROM profiles").fetchone()["n"]
        requests = c.execute("SELECT COUNT(*) AS n FROM counsellor_requests").fetchone()["n"]
        pending = c.execute("SELECT COUNT(*) AS n FROM counsellor_requests WHERE status='Pending'").fetchone()["n"]
        recent = c.execute(
            "SELECT id, student_name, education, location, interests, created_at FROM profiles ORDER BY id DESC LIMIT 5"
        ).fetchall()
        recent_profiles = [dict(row) for row in recent]
    return {
        "profiles_saved": profiles,
        "counsellor_requests": requests,
        "pending_requests": pending,
        "recent_profiles": recent_profiles,
        "note": "Demo dashboard. Use sample data only. Verify details with authorised providers.",
    }


@app.delete("/api/admin/profiles/{profile_id}")
def delete_dashboard_profile(profile_id: int):
    with connect() as c:
        cur = c.execute("DELETE FROM profiles WHERE id=?", (profile_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Profile not found.")
    return {"ok": True, "profile_id": profile_id, "message": "Profile history deleted."}


app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
