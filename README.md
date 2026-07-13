# Florida Hurricane Landfall Analyser (1900 - 2025)

A professional data engineering web application built to ingest, parse, and analyze the NOAA Best Track Data (HURDAT2). This system compares two distinct engineering paradigms to isolate hurricanes making physical landfall in Florida since 1900: **Metadata String Parsing** vs. **Vectorized Point-in-Polygon Spatial Analytics**.

## 🚀 Quick Start

Ensure you are operating within the root directory.

### 1. Set Up Environment & Install Dependencies
```bash
# Create an isolated virtual environment
python3 -m venv venv

# Activate the environment
source venv/bin/activate

# Install required parsing, web, spatial, and mapping packages
./venv/bin/pip install -r requirements.txt

# Run the application

./venv/bin/python app.py
```
## Once running, open your browser and navigate to: http://127.0.0.1:5000