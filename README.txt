AI-Interactive Dashboard (Pro)

Files:
- smart_home_dashboard_pro.py  -> main app (Plotly visuals, targets, presets, upload fallback)
- LT09 smart_home_devices_data.xlsx -> your dataset (keep in same folder or upload in the app)
- .streamlit/config.toml -> theme colors & fonts
- requirements.txt -> dependencies
- run_dashboard.bat (Windows) / run_dashboard.command (macOS) -> one-click launch

Run:
1) Install Python (https://www.python.org/downloads/)
2) In this folder:
   pip install -r requirements.txt
3) Launch:
   Windows: run_dashboard.bat
   macOS : ./run_dashboard.command

Or from terminal:
   streamlit run smart_home_dashboard_pro.py
