#!/usr/bin/env python3
"""一鍵體檢 iOS IPA（或 .app 資料夾）裡的 WidgetKit 擴展。

檢查「小工具為什麼沒出現在小工具庫」的四個關鍵環節，並在最後給出結論：

  1. 擴展有沒有被安裝進 PlugIns/
  2. 擴展的簽章 App ID 有沒有涵蓋擴展自己的 bundle ID
  3. 擴展產物完不完整（Metadata.appintents / Assets.car / PkgInfo / NSExtension）
  4. 二進位對不對（LC_MAIN / platform=iOS / SDK 版本 / 連結的 framework）

只用 Python 標準函式庫，Windows / macOS / Linux 都能跑，不需要 Xcode 或 otool。

用法：
    python inspect_ipa.py App.ipa
    python inspect_ipa.py /path/to/Payload/App.app
    python inspect_ipa.py App.ipa --json        # 輸出機器可讀結果

離開碼：0 = 全部通過；1 = 有項目不合格。
"""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import struct
import sys
import tempfile
import zipfile

# ---------------------------------------------------------------- Mach-O

LC_REQ_DYLD = 0x80000000
LC_SEGMENT_64 = 0x19
LC_CODE_SIGNATURE = 0x1D
LC_BUILD_VERSION = 0x32
LC_VERSION_MIN_IPHONEOS = 0x25
LC_MAIN = 0x28
LC_LOAD_DYLIB = 0xC
LC_LOAD_WEAK_DYLIB = 0x18
LC_REEXPORT_DYLIB = 0x1F
LC_LOAD_UPWARD_DYLIB = 0x23

MH_MAGIC_64 = 0xFEEDFACF
MH_EXECUTE = 2

PLATFORMS = {1: "macOS", 2: "iOS", 3: "tvOS", 4: "watchOS", 6: "macCatalyst",
             7: "iOS-simulator", 11: "visionOS"}

HEADER_FLAGS = {
    0x1: "MH_NOUNDEFS", 0x4: "MH_DYLDLINK", 0x80: "MH_TWOLEVEL",
    0x200000: "MH_PIE", 0x2000000: "MH_APP_EXTENSION_SAFE",
}

CS_SLOT_CODE_DIRECTORY = 0
CS_SLOT_ENTITLEMENTS = 5
CS_SLOT_DER_ENTITLEMENTS = 7


def _version(value: int) -> str:
    return "%d.%d.%d" % ((value >> 16) & 0xFFFF, (value >> 8) & 0xFF, value & 0xFF)


def parse_macho(path: str) -> dict:
    """回傳 {sdk, platform, minos, is_executable, has_lc_main, flags, dylibs, entitlements}。"""
    with open(path, "rb") as handle:
        data = handle.read()

    if len(data) < 32:
        raise ValueError("檔案太小，不是 Mach-O")

    magic = struct.unpack_from("<I", data, 0)[0]
    if magic != MH_MAGIC_64:
        raise ValueError("不是 64-bit little-endian Mach-O（magic=%#x）" % magic)

    # mach_header_64 依序是：magic, cputype, cpusubtype, filetype, ncmds, sizeofcmds, flags
    cputype, cpusubtype, file_type, ncmds, sizeofcmds, flags = struct.unpack_from("<iiIIII", data, 4)

    info = {
        "cpu_type": cputype,
        "file_type": file_type,
        "is_executable": file_type == MH_EXECUTE,
        "has_lc_main": False,
        "flags": [name for bit, name in HEADER_FLAGS.items() if flags & bit],
        "app_extension_safe": bool(flags & 0x2000000),
        "platform": None, "platform_name": None, "minos": None, "sdk": None,
        "dylibs": [], "code_signature": None,
    }

    offset = 32
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from("<II", data, offset)
        base = cmd & ~LC_REQ_DYLD

        if base == LC_BUILD_VERSION:
            platform, minos, sdk, _ = struct.unpack_from("<IIII", data, offset + 8)
            info["platform"] = platform
            info["platform_name"] = PLATFORMS.get(platform, str(platform))
            info["minos"] = _version(minos)
            info["sdk"] = _version(sdk)
        elif base == LC_VERSION_MIN_IPHONEOS:
            minos, sdk = struct.unpack_from("<II", data, offset + 8)
            info["platform_name"] = "iOS"
            info["minos"] = _version(minos)
            info["sdk"] = _version(sdk)
        elif base == LC_MAIN:
            info["has_lc_main"] = True
        elif base == LC_CODE_SIGNATURE:
            dataoff, datasize = struct.unpack_from("<II", data, offset + 8)
            info["code_signature"] = (dataoff, datasize)
        elif base in (LC_LOAD_DYLIB, LC_LOAD_WEAK_DYLIB, LC_REEXPORT_DYLIB, LC_LOAD_UPWARD_DYLIB):
            name_offset = struct.unpack_from("<I", data, offset + 8)[0]
            raw = data[offset + name_offset:offset + cmdsize].split(b"\x00")[0]
            info["dylibs"].append(raw.decode("utf-8", "replace"))

        offset += cmdsize

    info["entitlements"] = _parse_entitlements(data, info["code_signature"])
    return info


