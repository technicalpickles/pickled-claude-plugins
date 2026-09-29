"""Unit tests for yt-digest's pure helpers. Heavy deps are stubbed; the
pipeline itself is not exercised here (it needs network, ffmpeg, and Claude)."""
import importlib.machinery
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parent.parent / "yt-digest"


def load_module():
    for name in ("yt_dlp", "claude_agent_sdk", "imageio_ffmpeg", "wordfreq"):
        sys.modules.setdefault(name, mock.MagicMock())
    rapid = types.ModuleType("rapidocr_onnxruntime")
    rapid.RapidOCR = mock.MagicMock()
    sys.modules.setdefault("rapidocr_onnxruntime", rapid)
    loader = importlib.machinery.SourceFileLoader("yt_digest", str(SCRIPT))
    spec = importlib.util.spec_from_loader("yt_digest", loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules["yt_digest"] = module  # @dataclass looks the module up by name
    loader.exec_module(module)
    return module


yt = load_module()


class SelectMetadata(unittest.TestCase):
    def test_maps_and_formats_fields(self):
        info = {
            "title": "A Talk",
            "channel": "Some Channel",
            "upload_date": "20260102",
            "webpage_url": "https://www.youtube.com/watch?v=abc",
            "duration": 3725,
            "formats": ["ignored"],
        }
        self.assertEqual(
            yt.select_metadata(info),
            {
                "title": "A Talk",
                "channel": "Some Channel",
                "published": "2026-01-02",
                "url": "https://www.youtube.com/watch?v=abc",
                "duration_seconds": 3725,
            },
        )

    def test_missing_fields_become_none(self):
        self.assertEqual(
            yt.select_metadata({}),
            {"title": None, "channel": None, "published": None, "url": None, "duration_seconds": None},
        )

    def test_falls_back_to_uploader_when_no_channel(self):
        self.assertEqual(yt.select_metadata({"uploader": "Someone"})["channel"], "Someone")


class WriteMetadata(unittest.TestCase):
    def test_writes_metadata_json(self):
        info = {"title": "T", "channel": "C", "upload_date": "20260102", "webpage_url": "u", "duration": 1}
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            fake_ydl = mock.MagicMock()
            fake_ydl.__enter__.return_value.extract_info.return_value = info
            with mock.patch.object(yt.yt_dlp, "YoutubeDL", return_value=fake_ydl):
                yt.write_metadata("https://youtu.be/abc", out)
            self.assertEqual(json.loads((out / "metadata.json").read_text())["published"], "2026-01-02")

    def test_failure_warns_and_does_not_raise(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(yt.yt_dlp, "YoutubeDL", side_effect=RuntimeError("blocked")):
                yt.write_metadata("https://youtu.be/abc", Path(tmp))
            self.assertFalse((Path(tmp) / "metadata.json").exists())


if __name__ == "__main__":
    unittest.main()
