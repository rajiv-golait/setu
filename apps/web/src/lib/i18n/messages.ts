export type Locale = "en" | "mr" | "hi";

type Messages = Record<string, string>;

const en: Messages = {
  "nav.home": "Home",
  "nav.summary": "Summary",
  "nav.memory": "Memory",
  "nav.share": "Share",
  "nav.triage": "Symptoms",
  "nav.appointments": "Visits",
  "nav.doctors": "Doctors",
  "nav.vitals": "Vitals",
  "nav.saathi": "Saathi",
  "profile.title": "Health profile",
  "profile.subtitle": "Basic details help doctors prepare for your visit.",
  "profile.save": "Save profile",
  "timeline.title": "Health timeline",
  "timeline.subtitle": "Consultations, documents, vitals, and prescriptions in one view.",
  "timeline.empty": "No events yet. Upload a report or book a consultation.",
  "triage.title": "Check your symptoms",
  "triage.subtitle": "We'll suggest where to seek care — not a diagnosis.",
  "triage.submit": "Get guidance",
  "triage.book": "Book specialist",
  "appointments.title": "Your consultations",
  "appointments.book": "Book a specialist",
  "appointments.empty": "No consultations yet.",
  "vitals.title": "Health readings",
  "vitals.log": "Log a reading",
  "doctor.dashboard": "Consultations",
  "doctor.appointments": "Appointments",
  "worker.dashboard": "My patients",
  "worker.register": "Register patient",
  "admin.dashboard": "Analytics",
  "video.audioOnly": "Low data (audio only)",
  "offline.queued": "reports waiting to upload",
};

const mr: Messages = {
  "nav.home": "मुख्य",
  "nav.summary": "सारांश",
  "nav.memory": "आठवण",
  "nav.share": "शेअर",
  "nav.triage": "लक्षणे",
  "nav.appointments": "भेटी",
  "nav.doctors": "डॉक्टर",
  "nav.vitals": "वाचन",
  "nav.saathi": "साथी",
  "profile.title": "आरोग्य प्रोफाइल",
  "profile.subtitle": "मूलभूत माहिती डॉक्टरांना भेटीसाठी तयार करते.",
  "profile.save": "प्रोफाइल जतन करा",
  "timeline.title": "आरोग्य वेळापत्रक",
  "timeline.subtitle": "भेटी, कागदपत्रे, वाचने आणि प्रिस्क्रिप्शन एका ठिकाणी.",
  "timeline.empty": "अजून कोणतीही घटना नाही.",
  "triage.title": "तुमची लक्षणे तपासा",
  "triage.subtitle": "कुठे उपचार घ्यावे ते सुचवू — निदान नाही.",
  "triage.submit": "मार्गदर्शन मिळवा",
  "triage.book": "तज्ज्ञ भेट ठरवा",
  "appointments.title": "तुमच्या भेटी",
  "appointments.book": "तज्ज्ञ भेट बुक करा",
  "appointments.empty": "अजून कोणतीही भेट नाही.",
  "vitals.title": "आरोग्य वाचन",
  "vitals.log": "वाचन नोंदवा",
  "doctor.dashboard": "सल्ला",
  "doctor.appointments": "भेटी",
  "worker.dashboard": "माझे रुग्ण",
  "worker.register": "रुग्ण नोंदणी",
  "admin.dashboard": "आकडेवारी",
  "video.audioOnly": "कमी डेटा (फक्त ऑडिओ)",
  "offline.queued": "अपलोड प्रतीक्षेत",
};

const hi: Messages = {
  "nav.home": "होम",
  "nav.summary": "सारांश",
  "nav.memory": "याद",
  "nav.share": "शेयर",
  "nav.triage": "लक्षण",
  "nav.appointments": "मुलाकात",
  "nav.doctors": "डॉक्टर",
  "nav.vitals": "रीडिंग",
  "nav.saathi": "साथी",
  "profile.title": "स्वास्थ्य प्रोफ़ाइल",
  "profile.subtitle": "बुनियादी जानकारी डॉक्टरों को तैयारी में मदद करती है।",
  "profile.save": "प्रोफ़ाइल सहेजें",
  "timeline.title": "स्वास्थ्य समयरेखा",
  "timeline.subtitle": "मुलाकात, दस्तावेज़, रीडिंग और नुस्खे एक जगह।",
  "timeline.empty": "अभी कोई घटना नहीं।",
  "triage.title": "अपने लक्षण जाँचें",
  "triage.subtitle": "कहाँ इलाज लें — निदान नहीं।",
  "triage.submit": "मार्गदर्शन पाएँ",
  "triage.book": "विशेषज्ञ बुक करें",
  "appointments.title": "आपकी मुलाकातें",
  "appointments.book": "विशेषज्ञ बुक करें",
  "appointments.empty": "अभी कोई मुलाकात नहीं।",
  "vitals.title": "स्वास्थ्य रीडिंग",
  "vitals.log": "रीडिंग दर्ज करें",
  "doctor.dashboard": "परामर्श",
  "doctor.appointments": "मुलाकात",
  "worker.dashboard": "मेरे मरीज़",
  "worker.register": "मरीज़ पंजीकरण",
  "admin.dashboard": "आँकड़े",
  "video.audioOnly": "कम डेटा (केवल ऑडियो)",
  "offline.queued": "अपलोड प्रतीक्षा में",
};

const tables: Record<Locale, Messages> = { en, mr, hi };

export function t(locale: Locale, key: string): string {
  return tables[locale]?.[key] ?? tables.en[key] ?? key;
}

export function localeFromPref(pref?: string | null): Locale {
  if (pref === "mr" || pref === "hi") return pref;
  return "en";
}
