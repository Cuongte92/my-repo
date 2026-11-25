import urllib.request
import json
import os
import sys
import re

TARGET_APPS = [
    {
        "target_repo": "Apollo-Reborn/Apollo-Reborn",
        "bundle_id": "com.christianselig.Apollo",
        "prefer_exact": r"^apollo-reborn-[\d.]+\.ipa$"
    },
    {
        "target_repo": "mikevillarroel/buildbox-ios",
        "bundle_id": "com.mikevillarroel.buildbox"
    },
    {
        "target_repo": "marioparaschiv/unbound",
        "bundle_id": "com.hammerandchisel.discord"
    },
    {
        "target_repo": "mxhm11cr/LinuxRunner",
        "bundle_id": "dev.linuxrunner.app.U4VR236UMH"
    }
]

JSON_FILE = "apps.json"

def fetch_latest_ipa_release(repo, prefer_pattern=None):
    url = f"https://api.github.com/repos/{repo}/releases?per_page=20"
    headers = {'User-Agent': 'ESign-Update-Bot'}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers['Authorization'] = f'Bearer {token}'

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        releases = json.loads(response.read().decode())

    for release in releases:
        ipa_assets = [
            a for a in release.get("assets", [])
            if a.get("name", "").lower().endswith((".ipa", ".tipa"))
        ]
        if not ipa_assets:
            continue

        # Nếu có quy tắc ưu tiên tên file (ví dụ bản Apollo chuẩn đầy đủ extension)
        if prefer_pattern:
            for a in ipa_assets:
                if re.match(prefer_pattern, a.get("name", "").lower()):
                    return release, a

        return release, ipa_assets[0]

    return None, None

def clean_version(tag_name):
    match = re.search(r'discord-(\d+\.\d+(?:\.\d+)?)', tag_name)
    if match:
        return match.group(1)
    return tag_name.lstrip("v")

def main():
    if not os.path.exists(JSON_FILE):
        print(f"Không tìm thấy file {JSON_FILE}!")
        sys.exit(1)

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        repo_data = json.load(f)

    any_updated = False

    for target in TARGET_APPS:
        repo_name = target["target_repo"]
        bundle_id = target["bundle_id"]
        prefer_pattern = target.get("prefer_exact")

        print(f"\n--- Đang kiểm tra repo: {repo_name} ---")
        try:
            release, ipa_asset = fetch_latest_ipa_release(repo_name, prefer_pattern)
        except Exception as e:
            print(f"Bỏ qua {repo_name} do lỗi lấy release: {e}")
            continue

        if not release or not ipa_asset:
            print(f"Cảnh báo: Không tìm thấy file .ipa/.tipa trong {repo_name}.")
            continue

        raw_tag = release.get("tag_name", "")
        version = clean_version(raw_tag)
        pub_date = release.get("published_at", "").split("T")[0]
        ipa_url = ipa_asset.get("browser_download_url")
        size = ipa_asset.get("size", 0)

        print(f"Chọn file: {ipa_asset.get('name')} | Version: {version}")

        for app in repo_data.get("apps", []):
            if app.get("bundleIdentifier") == bundle_id:
                if app.get("version") == version and app.get("downloadURL") == ipa_url:
                    print(f"App {bundle_id} đã ở bản mới nhất ({version}).")
                else:
                    app["version"] = version
                    app["versionDate"] = pub_date
                    app["downloadURL"] = ipa_url
                    if size > 0:
                        app["size"] = size
                    any_updated = True
                    print(f"Cập nhật thành công {bundle_id} lên v{version}!")
                break

    if any_updated:
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(repo_data, f, indent=2, ensure_ascii=False)
        print("\nĐã ghi đè dữ liệu mới vào apps.json.")
    else:
        print("\nKhông có thay đổi nào cần cập nhật.")

if __name__ == "__main__":
    main()
