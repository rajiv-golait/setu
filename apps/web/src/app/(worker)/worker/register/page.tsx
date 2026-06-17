"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { WorkerShell } from "@/components/layout/role-shells";
import { PrimaryButton } from "@/components/ui/buttons";
import { registerPatientAsWorker } from "@/lib/api";
import { useLocale } from "@/lib/hooks/use-locale";

export default function WorkerRegisterPage() {
  const router = useRouter();
  const { t } = useLocale();
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [lang, setLang] = useState("mr");
  const [rural, setRural] = useState(true);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      const p = await registerPatientAsWorker({
        display_name: name,
        phone: phone || undefined,
        lang_pref: lang,
        is_rural: rural,
      });
      router.push(`/worker/patient/${p.id}`);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Registration failed — API pending");
      setLoading(false);
    }
  };

  return (
    <WorkerShell>
      <h1 className="text-xl font-semibold">{t("worker.register")}</h1>
      <div className="mt-6 space-y-4">
        <input
          placeholder="Patient name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full rounded-card border border-border px-4 py-3"
        />
        <input
          placeholder="Phone (optional)"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          className="w-full rounded-card border border-border px-4 py-3"
        />
        <select
          value={lang}
          onChange={(e) => setLang(e.target.value)}
          className="w-full rounded-card border border-border px-4 py-3"
        >
          <option value="mr">Marathi</option>
          <option value="hi">Hindi</option>
          <option value="en">English</option>
        </select>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={rural} onChange={(e) => setRural(e.target.checked)} />
          Rural patient
        </label>
        <PrimaryButton disabled={!name || loading} onClick={submit}>
          Register & continue
        </PrimaryButton>
      </div>
    </WorkerShell>
  );
}
