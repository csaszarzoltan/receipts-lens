"use client";

import Pill, { type PillTone } from "@/components/Pill";

interface TaxBadgeProps {
  category: string | null | undefined;
}

// Tax categories share the six app tones, so no extra colour family is added.
const TONE: Record<string, PillTone> = {
  "Meals": "wait",
  "Travel": "check",
  "Transportation": "accent",
  "Office": "neutral",
  "Rent": "neutral",
  "Advertising": "neutral",
  "Groceries": "ok",
};

function tone(category: string): PillTone {
  for (const [key, value] of Object.entries(TONE)) {
    if (category.startsWith(key) || category.includes(key)) return value;
  }
  return "neutral";
}

export default function TaxBadge({ category }: TaxBadgeProps) {
  if (!category) return <Pill>—</Pill>;
  return (
    <Pill tone={tone(category)} title={category}>
      {category}
    </Pill>
  );
}
