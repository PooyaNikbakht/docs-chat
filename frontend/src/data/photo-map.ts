// Which photo goes where, with alt text. Facts stay in northwind.json; this file is only imagery.
import type { PhotoName } from "@/components/northwind/Photo";

type Shot = { name: PhotoName; alt: string };

export const COFFEE_PHOTOS: Record<string, Shot> = {
  "harbour-blend": { name: "coffee-burlap", alt: "Medium-roasted coffee beans spilling from an open burlap sack" },
  "first-light": { name: "coffee-open-bag", alt: "An open white bag of light-brown roasted coffee beans" },
  "night-shift": { name: "coffee-dark-cup", alt: "A white cup heaped with dark, glossy espresso beans" },
  "huila-valley": { name: "coffee-bag-hands", alt: "Two hands holding open a coffee bag full of roasted beans" },
  kirinyaga: { name: "coffee-bag-top", alt: "Looking down into a foil-lined bag of roasted coffee beans" },
  "still-water": { name: "coffee-spill", alt: "Roasted coffee beans tipped out of a white mug onto a pale table" },
};

export const CAFE_PHOTOS: Record<string, Shot> = {
  "Harbour Street": { name: "cafe-harbour", alt: "A bright café counter with pendant lights and big street-facing windows" },
  Roastery: { name: "cafe-roastery", alt: "A brick-walled café with tall factory windows, wooden tables and hanging plants" },
  "Willow Row": { name: "cafe-willow", alt: "Wooden shelves full of books and magazines in a quiet café corner" },
};

export const BREW_PHOTOS: Record<string, Shot> = {
  "Pour-over": { name: "brew-pourover", alt: "Hot water poured from a gooseneck kettle into a white pour-over dripper" },
  "French press": { name: "brew-press", alt: "A French press of brewed coffee on a pale wooden counter" },
  Espresso: { name: "brew-espresso", alt: "A thin stream of espresso running from a portafilter" },
};
