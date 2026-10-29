/**
 * Photo library for decorative and contextual imagery. Files live in
 * public/photos/ and are self-hosted, so the browser makes no third-party image
 * requests. Credits (author and licence) are listed in docs/PHOTO-CREDITS.md.
 */
export type PhotoKey =
  | "hero"
  | "produce"
  | "bakery"
  | "coffee"
  | "meals"
  | "market"
  | "herbs"
  | "home"
  | "table"
  | "street";

export interface Photo {
  src: string;
  /** Empty for decorative use; set only when the photo carries meaning on its own. */
  alt: string;
}

export const PHOTOS: Record<PhotoKey, Photo> = {
  hero: { src: "/photos/hero.jpg", alt: "" },
  produce: { src: "/photos/produce.jpg", alt: "" },
  bakery: { src: "/photos/bakery.jpg", alt: "" },
  coffee: { src: "/photos/coffee.jpg", alt: "" },
  meals: { src: "/photos/meals.jpg", alt: "" },
  market: { src: "/photos/market.jpg", alt: "" },
  herbs: { src: "/photos/herbs.jpg", alt: "" },
  home: { src: "/photos/home.jpg", alt: "" },
  table: { src: "/photos/table.jpg", alt: "" },
  street: { src: "/photos/street.jpg", alt: "" },
};

/** Stored category names (see lib/i18n.ts cat_* keys) mapped to a photo. */
const CATEGORY_PHOTO: Record<string, PhotoKey> = {
  Groceries: "produce",
  Meals: "meals",
  MealsEntertainment: "coffee",
  Healthcare: "herbs",
  Housing: "home",
  Utilities: "home",
  Office: "table",
  OfficeSupplies: "table",
  Shopping: "market",
  Transport: "street",
  Transportation: "street",
  Uncategorized: "table",
};

export function photoForCategory(name: string | null | undefined): Photo {
  const key = name ? CATEGORY_PHOTO[name] : undefined;
  return PHOTOS[key ?? "table"];
}

/**
 * Routes that get a photo strip above their content. Pages with their own
 * PhotoBanner (dashboard, receipts, onboarding) are not listed here.
 */
const ROUTE_PHOTO: Record<string, PhotoKey> = {
  "/accounting": "home",
  "/approvals": "table",
  "/budget": "produce",
  "/chat": "coffee",
  "/cost-splits": "table",
  "/exports": "table",
  "/finances": "market",
  "/forecast": "market",
  "/insights": "herbs",
  "/more": "table",
  "/price-tracking": "produce",
  "/reports": "table",
  "/savings-goals": "coffee",
  "/settings": "table",
  "/statement": "table",
  "/subscriptions": "meals",
  "/tax": "home",
  "/upload": "meals",
  "/warranties": "home",
};

export function routePhoto(pathname: string): PhotoKey | null {
  const match = Object.keys(ROUTE_PHOTO).find((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
  return match ? ROUTE_PHOTO[match] : null;
}
