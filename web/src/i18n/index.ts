import { en, type MessageKey } from './en';
import { fr } from './fr';

export type Lang = 'en' | 'fr';
export const LANGS: readonly Lang[] = ['en', 'fr'];

const dictionaries: Record<Lang, Record<MessageKey, string>> = { en, fr };
const STORAGE_KEY = 'blinkguard.lang';

let current: Lang = 'en';
const listeners = new Set<(lang: Lang) => void>();

/** Saved choice first, then the browser language, then English. */
export function detectLang(saved: string | null, browserLangs: readonly string[]): Lang {
  if (saved === 'en' || saved === 'fr') return saved;
  for (const l of browserLangs) {
    const base = l.toLowerCase().slice(0, 2);
    if (base === 'fr' || base === 'en') return base;
  }
  return 'en';
}

export function format(template: string, vars: Record<string, string | number> = {}): string {
  return template.replace(/\{(\w+)\}/g, (match, name: string) => (name in vars ? String(vars[name]) : match));
}

export function t(key: MessageKey, vars?: Record<string, string | number>): string {
  return format(dictionaries[current][key], vars);
}

export function getLang(): Lang {
  return current;
}

export function onLangChange(listener: (lang: Lang) => void): void {
  listeners.add(listener);
}

export function setLang(lang: Lang): void {
  current = lang;
  document.documentElement.lang = lang;
  try {
    localStorage.setItem(STORAGE_KEY, lang);
  } catch {
    // Storage blocked (private mode): the choice simply isn't remembered.
  }
  applyTranslations(document);
  listeners.forEach((listener) => listener(lang));
}

export function initLang(): void {
  let saved: string | null = null;
  try {
    saved = localStorage.getItem(STORAGE_KEY);
  } catch {
    saved = null;
  }
  setLang(detectLang(saved, navigator.languages ?? [navigator.language]));
}

/**
 * Fills static markup:
 * data-i18n -> text, data-i18n-label -> aria-label, data-i18n-title -> title.
 */
export function applyTranslations(root: ParentNode): void {
  root.querySelectorAll<HTMLElement>('[data-i18n]').forEach((el) => {
    el.textContent = t(el.dataset.i18n as MessageKey);
  });
  root.querySelectorAll<HTMLElement>('[data-i18n-label]').forEach((el) => {
    el.setAttribute('aria-label', t(el.dataset.i18nLabel as MessageKey));
  });
  root.querySelectorAll<HTMLElement>('[data-i18n-title]').forEach((el) => {
    el.title = t(el.dataset.i18nTitle as MessageKey);
  });
}

export type { MessageKey };
