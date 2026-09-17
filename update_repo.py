import urllib.request
import json
import os
import sys

TARGET_APPS = [
    {
        "target_repo": "Apollo-Reborn/Apollo-Reborn",
        "bundle_id": "com.christianselig.Apollo"
    },
    {
        "target_repo": "unbound-app/loader-ios",
        "bundle_id": "com.hammerandchisel.discord"
    },
    {
        "target_repo": "arichornlover/TrollStore-DEBs",
        "bundle_id": "com.burbn.instagram"
    }
]


JSON_FILE = "apps.json"

def fetch_latest_release(repo):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    headers = {'User-Agent': 'ESign-Update-Bot'}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers['Authorization'] = f'Bearer {token}'

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

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
            release = fetch_latest_release(repo_name)
        except Exception as e:
            print(f"Bỏ qua {repo_name} do không lấy được release: {e}")
            continue

        version = release.get("tag_name", "").lstrip("v")
        pub_date = release.get("published_at", "").split("T")[0]

        ipa_url = ""
        size = 0
        for asset in release.get("assets", []):
            if asset.get("name", "").endswith(".ipa"):
                ipa_url = asset.get("browser_download_url")
                size = asset.get("size", 0)
                break

        if not ipa_url:
            print(f"Cảnh báo: Bản release mới nhất của {repo_name} không có file .ipa. Bỏ qua.")
            continue

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
