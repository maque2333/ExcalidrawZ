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

print("UI patches applied OK")
