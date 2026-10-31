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

print("UI patches applied OK")