def _parse_entitlements(data: bytes, code_signature) -> dict:
    """從簽章 SuperBlob 取出 entitlements（slot 5）。"""
    if not code_signature:
        return {}
    offset, size = code_signature
    blob = data[offset:offset + size]
    if len(blob) < 12:
        return {}

    _, _, count = struct.unpack_from(">III", blob, 0)
    slots = {}
    cursor = 12
    for _ in range(count):
        slot_type, slot_offset = struct.unpack_from(">II", blob, cursor)
        slots[slot_type] = slot_offset
        cursor += 8

    if CS_SLOT_ENTITLEMENTS not in slots:
        return {}

    chunk = blob[slots[CS_SLOT_ENTITLEMENTS]:]
    if CS_SLOT_DER_ENTITLEMENTS in slots and slots[CS_SLOT_DER_ENTITLEMENTS] > slots[CS_SLOT_ENTITLEMENTS]:
        chunk = blob[slots[CS_SLOT_ENTITLEMENTS]:slots[CS_SLOT_DER_ENTITLEMENTS]]

    start = chunk.find(b"<?xml")
    end = chunk.find(b"</plist>")
    if start < 0 or end < 0:
        return {}
    try:
        return plistlib.loads(chunk[start:end + 8])
    except Exception:
        return {}


# ---------------------------------------------------------------- 檢查邏輯

def covers(app_identifier: str, bundle_identifier: str) -> bool:
    """<TeamID>.<AppID>（或 <TeamID>.*）是否涵蓋指定的 bundle ID。"""
    if not app_identifier or not bundle_identifier:
        return False
    dot = app_identifier.find(".")
    if dot < 0:
        return False
    identifier = app_identifier[dot + 1:]
    if identifier == "*":
        return True
    if identifier.endswith(".*"):
        return bundle_identifier.startswith(identifier[:-1])
    return identifier == bundle_identifier


def read_plist(path: str) -> dict:
    with open(path, "rb") as handle:
        return plistlib.load(handle)


