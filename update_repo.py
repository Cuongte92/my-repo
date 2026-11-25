import urllib.request
import json
import os
import sys
import re

TARGET_APPS = [
    {
        "target_repo": "Apollo-Reborn/Apollo-Reborn",
        "bundle_id": "com.christianselig.Apollo"
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

def fetch_latest_ipa_release(repo):
    # Lấy danh sách 20 release gần nhất (bao gồm cả Pre-release)
    url = f"https://api.github.com/repos/{repo}/releases?per_page=20"
    headers = {'User-Agent': 'ESign-Update-Bot'}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers['Authorization'] = f'Bearer {token}'

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        releases = json.loads(response.read().decode())

    # Duyệt từ bản mới nhất xuống, tìm bản đầu tiên có đính kèm file .ipa hoặc .tipa
    for release in releases:
        for asset in release.get("assets", []):
            name = asset.get("name", "").lower()
            if name.endswith(".ipa") or name.endswith(".tipa"):
                return release, asset

    return None, None

def clean_version(tag_name):
    # Xử lý riêng tag dạng 'discord-357.0_124781-ios-testflight' của Unbound -> '357.0'
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

        print(f"\n--- Đang kiểm tra repo: {repo_name} ---")
        try:
            release, ipa_asset = fetch_latest_ipa_release(repo_name)
        except Exception as e:
            print(f"Bỏ qua {repo_name} do lỗi lấy release: {e}")
            continue

        if not release or not ipa_asset:
            print(f"Cảnh báo: Không tìm thấy bản release nào có file .ipa/.tipa trong {repo_name}.")
            continue

        raw_tag = release.get("tag_name", "")
        version = clean_version(raw_tag)
        pub_date = release.get("published_at", "").split("T")[0]
        ipa_url = ipa_asset.get("browser_download_url")
        size = ipa_asset.get("size", 0)

        print(f"Tìm thấy: {ipa_asset.get('name')} | Tag: {raw_tag} -> Version: {version}")

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
