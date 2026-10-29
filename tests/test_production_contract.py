"""Offline regressions: no Edge TTS or generation service is called."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_demo as bd
from production_contract import scene_layout, check_render_contract, audio_fingerprint


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((ROOT / "specs/4178-westminster-extremism.json").read_text())

    def test_all_existing_specs_keep_legacy_layouts(self):
        for path in (ROOT / "specs").glob("*.json"):
            spec = json.loads(path.read_text())
            check_render_contract(spec, draft=True)
            self.assertEqual([scene_layout(s) for s in spec["timeline"]],
                             ["hook", "receipt", "key_points", "facts_figures", "outro"])

    def test_arbitrary_count_and_order(self):
        self.spec["editorialGate"] = {"status": "approved", "editorApproved": True, "reviewedBy": "Editor"}
        self.spec["timeline"] = [{"sceneNumber": n, "layout": l} for n, l in
                                 [(1, "key_points"), (2, "hook"), (3, "receipt")]]
        check_render_contract(self.spec)
        self.assertEqual([scene_layout(s) for s in self.spec["timeline"]], ["key_points", "hook", "receipt"])

    def test_unknown_layout_and_duplicate_scene_fail_even_for_draft(self):
        with self.assertRaises(ValueError):
            scene_layout({"layout": "route_map"})
        self.spec["timeline"][1]["sceneNumber"] = 1
        with self.assertRaises(ValueError):
            check_render_contract(self.spec, draft=True)

    def test_pending_rejected_before_audio_or_writes(self):
        self.spec["editorialGate"]["editorApproved"] = False
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "pending.json"
            path.write_text(json.dumps(self.spec))
            with patch.object(bd, "generate_story_audio") as audio:
                with self.assertRaisesRegex(ValueError, "Editorial approval"):
                    bd.render_story_from_spec(path)
                audio.assert_not_called()

    def test_strict_gate_and_draft_exception(self):
        for value in ("true", 1, False, None):
            self.spec["editorialGate"]["editorApproved"] = value
            with self.assertRaises(ValueError):
                check_render_contract(self.spec)
            check_render_contract(self.spec, draft=True)
        self.spec["editorialGate"] = {"status": "approved", "editorApproved": True, "reviewedBy": " "}
        with self.assertRaises(ValueError):
            check_render_contract(self.spec)

    def test_explicit_layout_dispatch_and_scene_local_copy(self):
        scene = {"sceneNumber": 1, "layout": "key_points", "keyPoints": [["Local", "Body", "Source"]]}
        original = copy.deepcopy(self.spec)
        with patch.object(bd, "render_template_scene3_key_points", return_value="image") as renderer:
            self.assertEqual(bd.create_scene_overlay_image(self.spec, scene), "image")
            self.assertEqual(renderer.call_args.args[0]["keyPoints"], scene["keyPoints"])
        self.assertEqual(self.spec, original)

    def test_real_overlays_render_with_reordered_layouts(self):
        for scene in self.spec["timeline"]:
            modified = copy.deepcopy(scene)
            modified["layout"] = scene_layout(scene)
            modified["sceneNumber"] += 10
            image = bd.create_scene_overlay_image(self.spec, modified, t=1.0)
            self.assertEqual(image.size, (1080, 1920))

    def test_fingerprint_changes_only_for_audio_inputs(self):
        base = audio_fingerprint("Hello", "en-GB-SoniaNeural")
        self.assertEqual(base, audio_fingerprint("Hello", "en-GB-SoniaNeural"))
        self.assertNotEqual(base, audio_fingerprint("Changed", "en-GB-SoniaNeural"))
        self.assertNotEqual(base, audio_fingerprint("Hello", "en-GB-LibbyNeural"))
        self.assertNotEqual(base, audio_fingerprint("Hello", "en-GB-SoniaNeural", "+2%"))

    def test_disclosure_follows_asset_and_attribution_is_configurable(self):
        scene = copy.deepcopy(self.spec["timeline"][2])
        scene["layout"] = "key_points"
        scene["sourceLabel"] = "SOURCE: ARTICLE ONLY"
        scene["visualAsset"]["isIllustrative"] = False
        original_text = bd.ImageDraw.ImageDraw.text
        with patch.object(bd.rt, "apply_ai_disclaimer") as disclosure, \
             patch.object(bd.ImageDraw.ImageDraw, "text", autospec=True, side_effect=original_text) as text:
            bd.create_scene_overlay_image(self.spec, scene)
            self.assertFalse(disclosure.call_args.kwargs["show"])
            labels = [c.args[2] for c in text.call_args_list if len(c.args) > 2]
            self.assertIn("SOURCE: ARTICLE ONLY", labels)
            self.assertFalse(any("VERIFIED PUBLIC RECORD" in str(label) for label in labels))
        scene["visualAsset"]["isIllustrative"] = True
        with patch.object(bd.rt, "apply_ai_disclaimer") as disclosure:
            bd.create_scene_overlay_image(self.spec, scene)
            self.assertTrue(disclosure.call_args.kwargs["show"])

    def test_audio_cache_invalidates_changed_text(self):
        spec = {"timeline": [{"sceneNumber": 1, "voiceoverText": "First script"}]}
        with tempfile.TemporaryDirectory() as folder:
            audio = Path(folder) / "scene_1.mp3"
            def fake_command(cmd, **kwargs):
                if cmd[0] == "edge-tts":
                    Path(cmd[-1]).write_bytes(b'x' * 2000)
                return subprocess.CompletedProcess(cmd, 0, stdout="1.0\n")
            with patch.object(bd.subprocess, "run", side_effect=fake_command) as run:
                bd.generate_story_audio(spec, folder)
                self.assertEqual(sum(c.args[0][0] == "edge-tts" for c in run.call_args_list), 1)
                run.reset_mock()
                bd.generate_story_audio(spec, folder)
                self.assertFalse(any(c.args[0][0] == "edge-tts" for c in run.call_args_list))
                spec["timeline"][0]["voiceoverText"] = "Different script"
                bd.generate_story_audio(spec, folder)
                self.assertTrue(any(c.args[0][0] == "edge-tts" for c in run.call_args_list))

    def test_tts_failure_does_not_create_silent_success(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(bd.subprocess, "run", side_effect=OSError("offline")), patch.object(bd.time, "sleep"):
            with self.assertRaisesRegex(RuntimeError, "TTS failed"):
                bd.generate_story_audio({"timeline": [{"sceneNumber": 1, "voiceoverText": "Test"}]}, folder)
            self.assertFalse((Path(folder) / "scene_1.mp3.sha256").exists())

    def test_draft_output_never_updates_master_or_demos(self):
        self.spec["editorialGate"]["editorApproved"] = False
        self.spec["timeline"] = [{"sceneNumber": 1, "layout": "outro", "durationSeconds": .1,
                                  "voiceoverText": "Test", "visualAsset": {"type": "solid"}}]
        class FakePipe:
            def write(self, data):
                pass
            def close(self):
                pass
        class FakeProcess:
            stdin = FakePipe()
            def wait(self):
                return 0
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "spec.json"
            path.write_text(json.dumps(self.spec))
            with patch.object(bd, "BUILD_DIR", str(Path(folder) / "build")), patch.object(bd, "OUTPUT_DIR", str(Path(folder) / "output")), \
                 patch.object(bd, "generate_story_audio", return_value=[(1, .1, "test.mp3")]), \
                 patch.object(bd.subprocess, "Popen", return_value=FakeProcess()), \
                 patch.object(bd.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, stdout="duration=0.3")) as run:
                result = bd.render_story_from_spec(path, draft=True)
                self.assertEqual(Path(result).parent, Path(folder) / "build/drafts")
                self.assertFalse((Path(folder) / "output").exists())
                self.assertFalse(any(c.args[0][0] == "cp" or "+faststart" in c.args[0] for c in run.call_args_list))


if __name__ == "__main__":
    unittest.main()
