import { describe, expect, it } from 'vitest';
import { en } from './en';
import { fr } from './fr';
import { detectLang, format } from './index';

describe('translations', () => {
  it('French has exactly the same keys as English', () => {
    expect(Object.keys(fr).sort()).toEqual(Object.keys(en).sort());
  });

  it('no translation is empty', () => {
    for (const dict of [en, fr]) {
      for (const [key, value] of Object.entries(dict)) {
        expect(value.trim(), key).not.toBe('');
      }
    }
  });

  it('both languages use the same placeholders', () => {
    const placeholders = (s: string) => (s.match(/\{\w+\}/g) ?? []).sort();
    for (const key of Object.keys(en) as (keyof typeof en)[]) {
      expect(placeholders(fr[key]), key).toEqual(placeholders(en[key]));
    }
  });
});

describe('detectLang', () => {
  it('prefers the saved choice', () => {
    expect(detectLang('fr', ['en-US'])).toBe('fr');
  });

  it('falls back to the browser language', () => {
    expect(detectLang(null, ['fr-FR', 'en'])).toBe('fr');
    expect(detectLang(null, ['de-DE', 'en-GB'])).toBe('en');
  });

  it('defaults to English', () => {
    expect(detectLang('xx', ['de', 'es'])).toBe('en');
  });
});

describe('format', () => {
  it('fills placeholders and keeps unknown ones', () => {
    expect(format('Page {current} of {total} {x}', { current: 2, total: 9 })).toBe('Page 2 of 9 {x}');
  });
});
