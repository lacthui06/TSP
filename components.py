import tkinter as tk
from tkinter import ttk

# =======================================================================================
# CUSTOM POPUP (THÔNG BÁO)
# =======================================================================================
class CustomPopup(tk.Toplevel):
    def __init__(self, parent, title, message, is_error=False):
        super().__init__(parent)
        self.title(title)
        self.configure(bg="white")
        self.withdraw()
        self.update_idletasks()
        
        msg_font = ("Segoe UI", 16) 
        btn_font = ("Segoe UI", 14, "bold")
        text_color = "#c0392b" if is_error else "#2c3e50"

        lbl = tk.Label(self, text=message, font=msg_font, bg="white", fg=text_color, wraplength=500, justify="left")
        lbl.pack(pady=30, padx=30)

        btn = tk.Button(self, text="Đã Hiểu", font=btn_font, command=self.destroy, 
                        bg="#3498db", fg="white", relief="flat", padx=25, pady=8, cursor="hand2")
        btn.pack(pady=(0, 20))

        w = self.winfo_reqwidth() + 80
        h = self.winfo_reqheight() + 80
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"+{x}+{y}")
        self.deiconify()
        self.transient(parent)
        self.grab_set()
        self.wait_window(self)

# =======================================================================================
# ALGORITHM SELECTOR DIALOG (CHỌN THUẬT TOÁN THEO NHÓM) - FIXED SIZE
# =======================================================================================
class AlgorithmSelectorDialog(tk.Toplevel):
    def __init__(self, parent, algo_map):
        """
        algo_map: Dictionary dạng { "Tên Nhóm": { "Tên Thuật Toán": function_callback } }
        """
        super().__init__(parent)
        self.title("Thư Viện Thuật Toán")
        self.configure(bg="white")
        self.algo_map = algo_map
        self.selected_func = None
        
        # --- CẤU HÌNH FONT TO CHO DROPDOWN LIST ---
        self.option_add('*TCombobox*Listbox.font', ("Segoe UI", 16)) 
        
        # --- CHỈNH SỬA KÍCH THƯỚC CỬA SỔ ---
        w, h = 600, 550 
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        # UI Elements
        tk.Label(self, text="Chọn Loại Thuật Toán", font=("Segoe UI", 16, "bold"), bg="white", fg="#7f8c8d").pack(pady=(30, 10))
        
        # Combobox Nhóm (Category)
        self.groups = list(self.algo_map.keys())
        self.cb_group = ttk.Combobox(self, values=self.groups, font=("Segoe UI", 16), state="readonly", width=35)
        self.cb_group.current(0)
        self.cb_group.pack(pady=5, ipady=10) # Tăng chiều cao ô nhập
        self.cb_group.bind("<<ComboboxSelected>>", self.on_group_change)

        # Label 2
        tk.Label(self, text="Chọn Thuật Toán Cụ Thể", font=("Segoe UI", 16, "bold"), bg="white", fg="#2c3e50").pack(pady=(30, 10))

        # Combobox Thuật toán (Specific Algorithm)
        self.cb_algo = ttk.Combobox(self, font=("Segoe UI", 16), state="readonly", width=35)
        self.cb_algo.pack(pady=5, ipady=10) # Tăng chiều cao ô nhập
        
        # Init list thuật toán lần đầu
        self.on_group_change(None)

        # Buttons Frame
        f_btn = tk.Frame(self, bg="white")
        f_btn.pack(pady=40, fill=tk.X) 
        
        # Center buttons
        f_inner = tk.Frame(f_btn, bg="white")
        f_inner.pack()

        # --- NÚT BẤM TO (PADX=40) ---
        tk.Button(f_inner, text="Chạy Thuật Toán", command=self.ok, bg="#2980b9", fg="white", 
                  font=("Segoe UI", 14, "bold"), padx=40, pady=10, relief="flat", cursor="hand2").pack(side=tk.LEFT, padx=20)
        
        tk.Button(f_inner, text="Hủy", command=self.destroy, bg="#95a5a6", fg="white", 
                  font=("Segoe UI", 14, "bold"), padx=40, pady=10, relief="flat", cursor="hand2").pack(side=tk.LEFT, padx=20)

        self.transient(parent)
        self.grab_set()
        self.wait_window(self)

    def on_group_change(self, event):
        group = self.cb_group.get()
        algos = list(self.algo_map[group].keys())
        self.cb_algo['values'] = algos
        if algos: self.cb_algo.current(0)

    def ok(self):
        group = self.cb_group.get()
        algo_name = self.cb_algo.get()
        if group and algo_name:
            self.selected_func = self.algo_map[group][algo_name]
            self.destroy()