def probe_appex(appex_dir: str) -> dict:
    """檢查單一 .appex。"""
    info_path = os.path.join(appex_dir, "Info.plist")
    info = read_plist(info_path) if os.path.exists(info_path) else {}

    executable = info.get("CFBundleExecutable", "")
    executable_path = os.path.join(appex_dir, executable)
    bundle_id = info.get("CFBundleIdentifier", "")

    extension_dict = info.get("NSExtension") or {}
    extension_point = extension_dict.get("NSExtensionPointIdentifier")

    metadata_dir = os.path.join(appex_dir, "Metadata.appintents")
    actions_path = os.path.join(metadata_dir, "extract.actionsdata")
    intents = []
    if os.path.exists(actions_path):
        try:
            with open(actions_path, "r", encoding="utf-8") as handle:
                intents = sorted((json.load(handle).get("actions") or {}).keys())
        except Exception:
            intents = ["<無法解析>"]

    macho = {}
    if os.path.exists(executable_path):
        try:
            macho = parse_macho(executable_path)
        except Exception as error:  # pragma: no cover
            macho = {"error": str(error)}

    entitlements = macho.get("entitlements") or {}

    return {
        "dir": appex_dir,
        "name": os.path.basename(appex_dir),
        "bundle_id": bundle_id,
        "display_name": info.get("CFBundleDisplayName"),
        "version": info.get("CFBundleShortVersionString"),
        "build": info.get("CFBundleVersion"),
        "package_type": info.get("CFBundlePackageType"),
        "minimum_os": info.get("MinimumOSVersion"),
        "device_family": info.get("UIDeviceFamily"),
        "required_capabilities": info.get("UIRequiredDeviceCapabilities"),
        "extension_point": extension_point,
        "has_ex_attributes": "EXAppExtensionAttributes" in info,
        "has_principal_class": "NSExtensionPrincipalClass" in extension_dict,
        "executable": executable,
        "executable_exists": os.path.exists(executable_path),
        "has_pkg_info": os.path.exists(os.path.join(appex_dir, "PkgInfo")),
        "pkg_info_content": _read_text(os.path.join(appex_dir, "PkgInfo")),
        "has_assets": os.path.exists(os.path.join(appex_dir, "Assets.car")),
        "has_metadata_dir": os.path.isdir(metadata_dir),
        "has_actions_data": os.path.exists(actions_path),
        "has_version_json": os.path.exists(os.path.join(metadata_dir, "version.json")),
        "intents": intents,
        "macho": macho,
        "application_identifier": entitlements.get("application-identifier"),
        "application_groups": entitlements.get("com.apple.security.application-groups") or [],
        "has_entitlements": bool(entitlements),
        "dylibs": macho.get("dylibs") or [],
    }


def _read_text(path: str):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read().strip()
    except Exception:
        return None


def probe_app(app_dir: str) -> dict:
    info_path = os.path.join(app_dir, "Info.plist")
    info = read_plist(info_path) if os.path.exists(info_path) else {}

    executable = info.get("CFBundleExecutable", "")
    executable_path = os.path.join(app_dir, executable)
    macho = {}
    if os.path.exists(executable_path):
        try:
            macho = parse_macho(executable_path)
        except Exception as error:  # pragma: no cover
            macho = {"error": str(error)}
    entitlements = macho.get("entitlements") or {}

    plugins_dir = os.path.join(app_dir, "PlugIns")
    appex_dirs = []
    if os.path.isdir(plugins_dir):
        appex_dirs = sorted(
            os.path.join(plugins_dir, name)
            for name in os.listdir(plugins_dir)
            if name.lower().endswith(".appex")
        )

    return {
        "dir": app_dir,
        "bundle_id": info.get("CFBundleIdentifier"),
        "display_name": info.get("CFBundleDisplayName"),
        "name": info.get("CFBundleName"),
        "version": info.get("CFBundleShortVersionString"),
        "build": info.get("CFBundleVersion"),
        "minimum_os": info.get("MinimumOSVersion"),
        "launch_screen": info.get("UILaunchScreen"),
        "ui_design_requires_compatibility": info.get("UIDesignRequiresCompatibility"),
        "disable_min_frame_duration_phone": info.get("CADisableMinimumFrameDurationOnPhone"),
        "disable_min_frame_duration": info.get("CADisableMinimumFrameDuration"),
        "application_identifier": entitlements.get("application-identifier"),
        "application_groups": entitlements.get("com.apple.security.application-groups") or [],
        "has_entitlements": bool(entitlements),
        "macho": macho,
        "appexes": [probe_appex(path) for path in appex_dirs],
    }


# ---------------------------------------------------------------- 報告

def _mark(ok: bool) -> str:
    return "OK  " if ok else "FAIL"


