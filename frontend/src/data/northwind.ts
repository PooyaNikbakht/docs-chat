// Typed access to the Northwind facts. northwind.json is generated from
// backend/sample/northwind-facts.md by `make kb`, the same file that writes the help center
// PDF the bot answers from, so the site and the bot always agree.
import data from "./northwind.json";

export type Coffee = (typeof data.coffees)[number];
export type Cafe = (typeof data.cafes)[number];
export type BrewMethod = (typeof data.brewing)[number];

export const nw = data;

export function money(amount: number): string {
  return `$${amount}`;
}

/** "a, b and c" */
export function listing(items: readonly string[]): string {
  if (items.length < 2) return items.join("");
  return `${items.slice(0, -1).join(", ")} and ${items[items.length - 1]}`;
}

export function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export const ROAST_LEVELS = ["Light", "Medium", "Medium-dark"] as const;

export function roastStep(roast: string): number {
  return Math.max(0, ROAST_LEVELS.indexOf(roast as (typeof ROAST_LEVELS)[number])) + 1;
}

export function sundayHours(cafe: Cafe): string {
  return cafe.sunday === "closed" ? "Closed" : cafe.sunday;
}

/** "7:30 am" -> "07:30" */
function to24h(time: string): string {
  const m = /^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$/.exec(time.trim());
  if (!m) return time;
  const hour = (Number(m[1]) % 12) + (m[3] === "pm" ? 12 : 0);
  return `${String(hour).padStart(2, "0")}:${m[2] ?? "00"}`;
}

function openingHours(days: string[], range: string) {
  if (range === "closed") return [];
  const [opens, closes] = range.split(" to ");
  return [{ "@type": "OpeningHoursSpecification", dayOfWeek: days, opens: to24h(opens), closes: to24h(closes) }];
}

/** schema.org data for search engines: the roaster and each café with its address and hours. */
export function structuredData() {
  const org = { "@type": "Organization", "@id": "#org", name: data.business.name, email: data.business.email, telephone: data.business.phone };
  const cafes = data.cafes.map((cafe) => {
    const [street, locality] = cafe.address.split(", ");
    return {
      "@type": "CafeOrCoffeeShop",
      name: `${data.business.name}, ${cafe.name}`,
      parentOrganization: { "@id": "#org" },
      telephone: data.business.phone,
      servesCuisine: "Coffee",
      address: { "@type": "PostalAddress", streetAddress: street, addressLocality: locality, addressRegion: "NS", addressCountry: "CA" },
      openingHoursSpecification: [
        ...openingHours(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], cafe.weekdays),
        ...openingHours(["Saturday"], cafe.saturday),
        ...openingHours(["Sunday"], cafe.sunday),
      ],
    };
  });
  return { "@context": "https://schema.org", "@graph": [org, ...cafes] };
}
