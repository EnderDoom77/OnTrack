import json
import time
import requests
import zipfile
import os

def build_repo_path(file):
    return f"https://raw.githubusercontent.com/EnderDoom77/OnTrack/master/{file}"

def die():
    print("Exiting automatically in 5 seconds...")
    time.sleep(5)
    exit()

print("Downloading version data...")

github_version_data_path = build_repo_path("VERSION_DATA.json")
try:
    version_data = requests.get(github_version_data_path).json()
except:
    print(f"Error fetching version data from {github_version_data_path}")
    die()

print("Received version data. Checking for latest version...")

if not "latest_stable" in version_data:
    print(f"Invalid version data, no latest stable version data")
    die()

target_version = version_data["latest_stable"]

print(f"Latest version is {target_version}. Downloading...")

github_target_file_path = f"raw.githubusercontent.com/EnderDoom77/OnTrack/master/dist/versions/ontrack_v{target_version}.zip"
try:
    target_zip = requests.get(f"https://{github_target_file_path}")
except:
    print(f"Error fetching build from {github_target_file_path}")
    die()

print(f"Downloaded build for version {target_version}. Clearing old files...")

try:
    for f in os.listdir():
        if f.startswith("ontrack") and (f.endswith(".zip") or f.endswith(".exe")):
            os.remove(f)
except Exception as e:
    print(f"Error clearing old files: {e}")
    die()

print("Cleared old files. Saving new build...")

try:
    with open(f"ontrack_v{target_version}.zip", "wb") as f:
        f.write(target_zip.content)
except:
    print(f"Error saving build for version {target_version}")
    die()

print(f"Saved build for version {target_version}. Unzipping...")

try:
    with zipfile.ZipFile(f"ontrack_v{target_version}.zip", "r") as z:
        z.extractall() # extract to current directory
except Exception as e:
    print(f"Error unzipping build for version {target_version}: {e}")
    die()

print("Clearing downloaded zip file...")
os.remove(f"ontrack_v{target_version}.zip")

print(f"Update to version {target_version} complete!")