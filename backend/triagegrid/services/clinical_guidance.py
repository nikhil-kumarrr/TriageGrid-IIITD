"""Small curated reference pathways, not prescription training or diagnosis."""
import re
REVIEWED = "2026-10-25"
SOURCES = {
 "bite": [{"title":"WHO rabies guidance", "url":"https://www.who.int/news-room/fact-sheets/detail/rabies"}, {"title":"NHS animal bites", "url":"https://www.nhs.uk/conditions/animal-and-human-bites/"}],
 "wound": [{"title":"NHS cuts and grazes", "url":"https://www.nhs.uk/conditions/cuts-and-grazes/"}],
 "infection": [{"title":"CDC antibiotic guidance", "url":"https://www.cdc.gov/antibiotic-use/about/"}],
}

def topic(text):
    t=text.casefold()
    if re.search(r"dog|cat|animal|kutt[ae]|billi|कुत्त|बिल्ली|जानवर",t) and re.search(r"bitten|bite|\bbit\b|scratch|kaat|kat liya|kata|kanta|काट|खरोंच",t):
        if not re.search(r"(?:not|never) (?:been )?bitten|(?:nahi|nahin|नहीं) (?:kaat|काट)|(?:kaata|kata|काटा) (?:nahi|nahin|नहीं)",t):return "bite"
    if re.search(r"knee|ghutn|ghutno|घुटन",t):return "knee"
    if re.search(r"wound|open cut|cut on|cut my|ghav|ghaav|घाव|खुली चोट",t):return "wound"
    if re.search(r"infection|infected|संक्रमण",t) and re.search(r"antibiotic|prescri|medicine|dawa|dawai|injection|दवा|इंजेक्शन",t):return "infection"
    return None

COPY = {
 "bite": {
 "English": ("For an actual animal bite or scratch, immediately wash the wound with soap and running water for at least 15 minutes and seek medical assessment promptly. Do not wait for symptoms or a routine home injection. A clinician assesses rabies vaccine, immunoglobulin when indicated, tetanus protection and wound treatment; I cannot choose your injection or prescribe it. Heavy uncontrolled bleeding or severe illness needs emergency care.", "When did the bite or scratch happen?"),
 "Hinglish": ("Agar jaanwar ne sach mein kaata ya scratch kiya hai, wound ko turant sabun aur behte paani se kam-se-kam 15 minute dhoyein aur jaldi medical centre jayein. Symptoms ya routine home injection ka wait na karein. Doctor rabies vaccine, zaroorat par immunoglobulin, tetanus protection aur wound treatment assess karega; main injection prescribe nahi kar sakta. Bahut zyada na rukne wala bleeding ya severe illness ho to emergency help lein.", "Bite ya scratch kab hua tha?"),
 "Hindi": ("जानवर के वास्तविक काटने या खरोंचने पर घाव तुरंत साबुन और बहते पानी से कम से कम 15 मिनट धोएँ और जल्द चिकित्सा केंद्र जाएँ। लक्षण आने या घर पर सामान्य इंजेक्शन का इंतज़ार न करें। डॉक्टर रेबीज़ टीका, आवश्यकता पर इम्युनोग्लोबुलिन, टिटनेस सुरक्षा और घाव का उपचार तय करेगा। मैं इंजेक्शन का प्रिस्क्रिप्शन नहीं दे सकता। बहुत अधिक न रुकने वाला खून या गंभीर हालत में आपातकालीन मदद लें।", "काटने या खरोंचने की घटना कब हुई?"),
 },
 "wound": {
 "English": ("For a small surface cut, rinse with clean running water and cover with a clean dressing. For bleeding, use a clean cloth to apply pressure if nothing is embedded; do not remove an embedded object. Deep wounds, bleeding that will not stop, or spreading redness, swelling, pus or fever need medical assessment. A tetanus injection is not automatic for every injury; a clinician checks the wound and vaccination history.", "Is the wound deep, bleeding continuously, or showing redness or pus?"),
 "Hinglish": ("Chhote surface cut ko saaf behte paani se clean karke clean dressing se cover karein. Bleeding ho aur koi cheez andar na phansi ho to clean cloth se pressure dein; phansi hui cheez na nikalein. Deep wound, na rukne wala bleeding, failti laali, sujan, pus ya bukhar mein medical assessment chahiye. Har chot par tetanus injection automatic nahi hota; doctor wound aur vaccine history check karta hai.", "Kya wound deep hai, bleeding ruk nahi rahi, ya laali/pus hai?"),
 "Hindi": ("छोटे सतही कट को साफ बहते पानी से धोकर साफ ड्रेसिंग से ढकें। खून आने पर, अंदर कोई वस्तु न फँसी हो तो साफ कपड़े से दबाव दें; फँसी वस्तु न निकालें। गहरा घाव, न रुकता खून, फैलती लालिमा, सूजन, मवाद या बुखार में चिकित्सा जाँच चाहिए। हर चोट पर टिटनेस इंजेक्शन आवश्यक नहीं; डॉक्टर घाव और टीकाकरण का इतिहास जाँचेगा।", "क्या घाव गहरा है, खून रुक नहीं रहा या लालिमा/मवाद है?"),
 },
 "infection": {
 "English": ("An infection cannot be identified as bacterial from that word alone. Antibiotics do not treat viruses, and the right treatment depends on the affected area, severity, allergies and assessment. Do not start leftover antibiotics or injections. I can explain treatment information and help you seek care, but cannot issue a prescription.", "Where is the suspected infection?"),
 "Hinglish": ("Sirf infection kehne se bacterial infection confirm nahi hota. Antibiotics virus par kaam nahi karte; treatment jagah, severity, allergy aur assessment par depend karta hai. Bachi hui antibiotic ya injection khud se shuru na karein. Main treatment ki information samjha sakta hoon aur care tak guide kar sakta hoon, prescription issue nahi kar sakta.", "Infection kis jagah par lag raha hai?"),
 "Hindi": ("सिर्फ संक्रमण कहने से बैक्टीरिया वाला संक्रमण तय नहीं होता। एंटीबायोटिक वायरस पर काम नहीं करती; उपचार प्रभावित जगह, गंभीरता, एलर्जी और जाँच पर निर्भर है। बची एंटीबायोटिक या इंजेक्शन खुद शुरू न करें। मैं उपचार की जानकारी और उचित सहायता का रास्ता समझा सकता हूँ, प्रिस्क्रिप्शन जारी नहीं कर सकता।", "संक्रमण किस जगह पर लग रहा है?"),
 }
}

