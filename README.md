# Historische Foto's

Deze applicatie bestaat uit twee delen;

1) FOTO_sort_app
2) FOTO_wrapper_app

De gebruiker dan dus na de processing de map met foto's en html op een stick of disk installeren en met zijn browser de foto's bekijken.

## FOTO_sort_app

De eerste versie staat in `foto_sort.py`. Vereist Python 3.10 of hoger.
Installeer de EXIF-ondersteuning vanuit de hoofdmap van het project:

```sh
python -m pip install -r requirements.txt
```

Voer eerst een proef uit; hiermee worden geen bestanden verplaatst:

```sh
python foto_sort.py /pad/naar/fotos --dry-run
```

Zonder parameters toont het programma de helptekst met alle opties en
standaardwaarden. Gebruik `.` als je de huidige map daadwerkelijk wilt
sorteren; zonder mapargument is de huidige map de standaardlocatie.

Verplaats de foto's daarna door dezelfde opdracht zonder `--dry-run` uit te
voeren. Als geen map is opgegeven, gebruikt het programma de huidige map.
Alleen foto's die direct in die map staan worden verwerkt. Het jaartal wordt
bepaald uit een geldige `yyyymmdd`-datum in de bestandsnaam, daarna uit de
EXIF-opnamedatum en vervolgens uit de bestandstijd (aanmaaktijd waar het
besturingssysteem die aanbiedt, anders wijzigingstijd). Onleesbare foto's of
bestanden zonder bruikbare datum worden overgeslagen en gemeld. Bestaande
bestanden worden nooit overschreven.

Voer de tests uit met:

```sh
python -m unittest discover -s tests
```

## FOTO_wrapper_app

De tweede applicatie staat in `foto_wrapper.py`. Hij maakt in `raw_path` een
offline album op basis van de jaartalmappen die FOTO_sort_app heeft gemaakt.
Een map telt mee als jaartalmap wanneer de naam uit vier cijfers bestaat en
de map ten minste één ondersteunde foto bevat.

```sh
python foto_wrapper.py /pad/naar/fotos
```

De uitvoer bevat `index.html`, `foto-album.css` en `foto-album.js` in de
opgegeven bovenliggende map. De HTML gebruikt uitsluitend relatieve
verwijzingen, zodat de complete map naar een andere schijf of computer kan
worden gekopieerd. Jaar-tabs staan van nieuw naar oud. Klik op een miniatuur
voor schermvullend bekijken; blader met de vorige/volgende knoppen of de
pijltjestoetsen. De knop Album of Esc brengt je terug naar het overzicht.
Zonder JavaScript blijft de afbeelding als gewone link beschikbaar.

Opties en standaardwaarden:

- `raw_path`: map met jaartalmappen; standaard de huidige map.
- `--thumbnail-width PIXELS`: breedte van miniaturen; standaard 250 pixels
	(toegestaan: 50 t/m 1000).

Zonder argumenten toont het programma de helptekst. Voor een afwijkende
miniatuurgrootte:

```sh
python foto_wrapper.py /pad/naar/fotos --thumbnail-width 320
```

De tests voor beide applicaties voer je uit vanuit de projectmap:

```sh
python -m unittest discover -s tests
```
