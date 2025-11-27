import urllib.request
import zipfile
import os

url = "https://github.com/lichess-org/chessboard-image-detector/archive/refs/heads/master.zip"
zip_path = "lichess-detector.zip"
extract_path = "."

print(f"Downloading {url}...")
urllib.request.urlretrieve(url, zip_path)
print("Download complete.")

print(f"Extracting to {extract_path}...")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_path)
print("Extraction complete.")

# Rename the directory
extracted_dir = "chessboard-image-detector-master"
target_dir = "lichess-detector"
if os.path.exists(extracted_dir):
    if os.path.exists(target_dir):
        print(f"Removing existing {target_dir}...")
        import shutil
        shutil.rmtree(target_dir)
    os.rename(extracted_dir, target_dir)
    print(f"Renamed {extracted_dir} to {target_dir}")
