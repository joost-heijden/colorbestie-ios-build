"""macOS pre-upload guard: approved source and actual iPhone/iPad archive pixels."""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import struct
import subprocess
import sys

APPROVED = "30af857b155e4052dee2cecf8142138316f5a12f2e1d2d076f13e65c68514e0b"
source, app, output = map(Path, sys.argv[1:4])
assert hashlib.sha256(source.read_bytes()).hexdigest() == APPROVED, "AppIcon source is not the approved public icon"
assert struct.unpack(">II", source.read_bytes()[16:24]) == (1024, 1024)
contents = json.loads((source.parent / "Contents.json").read_text())
assert contents["images"] == [{"filename": source.name, "idiom": "universal", "platform": "ios", "size": "1024x1024"}]
info = plistlib.loads((app / "Info.plist").read_bytes())
for key in ("CFBundleIcons", "CFBundleIcons~ipad"):
    assert info[key]["CFBundlePrimaryIcon"]["CFBundleIconName"] == "AppIcon"
work = output.parent / "icon-reference-work"
catalog = work / "Assets.xcassets/AppIcon.appiconset"
catalog.mkdir(parents=True)
output.mkdir(parents=True)
shutil.copyfile(source, catalog / source.name)
(catalog / "Contents.json").write_text(json.dumps(contents))
(catalog.parent / "Contents.json").write_text(json.dumps({"info": {"author": "xcode", "version": 1}}))
compiled = work / "compiled"
compiled.mkdir()
subprocess.run(["xcrun", "actool", str(catalog.parent), "--compile", str(compiled), "--platform", "iphoneos", "--minimum-deployment-target", info["MinimumOSVersion"], "--target-device", "iphone", "--target-device", "ipad", "--app-icon", "AppIcon", "--output-partial-info-plist", str(work / "partial.plist"), "--compress-pngs"], check=True)

def pixels(file):
    data = file.read_bytes()
    assert data[:2] == b"BM"
    offset, = struct.unpack_from("<I", data, 10)
    width, height, planes, bits = struct.unpack_from("<iiHH", data, 18)
    assert width > 0 and height != 0 and planes == 1 and bits in (24, 32)
    compression, = struct.unpack_from("<I", data, 30)
    assert compression in (0, 3), "Unexpected BMP compression"
    size = ((width * bits + 31) // 32 * 4) * abs(height)
    raw = data[offset:offset + size]
    assert len(raw) == size
    return width, height, bits, compression, data[54:66] if compression == 3 else b"", raw

proof = {"approvedSourceSha256": APPROVED, "sourceCommit": os.environ["SOURCE_COMMIT"], "build": os.environ["BUILD_NUMBER"], "passed": True, "icons": []}
for archive_name, public_name, size in (("AppIcon60x60@2x.png", "iPhone-120.png", 120), ("AppIcon76x76@2x~ipad.png", "iPad-152.png", 152)):
    actual, expected = work / "actual.bmp", work / "expected.bmp"
    for image, bmp in ((app / archive_name, actual), (compiled / archive_name, expected)):
        assert image.is_file(), "Expected compiled iPhone/iPad icon is missing"
        subprocess.run(["sips", "-s", "format", "bmp", str(image), "--out", str(bmp)], check=True)
    actual_pixels, expected_pixels = pixels(actual), pixels(expected)
    assert (actual_pixels[0], abs(actual_pixels[1])) == (size, size), f"Unexpected BMP dimensions {actual_pixels[:2]}; expected {size}x{size}"
    assert actual_pixels == expected_pixels, "Archived icon pixels do not match independently compiled approved icon"
    exported = output / public_name
    # BMP re-encoding strips the compiled PNG metadata before public inspection.
    subprocess.run(["sips", "-s", "format", "png", str(actual), "--out", str(exported)], check=True)
    proof["icons"].append({"file": public_name, "size": size, "pngSha256": hashlib.sha256(exported.read_bytes()).hexdigest()})
(output / "proof.json").write_text(json.dumps(proof, indent=2) + "\n")
print("Approved public AppIcon: source SHA256 and actual iPhone/iPad archive pixels verified.")
