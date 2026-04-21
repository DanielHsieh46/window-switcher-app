import sys, ctypes
from pathlib import Path
import win32gui, win32con
from PyQt6 import QtWidgets, QtCore, QtGui


try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("WindowSwitcher.App")
except Exception:
    pass


def icon_path(name="switcher-icon.ico") -> Path:
    try:
        return (Path(__file__).resolve().parent / name)
    except NameError:
        return (Path.cwd() / name)


def list_windows():
    results = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            results.append((hwnd, win32gui.GetWindowText(hwnd)))
        return True

    win32gui.EnumWindows(callback, None)
    return results


def activate_window(hwnd):
    try:
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass


def hide_from_alt_tab(widget):
    hwnd = int(widget.winId())

    GWL_EXSTYLE = -20
    WS_EX_TOOLWINDOW = 0x00000080
    WS_EX_APPWINDOW = 0x00040000

    ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    ex_style = ex_style | WS_EX_TOOLWINDOW
    ex_style = ex_style & ~WS_EX_APPWINDOW
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)

    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    SWP_NOZORDER = 0x0004
    SWP_FRAMECHANGED = 0x0020

    ctypes.windll.user32.SetWindowPos(
        hwnd, 0, 0, 0, 0, 0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
    )


class CollapsedIcon(QtWidgets.QPushButton):
    expanded = QtCore.pyqtSignal()

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


class WindowHUD(QtWidgets.QWidget):
    def __init__(self, icon=None):
        super().__init__()
        self.setWindowTitle("Window Switcher HUD")
        self.setWindowFlags(
            QtCore.Qt.WindowType.Tool |
            QtCore.Qt.WindowType.WindowStaysOnTopHint
        )

        if icon is not None:
            self.setWindowIcon(icon)

        self.setMinimumWidth(200)
        self.setMaximumWidth(8000)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Preferred
        )

        self.pinned = {}
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

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

        self.add_window_btn.clicked.connect(self.select_window_to_pin)
        self.refresh_btn.clicked.connect(self.refresh_window_list)
        self.collapse_btn.clicked.connect(self.collapse)

        self.collapsed_icon = CollapsedIcon()
        self.collapsed_icon.expanded.connect(self.expand_back)
        self.available_windows = list_windows()

    def collapse(self):
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        icon_x = screen.width() - self.collapsed_icon.width() - 5
        icon_y = 30
        self.hide()
        self.collapsed_icon.move(icon_x, icon_y)
        self.collapsed_icon.show()
        hide_from_alt_tab(self.collapsed_icon)

    def expand_back(self):
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        hud_x = screen.width() - self.width() - 5
        hud_y = 30
        self.collapsed_icon.hide()
        self.move(hud_x, hud_y)
        self.show()
        hide_from_alt_tab(self)

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


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    ico_file = icon_path("switcher-icon.ico")
    icon = QtGui.QIcon(str(ico_file))

    app.setWindowIcon(icon)
    hud = WindowHUD(icon)
    hud.show()

    hide_from_alt_tab(hud)
    hide_from_alt_tab(hud.collapsed_icon)

    timer = QtCore.QTimer()
    timer.timeout.connect(hud.refresh_titles)
    timer.start(1000)

    sys.exit(app.exec())