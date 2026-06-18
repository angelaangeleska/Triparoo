const unsplash = (photoId: string, width = 800) =>
  `https://images.unsplash.com/photo-${photoId}?auto=format&fit=crop&w=${width}&q=80`

/** Verified Unsplash photo IDs — old URLs in this file were returning 404. */
const CITY_IMAGES: Record<string, string> = {
  paris: unsplash('1502602898657-3e91760cbb34'),
  london: unsplash('1513635269975-59663e0ac1ad'),
  rome: unsplash('1552832230-c0197dd311b5'),
  barcelona: unsplash('1753025494922-70b70e0b0308'),
  vienna: unsplash('1745224183815-cc2bbbc6501c'),
  prague: unsplash('1541849546-216549ae216d'),
  amsterdam: unsplash('1536880756060-98a6a140f0a7'),
}

export const DEFAULT_CITY_IMAGE = unsplash('1488646953014-85cb44e25828')

export const HERO_IMAGE = unsplash('1488646953014-85cb44e25828', 1920)

export function getCityImage(city: string | undefined | null): string {
  if (!city) return DEFAULT_CITY_IMAGE
  return CITY_IMAGES[city.trim().toLowerCase()] ?? DEFAULT_CITY_IMAGE
}
