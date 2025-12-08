import tkinter as tk
import platform
from gui import GraphGUI

# =======================================================================================
# CẤU HÌNH ĐỘ NÉT CAO (HIGH-DPI)
# =======================================================================================
if platform.system() == "Windows":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception as e:
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = GraphGUI(root)
    root.mainloop()