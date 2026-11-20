"use client";

import { useEffect, useSyncExternalStore } from "react";

export type Lang = "en" | "ar";

const STORAGE_KEY = "albayraq-lang";
const listeners = new Set<() => void>();
let current: Lang | null = null;

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function getSnapshot(): Lang {
  if (current) return current;
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved === "ar" || saved === "en") return saved;
  } catch {
    // Storage can be unavailable (private mode); fall back to English.
  }
  return "en";
}

function getServerSnapshot(): Lang {
  return "en";
}

export function setLang(lang: Lang) {
  current = lang;
  try {
    window.localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    // Ignore: the choice still applies for this visit.
  }
  listeners.forEach((listener) => listener());
}

export function useLang() {
  const lang = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  return { lang, setLang };
}

/** Sets <html lang/dir> while the calling page is mounted, then restores English/LTR. */
export function useDocumentLanguage(lang: Lang) {
  useEffect(() => {
    const root = document.documentElement;
    root.lang = lang;
    root.dir = lang === "ar" ? "rtl" : "ltr";
    return () => {
      root.lang = "en";
      root.dir = "ltr";
    };
  }, [lang]);
}
