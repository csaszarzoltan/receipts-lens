# Photo credits

Every image under `frontend/public/photos/` is used under the licence listed below. The
files are downscaled to 1280 px wide (Wikimedia Commons thumbnails) and otherwise
unedited. Photos are self-hosted, so the app makes no third-party image requests.

| File | Use | Author | Licence | Source |
| --- | --- | --- | --- | --- |
| `hero.jpg` | Dashboard header, landing hero | Shixart1985 | [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/) | [Fresh apples and herbs in a woven basket on a wooden table](https://commons.wikimedia.org/wiki/File:Fresh_apples_and_herbs_in_a_woven_basket_on_a_wooden_table.jpg) |
| `produce.jpg` | Groceries category | Webvilla on Unsplash | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | [Onion and a group of vegetables on a cutting board](https://commons.wikimedia.org/wiki/File:Onion_and_a_group_of_vegetables_on_a_cutting_board.jpg) |
| `bakery.jpg` | Landing call-to-action band | daisybush | [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/) | [No-Knead Bread - Finished Loaf](https://commons.wikimedia.org/wiki/File:No-Knead_Bread_-_Finished_Loaf_(294068096).jpg) |
| `coffee.jpg` | Meals & entertainment category | Edward | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | [Cup of coffee in Café Butter, Prenzlauer Berg, Berlin](https://commons.wikimedia.org/wiki/File:Cup_of_coffee_in_Café_Butter_-_Prenzlauer_Berg,_Berlin.jpg) |
| `meals.jpg` | Meals category, empty states | Michael J. Bennett | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) | [Roasted Chicken Dinner Plate, Broccoli, Demi Glace](https://commons.wikimedia.org/wiki/File:Roasted_Chicken_Dinner_Plate,_Broccoli,_Demi_Glace.jpg) |
| `market.jpg` | Shopping category | Ei'eke | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | [A market man selling grocery bags](https://commons.wikimedia.org/wiki/File:A_market_man_selling_grocery_bags.jpg) |
| `herbs.jpg` | Healthcare category, feature cards | Thomas Rehehäuser (trehehaeuser) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | [Fresh Herbs (Unsplash)](https://commons.wikimedia.org/wiki/File:Fresh_Herbs_(Unsplash).jpg) |
| `home.jpg` | Housing and utilities categories | Chatsom | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) | [Restored Kitchen Chateau Sommesnil](https://commons.wikimedia.org/wiki/File:Restored_Kitchen_Chateau_Sommesnil.jpg) |
| `table.jpg` | Office, uncategorised, default empty state | Shixart1985 | [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/) | [Freshly chopped vegetables on a wooden cutting board](https://commons.wikimedia.org/wiki/File:Freshly_chopped_vegetables_on_a_wooden_cutting_board.jpg) |
| `street.jpg` | Transport category | Wilfredor | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | [Snowy street in Quebec City with a bicycle lane](https://commons.wikimedia.org/wiki/File:Snowy_street_in_Quebec_City_with_a_bicycle_lane.jpg) |

## Adding a photo

1. Pick a file that is CC0, CC BY or CC BY-SA. Avoid NC and ND licences.
2. Add the file to `frontend/public/photos/` and a key to `PHOTOS` in `frontend/lib/photos.ts`.
3. Add a row to the table above with the author, licence and source page.
