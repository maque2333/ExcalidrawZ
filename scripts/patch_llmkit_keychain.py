#!/usr/bin/env python3
"""Patch LLMKit's AnonIdentityManager so it no longer uses the login Keychain.

The self-built ExcalidrawZ is ad-hoc signed; every re-sign changes its cdhash and
macOS keeps asking for the login Keychain password whenever LLMKit reads its
anonymous identity. Storing it in UserDefaults removes that Keychain access.

Usage: python3 patch_llmkit_keychain.py <checkout-root> [<checkout-root>...]
"""

import sys
from pathlib import Path

REPLACEMENT = '''struct AnonIdentityManager {
    private static let defaultsKeyPrefix = "LLMKit.anon.uuid."

    static func loadAnonID(for bundleID: String) -> String? {
        UserDefaults.standard.string(forKey: defaultsKeyPrefix + bundleID)
    }

    static func loadOrCreateAnonID(for bundleID: String) -> String {
        if let existing = loadAnonID(for: bundleID) {
            return existing
        }
        let newID = UUID().uuidString
        UserDefaults.standard.set(newID, forKey: defaultsKeyPrefix + bundleID)
        return newID
    }
}
'''

patched = 0
for arg in sys.argv[1:]:
    root = Path(arg)
    if not root.is_dir():
        continue
    for path in root.rglob("AnonAuthProvider.swift"):
        source = path.read_text()
        marker = "struct AnonIdentityManager {"
        index = source.find(marker)
        if index < 0:
            continue
        source = source[:index] + REPLACEMENT
        if "SecItem" in source:
            raise SystemExit(f"SecItem still present after patch: {path}")
        path.write_text(source)
        patched += 1
        print(f"patched {path}")

if patched == 0:
    raise SystemExit("no LLMKit AnonAuthProvider.swift found / patched")
print(f"patched {patched} LLMKit file(s)")