def report(app: dict) -> tuple[str, bool]:
    lines = []
    problems = []

    def line(text=""):
        lines.append(text)

    def check(ok: bool, label: str, detail: str = ""):
        lines.append("  [%s] %s%s" % (_mark(ok), label, ("  — " + detail) if detail else ""))
        if not ok:
            problems.append(label)
        return ok

    def info(label: str, detail: str = ""):
        """僅供參考、不列入合格與否。"""
        lines.append("  [--  ] %s%s" % (label, ("  — " + detail) if detail else ""))

    def check_provisioning(appex: dict):
        """簽章是否涵蓋擴展自己的 bundle ID。

        尚未被側載工具重新簽名的 IPA 沒有 application-identifier，這是正常的
        （側載工具會自己填），因此那一種情況只提示、不算失敗。
        """
        app_id = appex.get("application_identifier") or ""
        bundle_id = appex.get("bundle_id") or ""

        if not app_id:
            info("簽章 App ID 涵蓋擴展的 bundle ID",
                 "此 IPA 尚未被側載工具重新簽名（正常）。"
                 "安裝後請用 App 內診斷複查：應為 <TeamID>.%s" % bundle_id)
            return
        if covers(app_id, bundle_id):
            check(True, "簽章 App ID 涵蓋擴展的 bundle ID", app_id)
        else:
            check(False, "簽章 App ID 涵蓋擴展的 bundle ID",
                  "App ID=%s，bundle ID=%s" % (app_id, bundle_id))
            line("       → 安裝時選了「Keep App Extensions (Use Main Profile)」。")
            line("         請刪除 App 後重新安裝，改選 Register App ID for Each Extension。")

    line("=" * 68)
    line("主 App")
    line("=" * 68)
    line("  bundle ID      : %s" % app.get("bundle_id"))
    line("  顯示名稱        : %s" % app.get("display_name"))
    line("  版本            : %s (%s)" % (app.get("version"), app.get("build")))
    line("  最低系統        : %s" % app.get("minimum_os"))
    macho = app.get("macho") or {}
    line("  SDK            : %s / %s" % (macho.get("platform_name"), macho.get("sdk")))
    line("  App Group      : %s" % (", ".join(app.get("application_groups") or []) or "（無）"))
    line()

    line("-- 主 App 檢查 --")
    sdk = macho.get("sdk") or ""
    sdk_major = int(sdk.split(".")[0]) if sdk and sdk[0].isdigit() else 0
    check(sdk_major >= 26, "以 iOS 26 以上 SDK 建置（Liquid Glass 的前提）", "sdk=%s" % sdk)
    check(bool(app.get("display_name")), "已設定 CFBundleDisplayName（小工具庫搜尋用）")
    check(not app.get("ui_design_requires_compatibility"),
          "沒有開啟 UIDesignRequiresCompatibility",
          "值=%s" % app.get("ui_design_requires_compatibility"))
    launch = app.get("launch_screen")
    check(isinstance(launch, dict) and "UILaunchScreen" not in launch,
          "UILaunchScreen 是扁平字典（不是巢狀）")
    check(bool(app.get("application_groups")), "主 App 有 App Group 授權")
    line()

    if not app.get("appexes"):
        line("=" * 68)
        line("擴展")
        line("=" * 68)
        check(False, "App bundle 內有 PlugIns/*.appex",
              "找不到任何 .appex：側載工具在簽名時把它剔除了")
        return "\n".join(lines), False

    for appex in app.get("appexes") or []:
        line("=" * 68)
        line("擴展：%s" % appex["name"])
        line("=" * 68)
        line("  bundle ID      : %s" % appex["bundle_id"])
        line("  顯示名稱        : %s" % appex.get("display_name"))
        line("  版本            : %s (%s)" % (appex.get("version"), appex.get("build")))
        line("  擴展點          : %s" % appex.get("extension_point"))
        line("  簽章 App ID     : %s" % (appex.get("application_identifier") or "（無）"))
        line("  App Group      : %s" % (", ".join(appex.get("application_groups") or []) or "（無）"))
        line("  App Intents    : %s" % (", ".join(appex.get("intents") or []) or "（無）"))

        exe_macho = appex.get("macho") or {}
        ext_sdk = exe_macho.get("sdk") or ""
        ext_sdk_major = int(ext_sdk.split(".")[0]) if ext_sdk and ext_sdk[0].isdigit() else 0
        line("  SDK            : %s / %s" % (exe_macho.get("platform_name"), ext_sdk))
        line()

        line("-- 1. 有沒有被安裝 --")
        check(appex["executable_exists"], "執行檔存在", appex.get("executable"))
        check(appex["has_pkg_info"] and (appex.get("pkg_info_content") or "").startswith("XPC"),
              "PkgInfo 存在且為 XPC!", "內容=%r" % appex.get("pkg_info_content"))

        line("-- 2. 簽章有沒有涵蓋擴展自己 --")
        check_provisioning(appex)
        check(bool(appex.get("application_groups")),
              "擴展簽章含 App Group 授權（側載工具才不會跳過指派）",
              ", ".join(appex.get("application_groups") or []) or "（無）")

        line("-- 3. 產物完整度 --")
        check(appex["has_actions_data"], "Metadata.appintents/extract.actionsdata 存在",
              "（iOS 26 列舉擴展能力時會讀取）")
        check(appex["has_version_json"], "Metadata.appintents/version.json 存在")
        check(appex["has_assets"], "Assets.car 存在")
        check(appex.get("package_type") == "XPC!", "CFBundlePackageType = XPC!",
              str(appex.get("package_type")))
        check(appex.get("extension_point") == "com.apple.widgetkit-extension",
              "擴展點是 com.apple.widgetkit-extension")
        check(not appex.get("has_ex_attributes"),
              "沒有多餘的 EXAppExtensionAttributes（那是 ExtensionKit 用的）")
        check(not appex.get("has_principal_class"), "沒有 NSExtensionPrincipalClass")

        line("-- 4. 二進位 --")
        check(exe_macho.get("is_executable") is True, "是執行檔（MH_EXECUTE）")
        check(exe_macho.get("has_lc_main") is True, "具有 LC_MAIN 入口點")
        check(exe_macho.get("platform_name") == "iOS", "platform = iOS",
              str(exe_macho.get("platform_name")))
        check(ext_sdk_major >= 26, "以 iOS 26 以上 SDK 建置", "sdk=%s" % ext_sdk)
        check(any("WidgetKit" in d for d in appex.get("dylibs") or []), "連結 WidgetKit")
        check(any("AppIntents" in d for d in appex.get("dylibs") or []),
              "連結 AppIntents", "（Xcode 的 widget target 會自動連結）")
        line()

    line("=" * 68)
    if problems:
        line("結論：有 %d 項不合格" % len(problems))
        for item in problems:
            line("  - %s" % item)
    else:
        line("結論：擴展本身全部通過。")
        line("若小工具仍未出現在小工具庫，請依序確認：")
        line("  1. 安裝時選的是「Register App ID for Each Extension」")
        line("  2. 已刪除 App 後重新安裝（不是按更新）")
        line("  3. 安裝後開啟過 App 至少一次")
        line("  4. 換一次系統語言或重開機，強制重建小工具索引")
        line("  5. 其他側載 App 的小工具看得到嗎？（看不到 = 平台層級限制）")
    line("=" * 68)
    return "\n".join(lines), not problems


