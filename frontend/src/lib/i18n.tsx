"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import en from "@/messages/en.json";

type Messages = Record<string, unknown>;

interface LocaleContextValue {
  locale: string;
  t: (key: string) => string;
  switchLocale: (locale: string) => Promise<void>;
}

const LocaleContext = createContext<LocaleContextValue>({
  locale: "en",
  t: (key) => key,
  switchLocale: async () => {},
});

function lookup(obj: Messages, key: string): string {
  const parts = key.split(".");
  let cur: unknown = obj;
  for (const p of parts) {
    if (cur == null || typeof cur !== "object") return key;
    cur = (cur as Messages)[p];
  }
  return typeof cur === "string" ? cur : key;
}

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState("en");
  const [messages, setMessages] = useState<Messages>(en as Messages);

  const loadFont = (id: string, href: string) => {
    if (!document.getElementById(id)) {
      const link = document.createElement("link");
      link.id = id;
      link.rel = "stylesheet";
      link.href = href;
      document.head.appendChild(link);
    }
  };

  const switchLocale = async (newLocale: string) => {
    if (newLocale === "my") {
      const mod = await import("@/messages/my.json");
      setMessages(mod.default as Messages);
      loadFont(
        "font-noto-myanmar",
        "https://fonts.googleapis.com/css2?family=Noto+Sans+Myanmar:wght@400;600;700&display=swap"
      );
    } else if (newLocale === "th") {
      const mod = await import("@/messages/th.json");
      setMessages(mod.default as Messages);
      loadFont(
        "font-noto-thai",
        "https://fonts.googleapis.com/css2?family=Noto+Sans+Thai:wght@400;600;700&display=swap"
      );
    } else {
      setMessages(en as Messages);
    }
    setLocale(newLocale);
    document.documentElement.setAttribute("lang", newLocale);
    localStorage.setItem("locale", newLocale);
  };

  useEffect(() => {
    const saved = localStorage.getItem("locale");
    if (saved && saved !== "en") switchLocale(saved);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const t = (key: string) => lookup(messages, key);

  return (
    <LocaleContext.Provider value={{ locale, t, switchLocale }}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale() {
  return useContext(LocaleContext);
}
