# Zobrazovač v0.9.17

Desktopová aplikace pro vlastní knihovnu obrázků, GIFů a videí s popisky, poznámkami, hodnocením a **tagy**.

## Tagy místo kategorií

- Levý panel si zachovává původní podobu, ale každé médium může mít více tagů současně.
- Kliknutí na tag filtruje právě tento tag.
- **Ctrl + kliknutí** na další tagy filtruje jejich průnik (médium musí mít všechny vybrané tagy).
- „Vše“ zobrazuje celou knihovnu a „Nezařazené“ jen média bez tagu.
- Podtagy a ruční pořadí tagů zůstávají zachovány.
- **Hromadné vytváření tagů:** klikni na **+**, napiš více názvů (každý na samostatný řádek) a potvrď. Funguje také pro **Nový podtag**.
- Existující názvy se přeskočí a program upozorní na duplicity. Ostatní zadané tagy se vytvoří najednou.
- Při přiřazování tagů lze zaškrtnout více položek bez zavření nabídky. Tagy v nabídce jsou seřazené podle počtu médií.
- Po výběru média lze tagy přiřazovat a odebírat vpravo tlačítkem **Tagy** a uložit přes **Uložit změny**.
- Pravým kliknutím na náhled je možné přidávat nebo odebírat tagy také více vybraným médiím najednou.
- Pravé tlačítko nad náhledem nabízí **Zobrazit umístění souboru**.

## Přechod ze starší verze

Při prvním spuštění verze 0.9.15 se dosavadní zařazení do kategorií **automaticky převede na tagy** a zachová se přiřazení ke stávajícím médiím. Ještě před převodem se vytvoří záložní kopie původní databáze jako `data/media_notes.before_tags.db`, pokud databáze obsahuje záznamy. Tato záloha se při dalších spuštěních nepřepisuje.

Původní obrázky, GIFy a videa aplikace nekopíruje ani nemaže.

## Další funkce

- Přidávání přes dialog a drag & drop.
- Náhledy JPG, PNG, WebP, BMP a GIFů a běžných videoformátů.
- Krátký popisek, poznámky, hodnocení 1–3 hvězdičkami.
- Vyhledávání v názvech, popiscích, poznámkách a tagech.
- SQLite databáze uložená v `data/media_notes.db`.

## Spuštění

Nová instalace:

```bash
git clone https://github.com/Fousliez/Zobrazovac.git
cd Zobrazovac
chmod +x start_app.sh
./start_app.sh
```

U existující instalace stačí spustit `start_app.sh`; skript stáhne aktuální hlavní větev `main` z GitHubu.

## Klávesové zkratky

- `Ctrl+O`: Přidat média
- `Ctrl+S`: Uložit změny
- `Ctrl+F`: Vyhledávání
- `Delete`: Smazat vybraná média z databáze (původní soubory zůstanou)
