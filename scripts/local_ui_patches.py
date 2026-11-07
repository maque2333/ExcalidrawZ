#!/usr/bin/env python3
"""Local UI patches for the self-built ExcalidrawZ (Debug, unsigned).

Applied by the GitHub Actions workflow after checkout, before xcodebuild.
Usage: python3 local_ui_patches.py <repo-root>
"""

import re
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

# 1. What's New: Debug builds force the sheet on every launch.
p = root / "ExcalidrawZ/components/WhatsNew/WhatsNewSheetView.swift"
s = p.read_text()
patched = re.sub(r"\n#if DEBUG\n[ \t]*isPresented = true\n#endif", "", s, count=1)
if patched == s:
    raise SystemExit("WhatsNew DEBUG block not found")
p.write_text(patched)

# 2. Home: remove the tips section.
p = root / "ExcalidrawZ/ContentView+/Detail/Home/HomeView.swift"
s = p.read_text()
old = "                        HomeTipsSection()"
if old not in s:
    raise SystemExit("HomeTipsSection call not found")
p.write_text(s.replace(old, "                        EmptyView()", 1))

# 3. Sidebar: opaque background + remove the separator line below the toolbar.
p = root / "ExcalidrawZ/Sidebar/SidebarView.swift"
s = p.read_text()
old = "        GroupListView(sortField: fileState.sortField)\n"
if old not in s:
    raise SystemExit("GroupListView call not found")
s = s.replace(old, old + "            .background(Color.windowBackgroundColor)\n", 1)
border = "\n            .border(.top, color: .separatorColor)"
if border not in s:
    raise SystemExit("sidebar top border not found")
p.write_text(s.replace(border, "", 1))

# 4. Sidebar rows: flat fill instead of liquid glass.
p = root / "ExcalidrawZ/Sidebar/components/SidebarRowModifier.swift"
s = p.read_text()
old = """                    .fill(.clear)
                    .glassEffect(
                        Glass.regular
                            .tint(tint)
                            .interactive(!hoverSuppressed),
                        in: Capsule()
                    )"""
if old not in s:
    raise SystemExit("glassEffect block not found")
p.write_text(s.replace(old, "                    .fill(tint)", 1))

# 5. Hide the AI credits button in the top-right toolbar (home / no active file).
p = root / "ExcalidrawZ/ExcalidrawView/Toolbar/ExcalidrawEditorToolbarModifier.swift"
s = p.read_text()
old = """                if aiChatPreferences.isAIEnabled && AIChatAvailability.isAvailable {
                    AICreditsToolbarButton()
                }
"""
if old not in s:
    raise SystemExit("AI credits toolbar block not found")
p.write_text(s.replace(old, "", 1))

# 6. Move the sidebar toolbar to the root NavigationSplitView (one unified top bar).
p = root / "ExcalidrawZ/ContentView+/Detail/ContentViewModern.swift"
s = p.read_text()
patched = re.sub(r"\n[ \t]*\.toolbar\(content: sidebarToolbar\)", "", s)
if patched == s:
    raise SystemExit("sidebar toolbar attachments not found")
old = """        } detail: {
             ContentViewDetail(isSettingsPresented: $isSettingsPresented)
        }"""
new = old + "\n        .toolbar(content: sidebarToolbar)"
if old not in patched:
    raise SystemExit("NavigationSplitView detail block not found")
p.write_text(patched.replace(old, new, 1))

# 7. Remove the system titlebar separator line.
p = root / "ExcalidrawZ/AppDelegate.swift"
s = p.read_text()
old = """    func applicationDidFinishLaunching(_ notification: Notification) {
        // disable auto capitalization
        UserDefaults.standard.set(false, forKey: "NSAutomaticCapitalizationEnabled")
    }"""
new = """    func applicationDidFinishLaunching(_ notification: Notification) {
        // disable auto capitalization
        UserDefaults.standard.set(false, forKey: "NSAutomaticCapitalizationEnabled")
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            for window in NSApp.windows {
                window.titlebarSeparatorStyle = .none
            }
        }
    }"""
if old not in s:
    raise SystemExit("applicationDidFinishLaunching block not found")
p.write_text(s.replace(old, new, 1))

# 8. Restore a toolbar for the floating-bar layout (legacy content view).
p = root / "ExcalidrawZ/ContentView+/Detail/ContentViewLagacy.swift"
s = p.read_text()
old = """            .padding(.top, 10)
            .padding(.horizontal, 10)
            .padding(.bottom, 40)
        }
    }
}"""
new = """            .padding(.top, 10)
            .padding(.horizontal, 10)
            .padding(.bottom, 40)
        }
        .toolbar {
            ToolbarItemGroup(placement: .primaryAction) {
                NewFileButton(usesFileHomeOpenTransition: fileState.currentActiveGroup != nil)
            }
        }
    }
}"""
if old not in s:
    raise SystemExit("ContentViewLagacy body tail not found")
p.write_text(s.replace(old, new, 1))

# 9. Apply the opaque sidebar background only in the sidebar layout.
p = root / "ExcalidrawZ/Sidebar/SidebarView.swift"
s = p.read_text()
old = "            .background(Color.windowBackgroundColor)"
new = """            .background {
                if appPreference.sidebarLayout == .sidebar {
                    Color.windowBackgroundColor
                }
            }"""
