export const CONSENT_TEXT: Record<string, Record<string, string>> = {
  document_processing: {
    mr: "मी SETU ला माझ्या वैद्यकीय कागदपत्रांवर प्रक्रिया करण्यासाठी आणि त्यांचा सोपा सारांश तयार करण्यासाठी संमती देतो/देते. माझा डेटा फक्त याच कारणासाठी वापरला जाईल.",
    hi: "मैं SETU को अपने चिकित्सा दस्तावेज़ों को संसाधित करने और उनका सरल सारांश बनाने के लिए सहमति देता/देती हूँ। मेरा डेटा केवल इसी उद्देश्य के लिए उपयोग किया जाएगा।",
    en: "I consent to SETU processing my medical documents and creating a plain-language summary. My data will be used only for this purpose.",
  },
};

export function consentText(lang: string): string {
  const texts = CONSENT_TEXT.document_processing;
  return texts[lang] ?? texts.en;
}

const CONSENT_KEY = "setu_consent_granted";

export function hasLocalConsent(patientId: string): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(`${CONSENT_KEY}:${patientId}`) === "1";
}

export function markLocalConsent(patientId: string): void {
  localStorage.setItem(`${CONSENT_KEY}:${patientId}`, "1");
}

export function clearLocalConsent(patientId: string): void {
  localStorage.removeItem(`${CONSENT_KEY}:${patientId}`);
}
