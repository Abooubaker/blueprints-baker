"use client";

import { Languages } from "lucide-react";

import { useLang } from "@/lib/i18n";

export function LanguageToggle() {
  const { lang, setLang } = useLang();
  const next = lang === "ar" ? "en" : "ar";

  return (
    <button
      type="button"
      onClick={() => setLang(next)}
      className="lang-toggle"
      aria-label={lang === "ar" ? "Switch to English" : "التبديل إلى العربية"}
    >
      <Languages className="size-4" />
      <span>{lang === "ar" ? "EN" : "عربي"}</span>
    </button>
  );
}
