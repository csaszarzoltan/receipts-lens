import useSWR from "swr";
import { getPreferences } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { effectiveBaseCurrency } from "@/lib/utils";

/** The household's working currency: the one it chose, else the locale's currency (HUF only for Hungarian). */
export function useBaseCurrency(): string {
  const { locale } = useTranslation();
  const { data } = useSWR("/product/preferences", getPreferences);
  return effectiveBaseCurrency(data, locale).toUpperCase();
}
