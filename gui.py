import tkinter as tk
from tkinter import filedialog, ttk
import math
import json

from model import Graph
from components import RoundedButton, CustomPopup, EdgeDialog, ComboSelectionDialog, AlgorithmSelectorDialog

class GraphGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DSA Graph Master - Optimized (Big Font & Grouped Algo)")
        self.root.geometry("1600x900")
        self.root.configure(bg="#fdfdfd")
        
        self.history = [] 
        self.root.bind("<Control-z>", self.undo)
        self.root.bind("<Control-Z>", self.undo)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", foreground="#333", rowheight=40, font=("Segoe UI", 14))
        style.configure("Treeview.Heading", font=("Segoe UI", 14, "bold"))
        
        self.graph = Graph()
        self.sel_node = None; self.drag_node = None; self.is_drag = False
        
        self.base_r = 40
        self.zoom_scale = 1.0 
        self.offset_x = 0; self.offset_y = 0
        self.last_mouse_x = 0; self.last_mouse_y = 0

        self.setup_ui()

    # ... (Giữ nguyên các hàm to_screen_x, to_world_x cũ) ...
    def to_screen_x(self, world_x): return (world_x + self.offset_x) * self.zoom_scale
    def to_screen_y(self, world_y): return (world_y + self.offset_y) * self.zoom_scale
    def to_world_x(self, screen_x): return (screen_x / self.zoom_scale) - self.offset_x
    def to_world_y(self, screen_y): return (screen_y / self.zoom_scale) - self.offset_y

    def setup_ui(self):
        sb_bg = "#2c3e50"
        # Sidebar rộng 380px
        sb = tk.Frame(self.root, bg=sb_bg, width=380); sb.pack(side=tk.LEFT, fill=tk.Y); sb.pack_propagate(False)
        tk.Label(sb, text="GRAPH", font=("Segoe UI", 36, "bold"), bg=sb_bg, fg="white").pack(pady=30)
        
        def group_lbl(txt): tk.Label(sb, text=txt, bg=sb_bg, fg="#bdc3c7", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=25, pady=(20, 5))

        # NÚT BẤM TO HƠN: Width = 340 (để vừa sidebar 380)
        BTN_W = 340
        BTN_H = 55

        group_lbl("HỆ THỐNG")
        RoundedButton(sb, "Hoàn Tác (Ctrl+Z)", self.undo, bg_color="#e67e22", hover_color="#d35400", width=BTN_W, height=BTN_H).pack(pady=5)
        RoundedButton(sb, "Xóa Tất Cả", self.clear, bg_color="#c0392b", hover_color="#e74c3c", width=BTN_W, height=BTN_H).pack(pady=5)

        group_lbl("DỮ LIỆU")
        RoundedButton(sb, "Lưu File (.json)", self.save, bg_color="#16a085", hover_color="#1abc9c", width=BTN_W, height=BTN_H).pack(pady=5)
        RoundedButton(sb, "Mở File (.json)", self.load, bg_color="#16a085", hover_color="#1abc9c", width=BTN_W, height=BTN_H).pack(pady=5)
        RoundedButton(sb, "Xem Bảng Dữ Liệu", self.show_data, bg_color="#8e44ad", hover_color="#9b59b6", width=BTN_W, height=BTN_H).pack(pady=5)

        group_lbl("THUẬT TOÁN")
        # BFS và DFS vẫn để ngoài cho tiện
        RoundedButton(sb, "BFS (Loang)", self.run_bfs, bg_color="#2980b9", hover_color="#3498db", width=BTN_W, height=BTN_H).pack(pady=5)
        RoundedButton(sb, "DFS (Sâu)", self.run_dfs, bg_color="#2980b9", hover_color="#3498db", width=BTN_W, height=BTN_H).pack(pady=5)
        
        # Nút "Nâng Cao" đổi tên và làm to ra để sửa lỗi ảnh 1
        RoundedButton(sb, "Thư Viện Thuật Toán", self.show_adv_menu, bg_color="#f39c12", hover_color="#f1c40f", width=BTN_W, height=BTN_H).pack(pady=5)

        main = tk.Frame(self.root, bg="#fdfdfd"); main.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        cv_container = tk.Frame(main, bg="#bdc3c7", bd=1, relief="flat"); cv_container.pack(fill=tk.BOTH, expand=True)
        self.cv = tk.Canvas(cv_container, bg="white", highlightthickness=0, cursor="cross"); self.cv.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        self.cv.bind("<Button-1>", self.down)
        self.cv.bind("<B1-Motion>", self.drag)
        self.cv.bind("<ButtonRelease-1>", self.up)
        self.cv.bind("<MouseWheel>", self.zoom_event) 
        self.cv.bind("<Button-4>", self.zoom_event)
        self.cv.bind("<Button-5>", self.zoom_event)
        self.cv.bind("<Button-3>", self.start_pan)
        self.cv.bind("<B3-Motion>", self.motion_pan)
        
        tk.Label(main, text="🖱️ Trái: Tạo/Kéo | Phải: Kéo Màn Hình | Lăn Chuột: Phóng To/Nhỏ | Ctrl+Z: Undo", 
                 bg="#fdfdfd", fg="black", font=("Segoe UI", 14, "bold")).pack(pady=10)

    # --- MENU THUẬT TOÁN MỚI (GOM NHÓM LISTBOX) ---
    def show_adv_menu(self):
        # Cấu trúc: { "Tên Nhóm": { "Tên Thuật Toán": Hàm xử lý } }
        algo_structure = {
            "Tìm Đường Ngắn Nhất": {
                "Dijkstra (Trọng số dương)": self.run_dijkstra,
                "Bellman-Ford (Xử lý âm)": self.run_bellman_ford
            },
            "Cây Khung Nhỏ Nhất (MST)": {
                "Thuật toán Prim": self.run_prim,
                "Thuật toán Kruskal": self.run_kruskal
            },
            "Chu Trình Euler & Hamilton": {
                "Fleury (Euler)": self.run_fleury,
                "Hierholzer (Euler)": self.run_hierholzer,
                "Kiểm tra Hamilton": self.run_hamilton
            },
            "Luồng & Phân Tích Khác": {
                "Luồng Cực Đại (Max Flow)": self.run_maxflow,
                "Kiểm tra Đồ thị 2 Phía": self.run_bi
            }
        }
        
        # Gọi Dialog mới
        d = AlgorithmSelectorDialog(self.root, algo_structure)
        if d.selected_func:
            d.selected_func() # Chạy hàm được chọn

    # --- CÁC HÀM HỖ TRỢ (GIỮ NGUYÊN) ---
    def ask_node(self, title, prompt, extra_opt=None):
        if not self.graph.nodes:
            CustomPopup(self.root, "Thông Báo", "Đồ thị chưa có đỉnh nào!\nHãy tạo đỉnh trước.", is_error=True)
            return None, False
        choices = [str(n.id) for n in self.graph.nodes]
        d = ComboSelectionDialog(self.root, title, prompt, choices, extra_option=extra_opt)
        if d.result is not None: return int(d.result), d.extra_val
        return None, False

    # --- ALGORITHM RUNNERS (LOGIC CŨ VẪN DÙNG TỐT) ---
    def run_bfs(self):
        s, is_desc = self.ask_node("BFS", "Chọn Đỉnh Bắt Đầu:", extra_opt="Ưu tiên LỚN trước (Lớn->Nhỏ)")
        if s is not None:
            p = self.graph.bfs(s, descending=is_desc)
            desc_text = "Lớn -> Nhỏ" if is_desc else "Nhỏ -> Lớn"
            self.hl_path_fill(p); CustomPopup(self.root, "Kết Quả BFS", f"Thứ tự ({desc_text}):\n{p}")

    def run_dfs(self):
        s, is_desc = self.ask_node("DFS", "Chọn Đỉnh Bắt Đầu:", extra_opt="Ưu tiên LỚN trước (Lớn->Nhỏ)")
        if s is not None:
            p = self.graph.dfs(s, descending=is_desc)
            desc_text = "Lớn -> Nhỏ" if is_desc else "Nhỏ -> Lớn"
            self.hl_path_fill(p); CustomPopup(self.root, "Kết Quả DFS", f"Thứ tự ({desc_text}):\n{p}")

    def run_dijkstra(self):
        if any(e.weight < 0 for e in self.graph.edges):
            CustomPopup(self.root, "Lỗi Thuật Toán", "Dijkstra KHÔNG hoạt động với trọng số ÂM!", is_error=True); return
        s, _ = self.ask_node("Dijkstra", "Chọn Điểm Đi (Start):")
        if s is None: return
        e, _ = self.ask_node("Dijkstra", "Chọn Điểm Đến (End):")
        if e is None: return
        p, w = self.graph.dijkstra(s,e)
        if p: self.hl_path_fill(p, "#e74c3c"); CustomPopup(self.root, "Kết Quả", f"Tổng Chi Phí: {w}\nLộ Trình: {p}")
        else: CustomPopup(self.root, "Lỗi", "Không tìm thấy đường đi!", is_error=True)

    def run_bellman_ford(self):
        s, _ = self.ask_node("Bellman-Ford", "Chọn Điểm Đi (Start):")
        if s is None: return
        e, _ = self.ask_node("Bellman-Ford", "Chọn Điểm Đến (End):")
        if e is None: return
        path, cost = self.graph.bellman_ford(s, e)
        if cost == float('-inf'): CustomPopup(self.root, "Cảnh Báo", "Phát hiện CHU TRÌNH ÂM!\nKhông thể tính đường đi ngắn nhất.", is_error=True)
        elif path: self.hl_path_fill(path, "#e74c3c"); CustomPopup(self.root, "Kết Quả", f"Tổng Chi Phí: {cost}\nLộ Trình: {path}")
        else: CustomPopup(self.root, "Lỗi", "Không tìm thấy đường đi!", is_error=True)

    def run_maxflow(self):
        s, _ = self.ask_node("Flow", "Chọn Nguồn (Source):")
        if s is None: return
        t, _ = self.ask_node("Flow", "Chọn Đích (Sink):")
        if t is None: return
        f = self.graph.ford_fulkerson(s,t); CustomPopup(self.root, "Max Flow", f"Luồng Cực Đại: {f}")

    def run_fleury(self):
        # Kiểm tra điều kiện Euler trước
        status, msg, auto_start_node = self.graph.get_euler_status()
        
        if status == 0: 
            CustomPopup(self.root, "Không thể chạy", f"Lý do: {msg}", is_error=True)
            return

        # BƯỚC 1: Thông báo tính chất đồ thị TRƯỚC
        # msg sẽ là "Đồ thị có chu trình Euler" hoặc "Đồ thị có đường đi Euler"
        CustomPopup(self.root, "Kiểm Tra Euler", f"Phát hiện: {msg}\n\nBấm 'Đã Hiểu' để chọn đỉnh (nếu cần) và chạy mô phỏng.")

        # Logic chọn đỉnh bắt đầu (giữ nguyên)
        final_start_node = auto_start_node
        if status == 2: # Chu trình (bắt đầu ở đâu cũng được)
            user_choice, _ = self.ask_node("Fleury", f"Chọn Đỉnh Bắt Đầu:\n(Mặc định: {auto_start_node})")
            if user_choice is not None:
                has_edge = any(e.u==user_choice or e.v==user_choice for e in self.graph.edges)
                if has_edge: final_start_node = user_choice
                else: CustomPopup(self.root, "Lỗi", f"Đỉnh {user_choice} cô lập, dùng mặc định {auto_start_node}", is_error=True)
        
        try:
            # Tính toán đường đi
            p = self.graph.fleury_algo(final_start_node)
            
            # BƯỚC 2: Visualize (Vẽ màu)
            self.hl_path_fill(p, "#f1c40f")
            
            # BƯỚC 3: Hiện kết quả cuối cùng
            CustomPopup(self.root, "Kết Quả Fleury", f"Lộ trình: {p}")
        except Exception as e: 
            CustomPopup(self.root, "Lỗi", str(e), is_error=True)

    def run_hierholzer(self):
        # Kiểm tra điều kiện Euler trước
        status, msg, auto_start_node = self.graph.get_euler_status()
        
        if status == 0: 
            CustomPopup(self.root, "Không thể chạy", f"Lý do: {msg}", is_error=True)
            return

        # BƯỚC 1: Thông báo tính chất đồ thị TRƯỚC
        CustomPopup(self.root, "Kiểm Tra Euler", f"Phát hiện: {msg}\n\nBấm 'Đã Hiểu' để chọn đỉnh (nếu cần) và chạy mô phỏng.")

        # Logic chọn đỉnh bắt đầu (giữ nguyên)
        final_start_node = auto_start_node
        if status == 2:
            user_choice, _ = self.ask_node("Hierholzer", f"Chọn Đỉnh Bắt Đầu:\n(Mặc định: {auto_start_node})")
            if user_choice is not None:
                has_edge = any(e.u==user_choice or e.v==user_choice for e in self.graph.edges)
                if has_edge: final_start_node = user_choice
                else: CustomPopup(self.root, "Lỗi", f"Đỉnh {user_choice} cô lập, dùng mặc định {auto_start_node}", is_error=True)
        
        try:
            # Tính toán đường đi
            p = self.graph.hierholzer_algo(final_start_node)
            
            # BƯỚC 2: Visualize (Vẽ màu)
            self.hl_path_fill(p, "#e67e22")
            
            # BƯỚC 3: Hiện kết quả cuối cùng
            CustomPopup(self.root, "Kết Quả Hierholzer", f"Lộ trình: {p}")
        except Exception as e: 
            CustomPopup(self.root, "Lỗi", str(e), is_error=True)
            
    def run_hamilton(self):
        # 1. Kiểm tra số lượng đỉnh tối thiểu
        if len(self.graph.nodes) < 3: 
            CustomPopup(self.root, "Lỗi", "Đồ thị cần ít nhất 3 đỉnh để xét chu trình Hamilton.", is_error=True)
            return

        # 2. Tìm kiếm chu trình (Mặc định thuật toán sẽ tìm ra 1 chu trình bất kỳ nếu có)
        found, initial_path = self.graph.check_hamilton()
        
        if found:
            # BƯỚC A: Thông báo tìm thấy TRƯỚC
            CustomPopup(self.root, "Thành Công", "Đã tìm thấy Chu trình Hamilton!\nBấm 'Đã Hiểu' để chọn đỉnh xuất phát.")
            
            # BƯỚC B: Hỏi người dùng chọn đỉnh bắt đầu
            # Mặc định lấy đỉnh đầu tiên của chu trình tìm được
            default_start = initial_path[0]
            user_choice, _ = self.ask_node("Hamilton", f"Chọn Đỉnh Bắt Đầu:\n(Chu trình đi qua mọi đỉnh)")

            final_path = initial_path
            
            # BƯỚC C: Xử lý xoay vòng lộ trình theo đỉnh người chọn
            if user_choice is not None:
                # initial_path có dạng [0, 1, 2, 3, 0] (đỉnh cuối lặp lại đỉnh đầu)
                # Ta cần bỏ đỉnh cuối đi để thành danh sách các đỉnh duy nhất: [0, 1, 2, 3]
                unique_nodes = initial_path[:-1]
                
                if user_choice in unique_nodes:
                    idx = unique_nodes.index(user_choice)
                    # Kỹ thuật xoay mảng (List Slicing): Đưa phần sau lên trước
                    # Ví dụ: [0, 1, 2, 3] chọn 2 (idx=2) -> [2, 3] + [0, 1] = [2, 3, 0, 1]
                    rotated = unique_nodes[idx:] + unique_nodes[:idx]
                    # Khép vòng lại (thêm đỉnh đầu vào cuối)
                    rotated.append(user_choice)
                    final_path = rotated
                else:
                    # Trường hợp cực hiếm: người dùng nhập 1 đỉnh không có trong đồ thị (dù đã chọn list)
                    CustomPopup(self.root, "Cảnh báo", "Đỉnh chọn không hợp lệ, dùng lộ trình mặc định.", is_error=True)

            # BƯỚC D: Chạy Visualize
            self.hl_path_fill(final_path, "#e84393")
            
            # BƯỚC E: Hiện kết quả chi tiết
            CustomPopup(self.root, "Kết Quả Chi Tiết", f"Thứ tự đi từ {final_path[0]}:\n{final_path}")
        else:
            CustomPopup(self.root, "Thất Bại", "Không tồn tại chu trình Hamilton trong đồ thị này.", is_error=True)

    def run_prim(self): 
        if any(e.is_directed for e in self.graph.edges): CustomPopup(self.root, "Lỗi Thuật Toán", "MST (Prim) chỉ áp dụng cho đồ thị VÔ HƯỚNG!", is_error=True); return
        e,w=self.graph.prim(); self.hl_edge(e, "#3498db"); CustomPopup(self.root, "Prim MST", f"Tổng Trọng Số: {w}")

    def run_kruskal(self):
        if any(e.is_directed for e in self.graph.edges): CustomPopup(self.root, "Lỗi Thuật Toán", "MST (Kruskal) chỉ áp dụng cho đồ thị VÔ HƯỚNG!", is_error=True); return
        e,w=self.graph.kruskal(); self.hl_edge(e, "#9b59b6"); CustomPopup(self.root, "Kruskal MST", f"Tổng Trọng Số: {w}")

    def run_bi(self):
        r,c=self.graph.check_bipartite()
        if r: 
            self.draw(); 
            for nid,v in c.items():
                n=self.graph.nodes[nid]; col="#e74c3c" if v else "#3498db"
                sx, sy = int(self.to_screen_x(n.x)), int(self.to_screen_y(n.y))
                current_r = self.base_r * self.zoom_scale
                self.cv.create_oval(sx-current_r+5,sy-current_r+5,sx+current_r-5,sy+current_r-5,fill=col) 
                self.cv.create_text(sx,sy,text=str(n.id),font=("Segoe UI",int(16*self.zoom_scale),"bold"), fill="white")
            CustomPopup(self.root, "Kết Quả", "Là Đồ Thị 2 Phía")
        else: CustomPopup(self.root, "Kết Quả", "KHÔNG Phải Đồ Thị 2 Phía", is_error=True)

    # --- SAVE/LOAD/UNDO/ZOOM (GIỮ NGUYÊN) ---
    def save_state(self):
        state = self.graph.to_dict(); self.history.append(state)
        if len(self.history) > 20: self.history.pop(0)

    def undo(self, event=None):
        if not self.history: CustomPopup(self.root, "Thông báo", "Không còn thao tác nào để quay lại!"); return
        last_state = self.history.pop(); self.graph.from_dict(last_state); self.sel_node = None; self.draw()

    def zoom_event(self, event):
        if event.num == 5 or event.delta < 0: scale_factor = 0.9 
        else: scale_factor = 1.1 
        new_zoom = self.zoom_scale * scale_factor
        if new_zoom < 0.2 or new_zoom > 5.0: return
        mouse_x = self.cv.canvasx(event.x); mouse_y = self.cv.canvasy(event.y)
        world_x = (mouse_x / self.zoom_scale) - self.offset_x
        world_y = (mouse_y / self.zoom_scale) - self.offset_y
        self.zoom_scale = new_zoom
        self.offset_x = (mouse_x / self.zoom_scale) - world_x
        self.offset_y = (mouse_y / self.zoom_scale) - world_y
        self.draw()

    def start_pan(self, event): self.last_mouse_x = event.x; self.last_mouse_y = event.y
    def motion_pan(self, event):
        dx = event.x - self.last_mouse_x; dy = event.y - self.last_mouse_y
        self.offset_x += dx / self.zoom_scale; self.offset_y += dy / self.zoom_scale
        self.last_mouse_x = event.x; self.last_mouse_y = event.y; self.draw()

    def down(self, e):
        wx = self.to_world_x(self.cv.canvasx(e.x)); wy = self.to_world_y(self.cv.canvasy(e.y))
        nid = self.find_node(wx, wy)
        if nid is not None: self.drag_node = nid; self.is_drag = False
        else: self.save_state(); self.graph.add_node(wx, wy); self.draw(); self.sel_node=None
            
    def drag(self, e):
        if self.drag_node is not None: 
            self.is_drag=True; n=self.graph.nodes[self.drag_node]
            n.x = self.to_world_x(self.cv.canvasx(e.x)); n.y = self.to_world_y(self.cv.canvasy(e.y)); self.draw()
            
    def up(self, e):
        if self.is_drag: self.drag_node=None; self.is_drag=False; return
        wx = self.to_world_x(self.cv.canvasx(e.x)); wy = self.to_world_y(self.cv.canvasy(e.y))
        nid = self.find_node(wx, wy)
        if nid is not None:
            if self.sel_node is None: self.sel_node=nid; self.draw()
            elif self.sel_node!=nid:
                d=EdgeDialog(self.root, self.sel_node, nid)
                if d.result: self.save_state(); self.graph.add_edge(self.sel_node, nid, d.result[0], d.result[1])
                self.sel_node=None; self.draw()
        else: self.sel_node=None; self.draw()
        self.drag_node=None; self.is_drag=False

    def find_node(self, wx, wy):
        for n in self.graph.nodes:
            if math.hypot(n.x - wx, n.y - wy) < self.base_r + 5: return n.id
        return None

    def draw(self):
        self.cv.delete("all"); self.cv.create_rectangle(-10000, -10000, 10000, 10000, fill="white", outline="white")
        current_r = self.base_r * self.zoom_scale
        font_size_node = int(16 * self.zoom_scale); font_size_edge = int(14 * self.zoom_scale)
        line_width_node = max(1, 3.0 * self.zoom_scale); line_width_edge = max(1, 3.0 * self.zoom_scale); line_width_sel = max(2, 6.0 * self.zoom_scale)
        existing_edges = set(); 
        for e in self.graph.edges: existing_edges.add((e.u, e.v))
        for e in self.graph.edges:
            u, v = self.graph.nodes[e.u], self.graph.nodes[e.v]
            sx, sy = int(self.to_screen_x(u.x)), int(self.to_screen_y(u.y))
            ex, ey = int(self.to_screen_x(v.x)), int(self.to_screen_y(v.y))
            has_reverse = (e.v, e.u) in existing_edges and e.u != e.v
            dx, dy = ex-sx, ey-sy; l = math.hypot(dx, dy)
            if l == 0: continue 
            arr = tk.LAST if e.is_directed else tk.NONE
            arrow_shape = (16*self.zoom_scale, 20*self.zoom_scale, 8*self.zoom_scale)
            if has_reverse:
                mx, my = (sx+ex)/2, (sy+ey)/2; offset = 40 * self.zoom_scale 
                nx, ny = -dy/l * offset, dx/l * offset; qx, qy = mx + nx, my + ny
                reduction = current_r + (5 * self.zoom_scale)
                ex_arrow = ex - (dx/l) * reduction; ey_arrow = ey - (dy/l) * reduction
                self.cv.create_line(sx, sy, qx, qy, ex_arrow, ey_arrow, smooth=True, fill="#34495e", width=line_width_edge, arrow=arr, arrowshape=arrow_shape, capstyle=tk.ROUND)
                lbl_x, lbl_y = qx, qy
            else:
                reduction = current_r + (5 * self.zoom_scale)
                if e.is_directed: ex_arrow = ex - (dx/l) * reduction; ey_arrow = ey - (dy/l) * reduction
                else: ex_arrow, ey_arrow = ex, ey 
                self.cv.create_line(sx, sy, ex_arrow, ey_arrow, fill="#34495e", width=line_width_edge, arrow=arr, arrowshape=arrow_shape, capstyle=tk.ROUND)
                lbl_x, lbl_y = (sx+ex)/2, (sy+ey)/2
            w_txt = str(int(e.weight)) if e.weight.is_integer() else str(e.weight)
            txt_id = self.cv.create_text(lbl_x, lbl_y, text=w_txt, fill="#e74c3c", font=("Segoe UI", font_size_edge, "bold"))
            bbox = self.cv.bbox(txt_id)
            if bbox:
                self.cv.create_rectangle(bbox[0]-4, bbox[1]-2, bbox[2]+4, bbox[3]+2, fill="white", outline="#bdc3c7", width=1)
                self.cv.tag_raise(txt_id)
        for n in self.graph.nodes:
            sx, sy = int(self.to_screen_x(n.x)), int(self.to_screen_y(n.y))
            fill = "#2ecc71"; width = line_width_node
            if n.id == self.sel_node: fill = "#f1c40f"; width = line_width_sel
            self.cv.create_oval(sx - current_r, sy - current_r, sx + current_r, sy + current_r, fill=fill, outline="#27ae60", width=width)
            self.cv.create_text(sx, sy, text=str(n.id), font=("Segoe UI", font_size_node, "bold"), fill="white")

    def hl_path_fill(self, p, col="#f1c40f", delay=500):
        self.draw(); current_r = self.base_r * self.zoom_scale; line_width_sel = max(2, 6.0 * self.zoom_scale); font_size_node = int(16 * self.zoom_scale)
        for nid in p:
            n = self.graph.nodes[nid]; sx, sy = self.to_screen_x(n.x), self.to_screen_y(n.y)
            self.cv.create_oval(sx - current_r, sy - current_r, sx + current_r, sy + current_r, fill=col, outline="#e67e22", width=line_width_sel)
            self.cv.create_text(sx, sy, text=str(n.id), font=("Segoe UI", font_size_node, "bold"), fill="white")
            self.root.update(); self.root.after(delay)
    
    def hl_edge(self, elist, col="#9b59b6"):
        self.draw()
        for e in elist:
            u,v = self.graph.nodes[e.u], self.graph.nodes[e.v]; sx, sy = self.to_screen_x(u.x), self.to_screen_y(u.y); ex, ey = self.to_screen_x(v.x), self.to_screen_y(v.y)
            arr = tk.LAST if e.is_directed else tk.NONE
            if e.is_directed:
                dx, dy = ex-sx, ey-sy; l = math.hypot(dx,dy); current_r = self.base_r * self.zoom_scale
                if l>0: ex -= (dx/l)*(current_r+5); ey -= (dy/l)*(current_r+5)
            self.cv.create_line(sx, sy, ex, ey, fill=col, width=max(2, 7.0*self.zoom_scale), arrow=arr, capstyle=tk.ROUND)
            self.root.update(); self.root.after(300)

    def save(self):
        f=filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")]); 
        if f: 
            with open(f,"w") as file: json.dump(self.graph.to_dict(), file)
            CustomPopup(self.root, "OK", "Đã lưu thành công.")
    def load(self):
        f=filedialog.askopenfilename(filetypes=[("JSON","*.json")])
        if f: 
            with open(f,"r") as file: self.graph.from_dict(json.load(file)); self.draw(); self.history = [] 
    def clear(self): self.save_state(); self.graph.clear(); self.sel_node=None; self.draw()

    def show_data(self):
        top = tk.Toplevel(self.root); top.title("Dữ Liệu Chi Tiết"); top.geometry("1100x600")
        nb = ttk.Notebook(top); nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        f_edge = tk.Frame(nb); nb.add(f_edge, text="Danh Sách Cạnh")
        cols = ("Nguồn (U)", "Đích (V)", "Trọng số (W)", "Hướng")
        tv = ttk.Treeview(f_edge, columns=cols, show="headings")
        for c in cols: tv.heading(c, text=c); tv.column(c, anchor="center")
        for e in self.graph.edges: tv.insert("", "end", values=(e.u, e.v, e.weight, "Có" if e.is_directed else "Không"))
        tv.pack(fill=tk.BOTH, expand=True)
        f_mat = tk.Frame(nb); nb.add(f_mat, text="Ma Trận Kề")
        node_ids = [str(n.id) for n in self.graph.nodes]; mat_cols = [""] + node_ids
        tv_mat = ttk.Treeview(f_mat, columns=mat_cols, show="headings")
        for c in mat_cols: tv_mat.heading(c, text=c); tv_mat.column(c, width=60, anchor="center")
        matrix = self.graph.get_matrix()
        for i, row in enumerate(matrix):
            row_vals = []; row_vals.append(str(self.graph.nodes[i].id))
            for x in row:
                if x == 0: row_vals.append(".")
                else: row_vals.append(str(int(x)) if isinstance(x, float) and x.is_integer() else str(x))
            tv_mat.insert("", "end", values=row_vals)
        sb_mat_x = ttk.Scrollbar(f_mat, orient="horizontal", command=tv_mat.xview); sb_mat_y = ttk.Scrollbar(f_mat, orient="vertical", command=tv_mat.yview)
        tv_mat.configure(xscrollcommand=sb_mat_x.set, yscrollcommand=sb_mat_y.set); sb_mat_x.pack(side=tk.BOTTOM, fill=tk.X); sb_mat_y.pack(side=tk.RIGHT, fill=tk.Y); tv_mat.pack(fill=tk.BOTH, expand=True)
        f_adj = tk.Frame(nb); nb.add(f_adj, text="Danh Sách Kề")
        t = tk.Text(f_adj, font=("Consolas", 16), padx=10, pady=10); t.pack(fill=tk.BOTH, expand=True)
        adj = self.graph.get_adj(directed=False) 
        for k,v in adj.items(): t.insert(tk.END, f"Node {k} -> {v}\n")