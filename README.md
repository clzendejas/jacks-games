# Jack's Games

Small, calm games for young children. No ads, no purchases, no tracking,
no accounts, no links out. Each game is a single self-contained web page
that also installs as its own app and works offline.

## Games

| Game | Play | What it is |
|---|---|---|
| Rainbow Bottles | [Play](https://clzendejas.github.io/jacks-games/rainbow-bottles/) | Pour colors between bottles until every bottle holds one color. |
| Jack's Reading Adventures | [Play](https://clzendejas.github.io/jacks-games/reading-adventures/) | Learn to read in small steps. First adventure: Sound Pals, where letter pals say their sounds. Word Slide (blending) and Word Builder (spelling) are coming. |
| Jack's World | [Play](https://clzendejas.github.io/jacks-games/jacks-world/) | A blocky 3D town builder. Paint the land by number, then build one thing a day: something needed, something fun, or something beautiful. |
| Logan's Coloring Book | [Play](https://clzendejas.github.io/jacks-games/logans-coloring-book/) | Twenty pictures in five books (zoo animals, princesses, unicorns, under the sea, yummy treats). Paint by numbers, or color freely. Paint stays inside the lines. |

## Install on a tablet or phone

**iPad / iPhone:** open a game's Play link in Safari, tap Share, then
"Add to Home Screen". Open it once while online so it is saved for
offline play.

**Android / Fire tablet:** open the Play link in the browser and choose
"Add to Home screen" or "Install app" from the menu.

Each game installs separately, with its own icon.

## How the games are built

One folder per game. Each folder holds an `index.html` with all the code
and styles inline, a web app manifest, icons, and a small service worker
for offline play. There is no build step and there are no dependencies.

Logan's Coloring Book keeps its pictures as separate files, one folder per
book under `logans-coloring-book/packs/`. They are drawn by
`tools/build_coloring_pages.py`; to add a picture or a book, add it there
and run the script.

## Sounds and fonts

The letter sounds in Jack's Reading Adventures are a parent's own recordings,
shared under the same MIT license as the code. The letters are set in Andika
(SIL Open Font License), a typeface made for early readers. Jack's World
uses three.js (MIT) for its 3D scene.

## License

MIT. Use these, change them, and share them with your own kids.