# ---------------------------------------------------------------- 進入點

def locate_app(path: str) -> str:
    if path.lower().endswith(".app"):
        return path

    if path.lower().endswith(".ipa") or zipfile.is_zipfile(path):
        temp_dir = tempfile.mkdtemp(prefix="inspect-ipa-")
        with zipfile.ZipFile(path) as archive:
            archive.extractall(temp_dir)
        payload = os.path.join(temp_dir, "Payload")
        if os.path.isdir(payload):
            for name in sorted(os.listdir(payload)):
                if name.lower().endswith(".app"):
                    return os.path.join(payload, name)
        raise SystemExit("在 IPA 的 Payload/ 裡找不到 .app")

    raise SystemExit("請傳入 .ipa 或 .app 路徑")


def main() -> int:
    parser = argparse.ArgumentParser(description="體檢 iOS IPA 裡的 WidgetKit 擴展")
    parser.add_argument("path", help=".ipa 或 .app 路徑")
    parser.add_argument("--json", action="store_true", help="輸出 JSON（機器可讀）")
    args = parser.parse_args()

    if not os.path.exists(args.path):
        raise SystemExit("找不到檔案：%s" % args.path)

    app = probe_app(locate_app(args.path))

    if args.json:
        print(json.dumps(app, ensure_ascii=False, indent=2, default=str))
        return 0

    text, ok = report(app)
    print(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
