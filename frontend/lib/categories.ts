import type { MessageKey } from "@/lib/i18n";

/** Translates a category the app assigned; a name the user typed is shown as written. */
export function categoryLabel(t: (key: MessageKey) => string, name: string | null | undefined): string {
  if (!name) return "—";
  const key = `cat_${name.replace(/[^A-Za-z]/g, "")}` as MessageKey;
  const translated = t(key);
  return translated === key ? name : translated;
}