if old not in s:
    raise SystemExit("sidebar background line not found")
p.write_text(s.replace(old, new, 1))

print("UI patches applied OK")

# 10. Backups: stop using the login Keychain for the encrypted-backup master key.
#     The self-built app is ad-hoc signed, so every re-sign changes its cdhash and
#     macOS keeps asking for the login Keychain password. Store the master key in a
#     0600 file under Application Support instead (legacy Keychain key is only read
#     on demand to decrypt backups created before this change).
p = root / "ExcalidrawZ/Persistence/Encryption/EncryptedBackupService.swift"
s = p.read_text()
marker = "private enum BackupEncryptionKeyStore {"
idx = s.find(marker)
if idx < 0:
    raise SystemExit("BackupEncryptionKeyStore not found")
new_key_store = '''private enum BackupEncryptionKeyStore {
    private static let byteCount = 32
    private static let legacyAccount = "InternalBackupMasterKey"
    private static let legacyService = "\\(Bundle.main.bundleIdentifier ?? "com.chocoford.ExcalidrawZ").backup-encryption"
    private static let keyFileName = "backup-master-key"

    private static let queue = DispatchQueue(label: "ExcalidrawZ.BackupEncryptionKeyStore")
    private static var cachedKeyData: Data?

    static func loadOrCreateKeyData() throws -> Data {
        try queue.sync {
            if let cachedKeyData {
                return cachedKeyData
            }
            if let existingKeyData = try loadKeyDataFromFile() {
                let validated = try validatedKeyData(existingKeyData)
                cachedKeyData = validated
                return validated
            }
            let keyData = try RecoveryKeyService.randomSalt(byteCount: byteCount)
            try saveKeyDataToFile(keyData)
            cachedKeyData = keyData
            return keyData
        }
    }

    static func loadExistingKeyData() throws -> Data {
        try queue.sync {
            if let cachedKeyData {
                return cachedKeyData
            }
            guard let existingKeyData = try loadKeyDataFromFile() else {
                throw EncryptedBackupError.missingKey
            }
            let validated = try validatedKeyData(existingKeyData)
            cachedKeyData = validated
            return validated
        }
    }

    /// Only used to decrypt backups that were encrypted before the master key moved
    /// out of the Keychain. Never touched by launch/termination paths.
    static func loadLegacyKeychainKeyData() -> Data? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: legacyService,
            kSecAttrAccount as String: legacyAccount,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]
        var item: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &item)
        guard status == errSecSuccess, let data = item as? Data else {
            return nil
        }
        return try? validatedKeyData(data)
    }

    private static func validatedKeyData(_ keyData: Data) throws -> Data {
        guard keyData.count == byteCount else {
            throw EncryptedBackupError.invalidKey
        }
        return keyData
    }

    private static func keyFileURL() throws -> URL {
        let supportDir = try FileManager.default.url(
            for: .applicationSupportDirectory,
            in: .userDomainMask,
            appropriateFor: nil,
            create: true
        )
        let directory = supportDir.appendingPathComponent("ExcalidrawZ", isDirectory: true)
        if !FileManager.default.fileExists(atPath: directory.path) {
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        }
        return directory.appendingPathComponent(keyFileName, isDirectory: false)
    }

    private static func loadKeyDataFromFile() throws -> Data? {
        let fileURL = try keyFileURL()
        guard FileManager.default.fileExists(atPath: fileURL.path) else {
            return nil
        }
        return try Data(contentsOf: fileURL)
    }

    private static func saveKeyDataToFile(_ keyData: Data) throws {
        let fileURL = try keyFileURL()
        try keyData.write(to: fileURL, options: .atomic)
        try? FileManager.default.setAttributes(
            [.posixPermissions: 0o600],
            ofItemAtPath: fileURL.path
        )
    }
}
'''
s = s[:idx] + new_key_store
p.write_text(s)

# 11. Decrypt: old encrypted backups use the legacy Keychain master key; fall back to
#     it only when the envelope keyID does not match the file-backed master key.
old_decrypt = '''        do {
            let keyData = try BackupEncryptionKeyStore.loadExistingKeyData()
            if let keyID = envelope.keyID,
               keyID != keyIdentifier(for: keyData) {
                throw EncryptedBackupError.keyMismatch
            }
            return try AES.GCM.open(
                envelope.payload.sealedBox(),
                using: SymmetricKey(data: keyData),
                authenticating: associatedData
            )'''
new_decrypt = '''        do {
            var keyData = try BackupEncryptionKeyStore.loadOrCreateKeyData()
            if let keyID = envelope.keyID,
               keyID != keyIdentifier(for: keyData) {
                if let legacyKeyData = BackupEncryptionKeyStore.loadLegacyKeychainKeyData(),
                   keyID == keyIdentifier(for: legacyKeyData) {
                    keyData = legacyKeyData
                } else {
                    throw EncryptedBackupError.keyMismatch
                }
            }
            return try AES.GCM.open(
                envelope.payload.sealedBox(),
                using: SymmetricKey(data: keyData),
                authenticating: associatedData
            )'''
if old_decrypt not in s:
    raise SystemExit("decrypt block not found")
s = s.replace(old_decrypt, new_decrypt, 1)
p.write_text(s)

print("keychain-free backup patches applied OK")