# =======================================================================================
# COMBOBOX SELECTION DIALOG (DÙNG CHO BFS/DFS/CHỌN NODE)
# =======================================================================================
class ComboSelectionDialog(tk.Toplevel):
    def __init__(self, parent, title, prompt, choices, extra_option=None):
        super().__init__(parent)
        self.title(title)
        self.configure(bg="white")
        self.result = None
        self.extra_val = False
        
        # Tăng kích thước một chút cho thoáng
        w, h = 500, 400
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        # Thêm option_add cho font listbox to
        self.option_add('*TCombobox*Listbox.font', ("Segoe UI", 16))

        tk.Label(self, text=prompt, font=("Segoe UI", 16, "bold"), bg="white", fg="#2c3e50").pack(pady=(25, 10))
        
        self.cb = ttk.Combobox(self, values=choices, font=("Segoe UI", 16), state="readonly", width=15)
        if choices: self.cb.current(0) 
        self.cb.pack(pady=10, ipady=8)
        
        self.chk_var = tk.BooleanVar(value=False)
        if extra_option:
            chk = tk.Checkbutton(self, text=extra_option, variable=self.chk_var, bg="white", 
                                 font=("Segoe UI", 14), fg="#e67e22", cursor="hand2")
            chk.pack(pady=10)

        self.cb.focus()
        f_btn = tk.Frame(self, bg="white")
        f_btn.pack(pady=40) # Tăng khoảng cách nút

        # --- NÚT BẤM TO (PADX=40) ---
        tk.Button(f_btn, text="Xác Nhận", command=self.ok, bg="#27ae60", fg="white", 
                  font=("Segoe UI", 14, "bold"), padx=40, pady=10, relief="flat", cursor="hand2").pack(side=tk.LEFT, padx=15)
        tk.Button(f_btn, text="Hủy", command=self.destroy, bg="#e74c3c", fg="white", 
                  font=("Segoe UI", 14, "bold"), padx=40, pady=10, relief="flat", cursor="hand2").pack(side=tk.LEFT, padx=15)
        
        self.bind('<Return>', self.ok)
        self.transient(parent); self.grab_set(); self.wait_window(self)

    def ok(self, event=None):
        val = self.cb.get()
        if val:
            self.result = val
            self.extra_val = self.chk_var.get()
            self.destroy()

# =======================================================================================
# ROUNDED BUTTON
# =======================================================================================
class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, width=200, height=50, corner_radius=25, bg_color="#3498db", fg_color="white", hover_color="#2980b9"):
        super().__init__(parent, borderwidth=0, relief="flat", highlightthickness=0, bg=parent["bg"])
        self.command = command
        self.bg_color = bg_color; self.hover_color = hover_color; self.fg_color = fg_color
        self.text_str = text; self.width = width; self.height = height; self.corner = corner_radius
        self.config(width=width, height=height)
        self.draw_button(self.bg_color)
        self.bind("<Button-1>", self.on_click); self.bind("<Enter>", self.on_enter); self.bind("<Leave>", self.on_leave)

    def draw_button(self, color):
        self.delete("all"); r, w, h = self.corner, self.width, self.height
        self.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=color, outline=color)
        self.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=color, outline=color)
        self.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=color, outline=color)
        self.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=color, outline=color)
        self.create_rectangle(r, 0, w-r, h, fill=color, outline=color)
        self.create_rectangle(0, r, w, h-r, fill=color, outline=color)
        self.create_text(w/2, h/2, text=self.text_str, fill=self.fg_color, font=("Segoe UI", 14, "bold"))

    def on_click(self, event):
        if self.command: self.command()
    def on_enter(self, event): self.draw_button(self.hover_color); self.config(cursor="hand2")
    def on_leave(self, event): self.draw_button(self.bg_color)

# =======================================================================================
# EDGE INPUT DIALOG - DEFAULT UNCHECKED (VÔ HƯỚNG) & BIG BUTTONS
# =======================================================================================
class EdgeDialog(tk.Toplevel):
    def __init__(self, parent, u, v):
        super().__init__(parent)
        self.title("Thêm Cạnh")
        # Tăng chiều cao lên 450 để chứa nút to
        self.geometry("550x450")
        self.configure(bg="white")
        self.result = None
        
        main_font = ("Segoe UI", 16)
        header_font = ("Segoe UI", 20, "bold")
        btn_font = ("Segoe UI", 14, "bold")
        
        tk.Label(self, text=f"Kết nối: {u}  ➜  {v}", font=header_font, bg="white", fg="#2c3e50").pack(pady=30)
        
        f1 = tk.Frame(self, bg="white")
        f1.pack(pady=20)
        
        tk.Label(f1, text="Trọng số:", bg="white", font=main_font).pack(side=tk.LEFT)
        self.ew = tk.Entry(f1, width=10, font=("Segoe UI", 18, "bold"), bd=2, relief="groove", justify='center')
        self.ew.insert(0, "1")
        self.ew.pack(side=tk.LEFT, padx=15, ipady=5)
        self.ew.focus()
        
        # Mặc định KHÔNG hướng
        self.vd = tk.BooleanVar(value=False) 
        
        tk.Checkbutton(self, text="Có hướng (Mũi tên)", variable=self.vd, bg="white", 
                       font=main_font, fg="#e67e22", cursor="hand2").pack(pady=20)
        
        f_btn = tk.Frame(self, bg="white")
        f_btn.pack(pady=40) # Tăng khoảng cách
        
        # --- NÚT BẤM TO (PADX=40) ---
        tk.Button(f_btn, text="Xác Nhận", command=self.ok, bg="#27ae60", fg="white", 
                  font=btn_font, padx=40, pady=10, bd=0, relief="flat", cursor="hand2").pack(side=tk.LEFT, padx=15)
        
        tk.Button(f_btn, text="Hủy Bỏ", command=self.destroy, bg="#e74c3c", fg="white", 
                  font=btn_font, padx=40, pady=10, bd=0, relief="flat", cursor="hand2").pack(side=tk.LEFT, padx=15)
        
        self.bind('<Return>', self.ok) 
        self.transient(parent)
        self.grab_set()
        self.wait_window(self)

    def ok(self, event=None):
        try: 
            w = float(self.ew.get()) 
            self.result = (w, self.vd.get())
            self.destroy()
        except ValueError: 
            CustomPopup(self, "Lỗi Nhập Liệu", "Vui lòng nhập số thực hợp lệ!", is_error=True)