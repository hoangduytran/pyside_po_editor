# 1) Remove any previous build/dist folders
rm -rf build/ dist/

# 2) (Optional) Clean up any Python‐generated cache
find . -name "__pycache__" -type d -exec rm -rf {} +

# 3) Re‑build your .app bundle
python3 setup.py py2app

