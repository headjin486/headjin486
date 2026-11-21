#!/usr/bin/env python3
import json, re, sys
from pathlib import Path

root = Path(sys.argv[1])
app = root / "app"
config = app / "google-services.json"
if not config.is_file():
    raise SystemExit("Firebase config missing: app/google-services.json")
data = json.loads(config.read_text(encoding="utf-8"))
package_name = data.get("client", [{}])[0].get("client_info", {}).get("android_client_info", {}).get("package_name")
if package_name != "com.earthunlock.app":
    raise SystemExit(f"Firebase package mismatch: expected com.earthunlock.app, got {package_name!r}")

root_gradle = root / "build.gradle.kts"
app_gradle = app / "build.gradle.kts"
if not root_gradle.is_file() or not app_gradle.is_file():
    raise SystemExit("Expected Kotlin Gradle files were not found")
root_text = root_gradle.read_text(encoding="utf-8")
app_text = app_gradle.read_text(encoding="utf-8")

plugin_line = '    id("com.google.gms.google-services") version "4.4.2" apply false'
if "com.google.gms.google-services" not in root_text:
    match = re.search(r"plugins\s*\{", root_text)
    if not match:
        raise SystemExit("Root build.gradle.kts has no plugins block; manual Gradle integration required")
    insert_at = match.end()
    root_text = root_text[:insert_at] + "\n" + plugin_line + root_text[insert_at:]
    root_gradle.write_text(root_text, encoding="utf-8")

app_line = '    id("com.google.gms.google-services")'
if "com.google.gms.google-services" not in app_text:
    match = re.search(r"plugins\s*\{", app_text)
    if not match:
        raise SystemExit("App build.gradle.kts has no plugins block; manual Gradle integration required")
    insert_at = match.end()
    app_text = app_text[:insert_at] + "\n" + app_line + app_text[insert_at:]
    app_gradle.write_text(app_text, encoding="utf-8")

print("Firebase config validated and Google Services Gradle plugin configured.")
