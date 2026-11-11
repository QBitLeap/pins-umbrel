"""Package the pinned PINS CLI and indexer with the native Node runtime."""

import argparse
import json
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
from zipfile import ZipFile

from fetch_upstream import fetch
from prepare_context import prepare

ROOT = Path(__file__).resolve().parents[1]
NODE_VERSION = "v22.23.4"


def package(output, assets):
    os_name = {"Darwin": "macos", "Windows": "windows", "Linux": "linux"}[platform.system()]
    architecture = {"x86_64": "x64", "amd64": "x64", "arm64": "arm64",
                    "aarch64": "arm64"}[platform.machine().lower()]
    windows = os_name == "windows"
    node = Path(subprocess.check_output(["node", "-p", "process.execPath"], text=True).strip())
    if subprocess.check_output([node, "--version"], text=True).strip() != NODE_VERSION:
        raise ValueError(f"Expected Node {NODE_VERSION}")
    node_license = (node.parent if windows else node.parent.parent) / "LICENSE"
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pins-desktop-") as directory:
        work = Path(directory)
        lock = json.loads((ROOT / "upstream.lock.json").read_text())
        upstream = work / "upstream"
        fetch(upstream, lock)
        context = work / "context"
        prepare(upstream, context)
        bundle = work / "pins"
        bundle.mkdir()
        protocol = bundle / "protocol"
        shutil.move(context / "protocol", protocol)
        if windows:
            canonical = protocol / "scripts/canonical-batch.ts"
            text = canonical.read_text(encoding="utf-8")
            old = 'execFileSync("unzip", ["-q", "-o", zipPath, "-d", staging], { stdio: "pipe" });'
            if text.count(old) != 1:
                raise ValueError("Review the upstream collection extraction before packaging Windows")
            canonical.write_text(text.replace(old, 'execFileSync("tar.exe", ["-xf", zipPath, "-C", staging], { stdio: "pipe" });'),
                                 encoding="utf-8")
        subprocess.run([shutil.which("npm"), "ci", "--omit=dev", "--ignore-scripts", "--no-audit", "--no-fund"],
                       cwd=protocol, check=True)
        shutil.copy2(node, bundle / node.name)
        shutil.copyfile(node_license, bundle / "NODE-LICENSE")
        shutil.copyfile(ROOT / "README.md", bundle / "README.md")
        shutil.copyfile(upstream / "docs/inscriber/README.md", bundle / "INSCRIBER.md")
        shutil.copyfile(assets / "icon-overlays/NOTICE.md", bundle / "ICON-NOTICE.md")
        for suffix in ("", "-testnet4"):
            shutil.copyfile(assets / f"platform-icons/pins/{os_name}{suffix}.png", bundle / f"icon{suffix}.png")
        (bundle / "source.json").write_text(json.dumps({
            "upstream": lock,
            "node": NODE_VERSION,
            "windowsArchiveExtractor": "Windows tar.exe" if windows else None,
        }, indent=2) + "\n", encoding="utf-8")
        for name in ("pins", "pins-indexer"):
            script = "packages/inscriber/cli.ts" if name == "pins" else "scripts/indexer-run.ts"
            if windows:
                launch = bundle / f"{name}.cmd"
                launch.write_text(f'@echo off\n"%~dp0node.exe" --experimental-strip-types "%~dp0protocol/{script}" %*\n',
                                  encoding="utf-8")
            else:
                launch = bundle / name
                launch.write_text(
                    f'#!/bin/sh\nhere=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\n'
                    f'exec "$here/node" --experimental-strip-types "$here/protocol/{script}" "$@"\n',
                    encoding="utf-8")
                launch.chmod(0o755)
        version = json.loads((upstream / "package.json").read_text())["version"]
        archive = shutil.make_archive(str(output / f"pins-{version}-{os_name}-{architecture}"),
                                      "zip" if windows else "gztar", root_dir=work, base_dir=bundle.name)
        extracted = work / "extracted"
        shutil.unpack_archive(archive, extracted)
        smoke(extracted / bundle.name, work, windows)
    print(archive)


def smoke(bundle, work, windows):
    pub = work / "issuer.json"
    pub.write_text(json.dumps({"issuerPublic": "01" * 32}), encoding="utf-8")
    entry = bundle / ("pins.cmd" if windows else "pins")
    for network in ("mainnet", "testnet4"):
        address = subprocess.check_output([entry, "address", "--pub", pub, "--network", network], cwd=work, text=True)
        if f"{network} funding address " not in address:
            raise ValueError("Packaged inscriber did not select the requested network")
    node = bundle / ("node.exe" if windows else "node")
    indexer = subprocess.run([node, "--experimental-strip-types", bundle / "protocol/scripts/indexer-run.ts",
                              "--port", "0"], cwd=work, capture_output=True, text=True)
    if indexer.returncode != 1 or "--port must be a number" not in indexer.stderr:
        raise ValueError("Packaged indexer did not parse its startup arguments")
    fixture = work / "collection.zip"
    with ZipFile(fixture, "w") as archive:
        archive.writestr("fixture.txt", "intentionally incomplete collection")
    module = (bundle / "protocol/scripts/canonical-batch.ts").as_uri()
    subprocess.run([node, "--experimental-strip-types", "--input-type=module", "-e",
                    "import {loadCanonical} from " + json.dumps(module) + ";"
                    "try { await loadCanonical(process.argv[1]); process.exitCode = 1; } "
                    "catch (error) { if (!String(error).includes('The zip must contain images/')) throw error; }",
                    fixture], cwd=work, check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--assets", required=True, type=Path)
    args = parser.parse_args()
    package(args.output.resolve(), args.assets.resolve())
