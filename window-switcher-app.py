#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import sys, ctypes
from pathlib import Path
import win32gui, win32con
from PyQt6 import QtWidgets, QtCore, QtGui


# ---------- 設定應用程式 AppID（讓 Windows 正確顯示自訂圖示） ----------
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("WindowSwitcher.App")
except Exception:
    pass


# ---------- 工具函式：取得圖示絕對路徑 ----------
def icon_path(name="switcher-icon.ico") -> Path:
    try:
        # 若為執行 .py 檔案
        return (Path(__file__).resolve().parent / name)
    except NameError:
        # 若在 Jupyter 或互動環境中執行，改用目前工作資料夾
        return (Path.cwd() / name)


# ---------- 取得目前可見視窗 ----------
def list_windows():
    results = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            results.append((hwnd, win32gui.GetWindowText(hwnd)))
        return True

    win32gui.EnumWindows(callback, None)
    return results


# ---------- 將指定視窗叫到前面 ----------
def activate_window(hwnd):
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass


# ---------- 收合狀態的圓形按鈕 ----------
class CollapsedIcon(QtWidgets.QPushButton):
    expanded = QtCore.pyqtSignal()  # 點擊後會觸發展開訊號

    def __init__(self):
        super().__init__("●")
        self.setFixedSize(40, 40)
        self.setStyleSheet("""
            QPushButton {
                background-color: #4b8cff;
                color: white;
                border-radius: 20px;
                border: none;
                font-size: 18px;
            }
        """)
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.Tool |
            QtCore.Qt.WindowType.WindowStaysOnTopHint
        )
        self.dragging = False
        self.start_pos = None

    def mousePressEvent(self, e):
        if e.button() == QtCore.Qt.MouseButton.LeftButton:
            self.start_pos = e.globalPosition().toPoint()
            self.offset = e.globalPosition().toPoint() - self.pos()
            self.dragging = False

    def mouseMoveEvent(self, e):
        if self.start_pos is None:
            return
        if (e.globalPosition().toPoint() - self.start_pos).manhattanLength() > 4:
            self.dragging = True
        if self.dragging:
            self.move(e.globalPosition().toPoint() - self.offset)

    def mouseReleaseEvent(self, e):
        if not self.dragging:
            self.expanded.emit()
        self.dragging = False
        self.start_pos = None


# ---------- 主視窗 ----------
class WindowHUD(QtWidgets.QWidget):
    def __init__(self, icon=None):
        super().__init__()
        self.setWindowTitle("Window Switcher HUD")
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint)

        if icon is not None:
            self.setWindowIcon(icon)

        # 可水平調整大小
        self.setMinimumWidth(200)
        self.setMaximumWidth(8000)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Preferred
        )

        self.pinned = {}  # 儲存已釘選的視窗
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # ---------- 上方功能列 ----------
        top_bar = QtWidgets.QHBoxLayout()
        self.add_window_btn = QtWidgets.QPushButton("+")
        self.refresh_btn = QtWidgets.QPushButton("⟳")
        self.collapse_btn = QtWidgets.QPushButton("⇱")

        for btn in (self.add_window_btn, self.refresh_btn, self.collapse_btn):
            btn.setFixedSize(30, 30)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    border: none;
                    background: #f0f0f0;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background: #e0e0e0;
                }
            """)

        top_bar.addWidget(self.add_window_btn)
        top_bar.addWidget(self.refresh_btn)
        top_bar.addStretch()
        top_bar.addWidget(self.collapse_btn)
        self.layout.addLayout(top_bar)
        self.layout.addSpacing(5)

        # 功能連結
        self.add_window_btn.clicked.connect(self.select_window_to_pin)
        self.refresh_btn.clicked.connect(self.refresh_window_list)
        self.collapse_btn.clicked.connect(self.collapse)

        self.collapsed_icon = CollapsedIcon()
        self.collapsed_icon.expanded.connect(self.expand_back)
        self.available_windows = list_windows()

    # ---------- 收合與展開 ----------
    def collapse(self):
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        icon_x = screen.width() - self.collapsed_icon.width() - 5
        icon_y = 30
        self.hide()
        self.collapsed_icon.move(icon_x, icon_y)
        self.collapsed_icon.show()

    def expand_back(self):
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        hud_x = screen.width() - self.width() - 5
        hud_y = 30
        self.collapsed_icon.hide()
        self.move(hud_x, hud_y)
        self.show()

    # ---------- 視窗清單 ----------
    def refresh_window_list(self):
        self.available_windows = list_windows()
        QtWidgets.QMessageBox.information(self, "", "視窗清單已更新 ✓")

    def select_window_to_pin(self):
        self.available_windows = list_windows()
        items = [title for hwnd, title in self.available_windows]
        item, ok = QtWidgets.QInputDialog.getItem(self, "", "選擇視窗：", items, 0, False)
        if ok and item:
            for hwnd, title in self.available_windows:
                if title == item:
                    self.pin_window(hwnd, title)
                    break

    def pin_window(self, hwnd, title):
        if hwnd in self.pinned:
            return
        btn = QtWidgets.QPushButton(title)
        btn.clicked.connect(lambda _, h=hwnd: activate_window(h))
        btn.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        btn.customContextMenuRequested.connect(lambda _, b=btn, h=hwnd: self.remove_pin(h, b))
        self.layout.insertWidget(self.layout.count() - 1, btn)
        self.pinned[hwnd] = btn

    def remove_pin(self, hwnd, btn):
        btn.deleteLater()
        self.pinned.pop(hwnd, None)

    def refresh_titles(self):
        for hwnd, btn in list(self.pinned.items()):
            if not win32gui.IsWindow(hwnd):
                btn.setText("(closed)")
            else:
                btn.setText(win32gui.GetWindowText(hwnd))


# ---------- 主程式 ----------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    ico_file = icon_path("switcher-icon.ico")
    icon = QtGui.QIcon(str(ico_file))

    app.setWindowIcon(icon)
    hud = WindowHUD(icon)
    hud.show()

    timer = QtCore.QTimer()
    timer.timeout.connect(hud.refresh_titles)
    timer.start(1000)

    sys.exit(app.exec())


# In[ ]:




