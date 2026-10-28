"""Organiseer foto's uit één map in mappen per jaar."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

PHOTO_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tif",
    ".tiff",
    ".webp",
    ".heic",
    ".heif",
    ".avif",
    ".dng",
    ".cr2",
    ".cr3",
    ".nef",
    ".arw",
    ".orf",
    ".rw2",
}
DATE_IN_NAME = re.compile(r"(?<!\d)(\d{8})(?!\d)")
EXIF_DATE_FORMAT = "%Y:%m:%d %H:%M:%S"


@dataclass(frozen=True)
class SortResult:
    moved: int
    skipped: int
    errors: tuple[str, ...]


def _year_from_filename(path: Path) -> int | None:
    """Haal de eerste geldige yyyymmdd-datum uit de bestandsnaam."""
    for candidate in DATE_IN_NAME.findall(path.stem):
        try:
            return date(int(candidate[:4]), int(candidate[4:6]), int(candidate[6:])).year
        except ValueError:
            continue
    return None


def _year_from_exif(path: Path) -> int | None:
    """Lees de opnamedatum uit EXIF als Pillow en de metadata beschikbaar zijn."""
    try:
        from PIL import Image

        with Image.open(path) as image:
            exif = image.getexif()
            for tag in (36867, 36868, 306):  # Original, Digitized, DateTime
                value = exif.get(tag)
                if isinstance(value, str):
                    try:
                        return datetime.strptime(value, EXIF_DATE_FORMAT).year
                    except ValueError:
                        continue
    except (OSError, ValueError, TypeError):
        # Niet-ondersteunde of beschadigde afbeeldingen kunnen nog een
        # bruikbare bestandstijd hebben.
        pass
    return None


def _year_from_file_date(path: Path) -> int | None:
    """Gebruik aanmaakdatum indien beschikbaar, anders wijzigingsdatum."""
    try:
        stat = path.stat()
        timestamp = getattr(stat, "st_birthtime", None)
        if timestamp is None and os.name == "nt":
            timestamp = stat.st_ctime
        if timestamp is None:
            # POSIX ctime is geen aanmaakdatum. Gebruik daarom mtime als
            # expliciete, portable benadering wanneer birthtime ontbreekt.
            timestamp = stat.st_mtime
        return datetime.fromtimestamp(timestamp).year
    except (OSError, OverflowError, ValueError):
        return None


def get_photo_year(path: Path) -> int | None:
    """Bepaal het jaar: bestandsnaam, EXIF-opnamedatum, bestandstijd."""
    return (
        _year_from_filename(path)
        or _year_from_exif(path)
        or _year_from_file_date(path)
    )


def sort_photos(raw_path: Path, dry_run: bool = False) -> SortResult:
    """Verplaats foto's direct in ``raw_path`` naar een map per jaar.

    Bestaande bestanden worden nooit overschreven. Mappen worden niet
    recursief doorzocht, zodat eerder gesorteerde foto's ongemoeid blijven.
    """
    root = raw_path.expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"Geen bestaande map: {root}")

    moved = 0
    skipped = 0
    errors: list[str] = []

    for source in sorted(root.iterdir(), key=lambda item: item.name.casefold()):
        if source.is_symlink() or not source.is_file():
            continue
        if source.suffix.lower() not in PHOTO_EXTENSIONS:
            continue

        year = get_photo_year(source)
        if year is None:
            skipped += 1
            errors.append(f"Geen bruikbare datum gevonden: {source.name}")
            continue

        destination_dir = root / str(year)
        destination = destination_dir / source.name
        if destination.exists():
            skipped += 1
            errors.append(f"Bestand bestaat al, overgeslagen: {destination.relative_to(root)}")
            continue

        if dry_run:
            print(f"[proef] {source.name} -> {year}/{source.name}")
            moved += 1
            continue

        try:
            destination_dir.mkdir(exist_ok=True)
            # Controleer opnieuw na het aanmaken van de map om overschrijven
            # van een bestand dat intussen is verschenen te voorkomen.
            if destination.exists():
                skipped += 1
                errors.append(f"Bestand bestaat al, overgeslagen: {destination.relative_to(root)}")
                continue
            shutil.move(str(source), str(destination))
            moved += 1
            print(f"{source.name} -> {year}/{source.name}")
        except OSError as error:
            skipped += 1
            errors.append(f"Kon {source.name} niet verplaatsen: {error}")

    return SortResult(moved=moved, skipped=skipped, errors=tuple(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verplaats foto's naar jaartalmappen op basis van datum in naam of metadata.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "raw_path",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="map met ongesorteerde foto's (standaard: huidige map)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="toon welke foto's verplaatst zouden worden, zonder bestanden te wijzigen",
    )
    args = parser.parse_args(argv)
    if not (argv if argv is not None else sys.argv[1:]):
        parser.print_help()
        return 0

    try:
        result = sort_photos(args.raw_path, dry_run=args.dry_run)
    except (NotADirectoryError, PermissionError) as error:
        parser.error(str(error))

    for error in result.errors:
        print(f"Waarschuwing: {error}")
    action = "zouden worden verplaatst" if args.dry_run else "verplaatst"
    print(f"Klaar: {result.moved} foto('s) {action}; {result.skipped} overgeslagen.")
    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())