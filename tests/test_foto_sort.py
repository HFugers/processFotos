import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import foto_sort


class PhotoYearTests(unittest.TestCase):
    def test_valid_date_in_filename_takes_priority(self):
        path = Path("vakantie_19991231.jpg")
        with patch("foto_sort._year_from_exif", return_value=2020):
            self.assertEqual(foto_sort.get_photo_year(path), 1999)

    def test_invalid_filename_date_is_ignored(self):
        path = Path("scan_20230230.jpg")
        with patch("foto_sort._year_from_exif", return_value=2021):
            self.assertEqual(foto_sort.get_photo_year(path), 2021)

    def test_date_must_be_eight_digit_token(self):
        self.assertIsNone(foto_sort._year_from_filename(Path("IMG1202401010.jpg")))


class SortPhotosTests(unittest.TestCase):
    def test_no_arguments_prints_help_with_defaults(self):
        output = StringIO()
        with redirect_stdout(output):
            exit_code = foto_sort.main([])

        self.assertEqual(exit_code, 0)
        self.assertIn("--dry-run", output.getvalue())
        self.assertIn("standaard: huidige map", output.getvalue())
        self.assertIn("default:", output.getvalue())

    def test_moves_photo_to_year_folder(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            photo = root / "foto_19840615.jpg"
            photo.write_bytes(b"not decoded because filename has date")

            result = foto_sort.sort_photos(root)

            self.assertEqual(result.moved, 1)
            self.assertTrue((root / "1984" / photo.name).exists())
            self.assertFalse(photo.exists())

    def test_dry_run_does_not_move_photo(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            photo = root / "foto_19840615.jpg"
            photo.write_bytes(b"photo")

            result = foto_sort.sort_photos(root, dry_run=True)

            self.assertEqual(result.moved, 1)
            self.assertTrue(photo.exists())
            self.assertFalse((root / "1984").exists())

    def test_existing_destination_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            photo = root / "foto_19840615.jpg"
            destination = root / "1984" / photo.name
            photo.write_bytes(b"original")
            destination.parent.mkdir()
            destination.write_bytes(b"existing")

            result = foto_sort.sort_photos(root)

            self.assertEqual(result.moved, 0)
            self.assertEqual(result.skipped, 1)
            self.assertEqual(photo.read_bytes(), b"original")
            self.assertEqual(destination.read_bytes(), b"existing")

    def test_missing_date_is_reported_without_moving(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            photo = root / "zonder_datum.jpg"
            photo.write_bytes(b"photo")
            with (
                patch("foto_sort._year_from_exif", return_value=None),
                patch("foto_sort._year_from_file_date", return_value=None),
            ):
                result = foto_sort.sort_photos(root)

            self.assertEqual(result.skipped, 1)
            self.assertIn("Geen bruikbare datum", result.errors[0])
            self.assertTrue(photo.exists())

    def test_non_photo_and_nested_files_are_ignored(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "document.txt").write_text("text")
            nested = root / "1980"
            nested.mkdir()
            (nested / "foto_19840615.jpg").write_bytes(b"photo")

            result = foto_sort.sort_photos(root)

            self.assertEqual(result.moved, 0)
            self.assertTrue((nested / "foto_19840615.jpg").exists())


if __name__ == "__main__":
    unittest.main()