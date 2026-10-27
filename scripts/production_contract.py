"""Small offline controls shared by the renderer and its tests.

Metadata checks do not establish source truth or authenticate a human reviewer.
"""
import hashlib
import json

LAYOUTS = ("hook", "receipt", "key_points", "facts_figures", "outro")


def scene_layout(scene):
    explicit = scene.get("layout")
    if explicit is not None:
        if explicit not in LAYOUTS:
            raise ValueError(f"Unknown scene layout: {explicit!r}")
        return explicit
    if scene.get("type") == "outro_archive" or scene.get("figure", {}).get("type") == "outro_archive":
        return "outro"
    return {1: "hook", 2: "receipt", 3: "key_points", 4: "facts_figures"}.get(scene.get("sceneNumber", 1), "outro")


def check_render_contract(spec, draft=False):
    timeline = spec.get("timeline", [])
    if not timeline:
        raise ValueError("Timeline is empty")
    numbers = [scene.get("sceneNumber") for scene in timeline]
    if any(type(n) is not int or n < 1 for n in numbers) or len(set(numbers)) != len(numbers):
        raise ValueError("Scene numbers must be unique positive integers")
    for scene in timeline:
        scene_layout(scene)
    if draft:
        return
    gate = spec.get("editorialGate", {})
    if (gate.get("status") != "approved" or gate.get("editorApproved") is not True
            or not isinstance(gate.get("reviewedBy"), str) or not gate["reviewedBy"].strip()):
        raise ValueError("Editorial approval required. Use --draft for an isolated review render.")


def audio_fingerprint(text, voice, rate="+18%"):
    payload = json.dumps([text, voice, rate], ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
