import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import foto_wrapper


class GenerateAlbumTests(unittest.TestCase):
    def test_generates_year_tabs_and_relative_photo_links(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "1999").mkdir()
            (root / "2024").mkdir()
            (root / "1999" / "oude foto.jpg").write_bytes(b"old")
            (root / "2024" / 'foto <familie>.png').write_bytes(b"new")
            (root / "not-a-year").mkdir()
            (root / "not-a-year" / "ignored.jpg").write_bytes(b"ignored")

            result = foto_wrapper.generate_album(root)
            page = result.index_path.read_text(encoding="utf-8")

            self.assertEqual(result.years, (2024, 1999))
            self.assertEqual(result.photo_count, 2)
            self.assertLess(page.index('data-year="2024"'), page.index('data-year="1999"'))
            self.assertIn('href="2024/foto%20%3Cfamilie%3E.png"', page)
            self.assertIn('src="1999/oude%20foto.jpg"', page)
            self.assertNotIn("file://", page)
            self.assertIn('href="foto-album.css"', page)
            self.assertIn('src="foto-album.js"', page)
            self.assertTrue(result.css_path.is_file())
            self.assertTrue(result.js_path.is_file())

    def test_thumbnail_width_is_written_to_generated_stylesheet(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "2024").mkdir()
            (root / "2024" / "foto.jpg").write_bytes(b"photo")

            result = foto_wrapper.generate_album(root, thumbnail_width=320)

            css = result.css_path.read_text(encoding="utf-8")
            page = result.index_path.read_text(encoding="utf-8")
            self.assertIn("--thumbnail-width: 320px", css)
            self.assertIn('width="320"', page)
            self.assertNotIn("<style", page)

    def test_empty_root_generates_helpful_empty_album(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = foto_wrapper.generate_album(Path(temporary_directory))
            page = result.index_path.read_text(encoding="utf-8")

            self.assertEqual(result.years, ())
            self.assertEqual(result.photo_count, 0)
            self.assertIn("Geen foto’s gevonden", page)

    def test_thumbnail_width_out_of_range_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaises(ValueError):
                foto_wrapper.generate_album(Path(temporary_directory), thumbnail_width=20)

    def test_no_arguments_prints_help(self):
        output = StringIO()
        with redirect_stdout(output):
            exit_code = foto_wrapper.main([])

        self.assertEqual(exit_code, 0)
        self.assertIn("--thumbnail-width", output.getvalue())
        self.assertRegex(output.getvalue(), r"default:\s+250")


if __name__ == "__main__":
    unittest.main()