def guidance(text, language):
    key=topic(text)
    if key is None:return None
    message, question=COPY[key][language]
    return {"topic":key,"message":message,"question":question,"sources":SOURCES[key],"reviewed":REVIEWED}


SOURCES["knee"] = [
 {"title":"NHS knee pain self-care", "url":"https://111.wales.nhs.uk/Kneepain/"},
 {"title":"NHS paracetamol suitability", "url":"https://www.nhs.uk/medicines/paracetamol-for-adults/"},
]
COPY["knee"] = {
 "English": ("For knee pain, reduce activities that worsen it. A wrapped cold pack may help; do not put ice directly on skin. Paracetamol is an OTC pain-relief option for some adults, not a treatment for every cause. Check the product label and pharmacist first, especially with liver/kidney disease, allergy, heavy alcohol use or other medicines; do not combine paracetamol-containing products. Children need age-appropriate advice. A hot/red knee with fever, inability to bear weight or a major injury needs urgent assessment.", "What is the patient's age?"),
 "Hinglish": ("Ghutne ke dard mein dard badhane wali activity kam karein. Kapde mein lapeta cold pack madad kar sakta hai; ice seedhe skin par na lagayein. Kuch adults ke liye paracetamol OTC pain-relief option hai, har cause ka ilaaj nahi. Product label aur pharmacist se suitability confirm karein, khaaskar liver/kidney problem, allergy, heavy alcohol use ya doosri medicines mein; do paracetamol wale products saath na lein. Bachchon ki advice alag hai. Garam/laal ghutne ke saath bukhar, pair par weight na rakh pana ya badi chot mein urgent assessment chahiye.", "Patient ki umar kitni hai?"),
 "Hindi": ("घुटने का दर्द बढ़ाने वाली गतिविधि कम करें। कपड़े में लपेटा ठंडा पैक मदद कर सकता है; बर्फ सीधे त्वचा पर न रखें। कुछ वयस्कों में पैरासिटामोल दर्द से राहत का विकल्प है, हर कारण का इलाज नहीं। पैकेट के निर्देश और फार्मासिस्ट से उपयुक्तता जाँचें, खासकर लिवर/किडनी की समस्या, एलर्जी, अधिक शराब या अन्य दवाओं में। पैरासिटामोल वाले दो उत्पाद साथ न लें। बच्चों की सलाह अलग है। गर्म/लाल घुटने के साथ बुखार, पैर पर वजन न रख पाना या बड़ी चोट में तत्काल जाँच चाहिए।", "मरीज़ की उम्र कितनी है?"),
}
