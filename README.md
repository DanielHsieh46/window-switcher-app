# Window Switcher HUD

A lightweight PyQt6 utility for Windows that lets you pin, view, and instantly switch between open windows through a floating heads-up display (HUD). The panel can be collapsed into a small draggable icon, keeping your workspace neat while allowing quick access to your pinned windows.

---

## Features
- Pin and manage frequently used windows
- One-click activation to bring any window to the front
- Collapsible floating icon for minimal desktop footprint
- Automatic refresh of window titles in real time
- Modern minimalist interface built with PyQt6

---

## Folder Structure
```
window-switcher-app/
│
├── window-switcher-app.py     # Main Python script
├── switcher-icon.ico          # Application icon
└── requirements.txt           # Dependency list
```

---

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/<your-username>/window-switcher-app.git
   cd window-switcher-app
   ```

2. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate      # for Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

Run the app:
```bash
python window-switcher-app.py
```

### Controls
- Add Window: Select an open window to pin to the HUD
- Refresh: Reload the current list of available windows
- Collapse: Minimize the HUD to a small draggable circle
- Right-click a pinned window: Unpin it

---

## Interface Preview
(You can add a screenshot or GIF here once available)

---

## Tech Stack
- Python 3.10+
- PyQt6 6.9.1
- pywin32 308

---

## Author
Daniel Hsieh  
Built for productivity, combining modern PyQt6 UI with Win32 window control.

