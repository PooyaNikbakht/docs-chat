# Northwind Coffee Co. fact sheet

Northwind Coffee Co. is a fictional business made up for this demo. Every name, address,
phone number and price below is invented.

This file is the single source of truth for the demo. `generate_kb.py` reads it and writes
both the customer help center PDF (what the bot answers from) and
`frontend/src/data/northwind.json` (what the sample website shows), so the two never drift.

Format rules, so the parser stays simple: `key: value` bullets under a heading become a
dictionary, and a Markdown table becomes a list of rows. Text outside those is ignored.

## Business

- name: Northwind Coffee Co.
- short_name: Northwind
- tagline: Small-batch coffee, roasted by the harbour.
- city: Halifax, Nova Scotia
- founded: 2014
- founders: Maya Okafor and Liam Doucette
- roaster: a 15 kg cast-iron drum roaster we call Old Tom
- email: hello@northwind.example
- wholesale_email: wholesale@northwind.example
- phone: (902) 555-0142
- support_hours: Monday to Friday, 9 am to 5 pm Atlantic time
- reply_time: within one business day
- currency: CAD
- bag_size: 340 g
- website: northwind.example

## Shipping

- order_cutoff: 12 pm Atlantic time
- roast_days: Monday to Thursday
- free_canada_over: 45
- free_us_over: 75
- countries: Canada and the United States
- no_ship_note: We don't ship outside Canada and the United States yet, so we can't send orders to the UK, Europe, Australia or Mexico.
- tracking: A tracking link is emailed as soon as your order ships.
- address_change_window: 2 hours

| zone | method | price | time |
|------|--------|-------|------|
| Canada | Standard | 8 | 2 to 5 business days |
| Canada | Express | 16 | 1 to 2 business days |
| United States | Standard | 14 | 4 to 8 business days |
| Local pickup | Harbour Street café | 0 | Ready the next business day |

## Returns

- window_days: 30
- guarantee: If a coffee isn't for you, tell us within 30 days of delivery and we'll send a different coffee or refund it, even if the bag is open. This works once per order.
- gear: Brewing gear can be returned unused, in its original box, within 30 days of delivery.
- damaged: If something arrives damaged or wrong, email a photo within 7 days and we'll replace it at no cost.
- refund_time: Refunds go back to the original payment method within 5 to 7 business days of approval.
- return_shipping: We email a prepaid return label for gear returns in Canada. US customers pay return shipping.
- final_sale: Gift cards and opened brewing gear are final sale.

## Subscriptions

- discount_percent: 10
- frequencies: every 1, 2, 3 or 4 weeks
- free_shipping: Subscriptions ship free anywhere in Canada. US subscriptions ship free over $75.
- change_deadline: 2 days before your next ship date
- pause_max: 3 months
- skip: Skip any single delivery from your account, up to the change deadline.
- cancel: Cancel any time from your account. There are no fees and no minimum number of deliveries.
- roasters_choice: Roaster's Choice sends a different single origin each delivery, picked by our roasting team.
- manage: Manage everything at northwind.example/account, or reply to any shipping email and we'll do it for you.

## Coffees

| id | name | origin | region | process | roast | notes | price | use | color |
|----|------|--------|--------|---------|-------|-------|-------|-----|-------|
| harbour-blend | Harbour Blend | Brazil and Colombia | Cerrado and Huila | Natural and washed | Medium | milk chocolate, toasted almond, brown sugar | 19 | drip, French press, cold brew | #8A5A3C |
| first-light | First Light | Ethiopia | Yirgacheffe | Washed | Light | bergamot, peach, jasmine | 22 | pour-over, filter | #C98B4E |
| night-shift | Night Shift Espresso | Brazil and Guatemala | Mogiana and Huehuetenango | Natural and washed | Medium-dark | cocoa, molasses, dark cherry | 20 | espresso, moka pot, milk drinks | #3B2A20 |
| huila-valley | Huila Valley | Colombia | Huila | Washed | Medium | red apple, caramel, orange zest | 21 | pour-over, drip, AeroPress | #5E7A5A |
| kirinyaga | Kirinyaga Peaberry | Kenya | Kirinyaga | Washed | Light | blackcurrant, grapefruit, cane sugar | 24 | pour-over, filter | #9C4A3A |
| still-water | Still Water Decaf | Colombia | Tolima | Sugarcane decaf | Medium | chocolate, plum, honey | 20 | any brew method | #6B7F8E |

## Coffee notes

- decaf_process: Still Water Decaf is decaffeinated in Colombia with the sugarcane process, which uses ethyl acetate made from fermented sugarcane and water. It removes about 97 percent of the caffeine.
- roast_levels: We roast light, medium and medium-dark. Light roasts taste brighter and more fruity, medium roasts are balanced and sweet, and medium-dark roasts are rich and low in acidity.
- freshness: Every bag is roasted to order and shows its roast date. Coffee tastes best from 5 to 30 days after roasting.
- grind: Every coffee is available as whole bean, or ground for espresso, pour-over, drip or French press.
- allergens: Our roastery handles only coffee beans. We don't roast flavoured coffees, and no nuts, dairy, gluten or soy are used in the roastery. Pastries in our cafés may contain nuts, milk, eggs or wheat.
- sourcing: We buy green coffee from importers who pay producers above the Fairtrade minimum, and we publish the price we pay for each coffee.

## Brewing

| method | ratio | dose | yield | grind | temperature | time |
|--------|-------|------|-------|-------|-------------|------|
| Pour-over | 1:16 | 22 g | 350 g of water | medium-fine | 93 to 96 °C | 3 to 3.5 minutes |
| French press | 1:15 | 30 g | 450 g of water | coarse | 94 °C | 4 minutes |
| Espresso | 1:2 | 18 g | 36 g of espresso | fine | 92 to 94 °C | 27 to 32 seconds |

## Gift cards

- amounts: 25, 50 and 100
- delivery: Digital gift cards are emailed right away, or on a date you choose.
- expiry: Gift cards never expire.
- use: Gift cards work on one-time orders, subscriptions and in our cafés.
- refunds: Gift cards can't be exchanged for cash.

## Wholesale

- who: coffee shops, restaurants and offices
- minimum: 5 kg per order
- delivery: Free delivery in the Halifax area every Tuesday and Friday. Elsewhere we ship by courier.
- training: New coffee shop partners get two free barista training sessions and help dialling in their grinder.
- contact: Email wholesale@northwind.example with your business name and expected weekly volume. We reply within 2 business days.

## Cafés

| name | address | weekdays | saturday | sunday | note |
|------|---------|----------|----------|--------|------|
| Harbour Street | 112 Harbour Street, Halifax | 7 am to 6 pm | 8 am to 5 pm | 8 am to 5 pm | Our first café, and the pickup point for online orders. |
| Roastery | 40 Foundry Lane, Dartmouth | 8 am to 4 pm | 9 am to 3 pm | closed | Free roastery tours run on Saturdays at 10 am. |
| Willow Row | 18 Willow Row, Halifax | 7:30 am to 5 pm | 8 am to 4 pm | 8 am to 4 pm | A quiet back room for reading and studying. |

## Cafés notes

- holidays: All cafés close on December 25 and January 1. Holiday hours are posted on our website a week ahead.
- wifi: Free Wi-Fi in every café.
- pets: Dogs are welcome on the Harbour Street patio.
