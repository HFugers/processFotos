"""Genereer een offline bladerbaar fotoalbum vanuit jaartalmappen."""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from foto_sort import PHOTO_EXTENSIONS

YEAR_DIRECTORY = re.compile(r"^\d{4}$")
ASSET_DIRECTORY = Path(__file__).parent / "web"
CSS_NAME = "foto-album.css"
JS_NAME = "foto-album.js"


@dataclass(frozen=True)
class AlbumResult:
    years: tuple[int, ...]
    photo_count: int
    index_path: Path
    css_path: Path
    js_path: Path


def _relative_url(*parts: str) -> str:
    """Encode each relative URL path component without creating absolute links."""
    return "/".join(quote(part, safe="") for part in parts)


def _atomic_write(path: Path, content: str) -> None:
    """Write generated text safely without leaving partial output files."""
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(content)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _read_year_photos(root: Path) -> dict[int, list[Path]]:
    albums: dict[int, list[Path]] = {}
    for folder in root.iterdir():
        if folder.is_symlink() or not folder.is_dir() or not YEAR_DIRECTORY.fullmatch(folder.name):
            continue
        photos = sorted(
            (
                path
                for path in folder.iterdir()
                if path.is_file()
                and not path.is_symlink()
                and path.suffix.lower() in PHOTO_EXTENSIONS
            ),
            key=lambda path: path.name.casefold(),
        )
        if photos:
            albums[int(folder.name)] = photos
    return albums


def _render_index(albums: dict[int, list[Path]], thumbnail_width: int) -> str:
    years = sorted(albums, reverse=True)
    tabs: list[str] = []
    sections: list[str] = []
    photo_index = 0

    for year_position, year in enumerate(years):
        selected = year_position == 0
        tabs.append(
            f'<button class="year-tab" type="button" role="tab" '
            f'id="tab-{year}" aria-controls="year-{year}" '
            f'aria-selected="{str(selected).lower()}" tabindex="{0 if selected else -1}" '
            f'data-year="{year}">{year}</button>'
        )
        cards: list[str] = []
        for photo in albums[year]:
            relative_path = _relative_url(str(year), photo.name)
            safe_path = html.escape(relative_path, quote=True)
            safe_name = html.escape(photo.name, quote=True)
            cards.append(
                f'<a class="photo-card" href="{safe_path}" '
                f'data-photo-index="{photo_index}" data-year="{year}" '
                f'aria-label="Bekijk {safe_name}">'
                f'<img src="{safe_path}" alt="{safe_name}" loading="lazy" '
                f'width="{thumbnail_width}" data-photo-index="{photo_index}">'
                f'<span>{html.escape(photo.name)}</span></a>'
            )
            photo_index += 1
        section_hidden = "" if selected else " hidden"
        sections.append(
            f'<section class="year-panel" id="year-{year}" role="tabpanel" '
            f'aria-labelledby="tab-{year}" data-year="{year}"{section_hidden}>'
            f'<div class="photo-grid">{"".join(cards)}</div></section>'
        )

    if not years:
        empty_message = (
            '<p class="empty-state">Geen foto’s gevonden in jaartalmappen. '
            'Sorteer eerst foto’s met FOTO_sort_app.</p>'
        )
    else:
        empty_message = ""

    return f'''<!doctype html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Een offline fotoalbum op jaartal.">
  <title>Historische foto’s</title>
  <link rel="stylesheet" href="{CSS_NAME}">
  <script src="{JS_NAME}" defer></script>
</head>
<body>
  <header class="site-header">
    <p class="eyebrow">Persoonlijk fotoarchief</p>
    <h1>Historische foto’s</h1>
    <p class="intro">Blader door de foto’s, gesorteerd op jaartal.</p>
  </header>
  <main>
    <nav class="year-tabs" role="tablist" aria-label="Kies een jaartal">{"".join(tabs)}</nav>
    {empty_message}
    {"".join(sections)}
  </main>
  <dialog class="viewer" aria-label="Foto bekijken">
    <div class="viewer-toolbar">
      <button class="viewer-home" type="button" aria-label="Terug naar het album">⌂ <span>Album</span></button>
      <p class="viewer-caption" aria-live="polite"></p>
      <button class="viewer-close" type="button" aria-label="Sluiten">×</button>
    </div>
    <button class="viewer-nav viewer-previous" type="button" aria-label="Vorige foto">‹</button>
    <figure class="viewer-figure"><img class="viewer-image" alt=""></figure>
    <button class="viewer-nav viewer-next" type="button" aria-label="Volgende foto">›</button>
    <p class="viewer-hint">Gebruik ← en → om te bladeren · Esc om te sluiten</p>
  </dialog>
  <footer>Gegenereerd door FOTO_wrapper_app</footer>
</body>
</html>
'''


def generate_album(raw_path: Path, thumbnail_width: int = 250) -> AlbumResult:
    """Genereer index.html en lokale CSS/JS voor de jaarmappen in ``raw_path``."""
    if thumbnail_width < 50 or thumbnail_width > 1000:
        raise ValueError("De miniatuurbreedte moet tussen 50 en 1000 pixels liggen.")
    root = raw_path.expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"Geen bestaande map: {root}")

    albums = _read_year_photos(root)
    index_path = root / "index.html"
    css_path = root / CSS_NAME
    js_path = root / JS_NAME
    _atomic_write(index_path, _render_index(albums, thumbnail_width))
    stylesheet = (ASSET_DIRECTORY / CSS_NAME).read_text(encoding="utf-8")
    stylesheet = stylesheet.replace("250px", f"{thumbnail_width}px", 1)
    css_path.write_text(stylesheet, encoding="utf-8", newline="\n")
    shutil.copyfile(ASSET_DIRECTORY / JS_NAME, js_path)
    return AlbumResult(
        years=tuple(sorted(albums, reverse=True)),
        photo_count=sum(len(photos) for photos in albums.values()),
        index_path=index_path,
        css_path=css_path,
        js_path=js_path,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Maak een offline HTML-fotoalbum van jaartalmappen.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "raw_path",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="bovenliggende map met jaartalmappen",
    )
    parser.add_argument(
        "--thumbnail-width",
        type=int,
        default=250,
        metavar="PIXELS",
        help="breedte van de miniaturen (50-1000 pixels)",
    )
    args = parser.parse_args(argv)
    if not (argv if argv is not None else sys.argv[1:]):
        parser.print_help()
        return 0

    try:
        result = generate_album(args.raw_path, args.thumbnail_width)
    except (NotADirectoryError, PermissionError, ValueError, OSError) as error:
        parser.error(str(error))

    print(
        f"Album gemaakt: {result.photo_count} foto('s) in {len(result.years)} jaartal(len). "
        f"Open {result.index_path}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())