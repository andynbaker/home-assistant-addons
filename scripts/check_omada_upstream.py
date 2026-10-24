#!/usr/bin/env python3
"""Propose reviewed updates to the legacy 3.2 image; never follow latest."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
IMAGE = "mbentley/omada-controller:3.2"
UPSTREAM = "mbentley/docker-omada-controller"
ARCHIVE_REF = "archive_v3_v4"
STATE_PATH = ".github/omada-v3-upstream.json"
TRACKED_PATHS = [STATE_PATH, "omada_v3/Dockerfile", "omada_v3/config.yaml",
                 "omada_v3/CHANGELOG.md"]


def fetch(url, headers=None):
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read(), response.headers


def github(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "omada-v3-updater"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    body, _ = fetch("https://api.github.com/repos/" + UPSTREAM + "/" + path, headers)
    return json.loads(body)


def snapshot():
    query = urllib.parse.urlencode({"service": "registry.docker.io",
                                   "scope": "repository:mbentley/omada-controller:pull"})
    body, _ = fetch("https://auth.docker.io/token?" + query)
    token = json.loads(body)["token"]
    body, headers = fetch(
        "https://registry-1.docker.io/v2/mbentley/omada-controller/manifests/3.2",
        {"Authorization": "Bearer " + token,
         "Accept": "application/vnd.oci.image.index.v1+json, "
                   "application/vnd.docker.distribution.manifest.list.v2+json"})
    digest = "sha256:" + hashlib.sha256(body).hexdigest()
    if headers.get("Docker-Content-Digest") != digest:
        raise ValueError("Registry manifest digest did not match the downloaded content")
    platforms = {(m.get("platform", {}).get("os"), m.get("platform", {}).get("architecture"))
                 for m in json.loads(body).get("manifests", [])}
    if not {("linux", "amd64"), ("linux", "arm64")} <= platforms:
        raise ValueError("The 3.2 image no longer provides both amd64 and arm64")
    archive = github("commits/" + ARCHIVE_REF)["sha"]
    readme = github("contents/README_v3_and_v4.md")["sha"]
    for value in (archive, readme):
        if not re.fullmatch(r"[0-9a-f]{40}", value):
            raise ValueError("Invalid upstream Git SHA")
    return {"image": IMAGE, "digest": digest, "source_repository": UPSTREAM,
            "archived_source_ref": ARCHIVE_REF, "archived_source_commit": archive,
            "legacy_readme_blob": readme}


def apply_update(root, current):
    state_path = root / STATE_PATH
    previous = json.loads(state_path.read_text()) if state_path.exists() else None
    if current["image"] != IMAGE or current["source_repository"] != UPSTREAM:
        raise ValueError("Updater may only track the configured legacy image and repository")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", current["digest"]):
        raise ValueError("Invalid image digest")
    dockerfile = root / "omada_v3/Dockerfile"
    source = dockerfile.read_text()
    pattern = r"(?m)^FROM mbentley/omada-controller:3\.2(?:@sha256:[0-9a-f]{64})?$"
    replacement = "FROM " + IMAGE + "@" + current["digest"]
    source, count = re.subn(pattern, replacement, source)
    if count != 1:
        raise ValueError("Expected exactly one legacy Omada base image")
    if previous == current and source == dockerfile.read_text():
        return False
    config = root / "omada_v3/config.yaml"
    text = config.read_text()
    match = re.search(r'(?m)^version: "(3\.2\.17)-(\d+)"$', text)
    if not match:
        raise ValueError("Unexpected add-on version; refusing to change release series")
    version = match[1] + "-" + str(int(match[2]) + 1)
    text = text[:match.start()] + 'version: "' + version + '"' + text[match.end():]
    changelog = root / "omada_v3/CHANGELOG.md"
    changes = changelog.read_text()
    if not changes.startswith("# Changelog\n"):
        raise ValueError("Unexpected changelog format")
    entry = ("\n## " + version + "\n\n"
             "- Refresh the reviewed Omada 3.2 upstream image/source baseline.\n"
             "- Pin the multi-architecture image to `" + current["digest"] + "`.\n"
             "- Keep the controller on the legacy 3.2 series.\n")
    dockerfile.write_text(source)
    config.write_text(text)
    changelog.write_text(changes.replace("# Changelog\n", "# Changelog\n" + entry, 1))
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n")
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    current = snapshot()
    if args.dry_run:
        print(json.dumps(current, indent=2, sort_keys=True))
        return
    changed = apply_update(ROOT, current)
    print("Upstream changes prepared for review." if changed else "No upstream changes.")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a") as stream:
            stream.write("changed=" + str(changed).lower() + "\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as stream:
            stream.write("## Omada v3 upstream check\n\n" +
                         ("Update PR changes prepared." if changed else "No changes detected.") +
                         "\n\nImage: `" + IMAGE + "`\n\nDigest: `" + current["digest"] + "`\n")


if __name__ == "__main__":
    main()
