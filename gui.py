import tkinter as tk
from tkinter import filedialog, ttk
import math
import json

from model import Graph
from components import RoundedButton, CustomPopup, EdgeDialog, ComboSelectionDialog, AlgorithmSelectorDialog

class GraphGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DSA Graph Master - Optimized")
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

        # Menu chuột phải
        self.context_menu = tk.Menu(self.root, tearoff=0, font=("Segoe UI", 12))
        # Các lệnh sẽ được add động (dynamic) tùy vào click trúng cái gì
        
        self.target_for_deletion = None # Lưu đối tượng cần xóa (có thể là cạnh hoặc đỉnh)
        self.delete_mode = None # "edge" hoặc "node"

        self.setup_ui()

    def to_screen_x(self, world_x): return (world_x + self.offset_x) * self.zoom_scale
    def to_screen_y(self, world_y): return (world_y + self.offset_y) * self.zoom_scale
    def to_world_x(self, screen_x): return (screen_x / self.zoom_scale) - self.offset_x
    def to_world_y(self, screen_y): return (screen_y / self.zoom_scale) - self.offset_y

    def setup_ui(self):
        sb_bg = "#2c3e50"
        sb = tk.Frame(self.root, bg=sb_bg, width=380); sb.pack(side=tk.LEFT, fill=tk.Y); sb.pack_propagate(False)
        tk.Label(sb, text="GRAPH", font=("Segoe UI", 36, "bold"), bg=sb_bg, fg="white").pack(pady=30)
        
        def group_lbl(txt): tk.Label(sb, text=txt, bg=sb_bg, fg="#bdc3c7", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=25, pady=(20, 5))

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
        RoundedButton(sb, "BFS (Loang)", self.run_bfs, bg_color="#2980b9", hover_color="#3498db", width=BTN_W, height=BTN_H).pack(pady=5)
        RoundedButton(sb, "DFS (Sâu)", self.run_dfs, bg_color="#2980b9", hover_color="#3498db", width=BTN_W, height=BTN_H).pack(pady=5)
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
        
        # Binding chuột phải
        self.cv.bind("<Button-3>", self.on_right_click)
        self.cv.bind("<B3-Motion>", self.motion_pan)
        
        tk.Label(main, text="🖱️ Trái: Tạo/Kéo | Phải: Menu Xóa (Click Đỉnh/Cạnh) hoặc Kéo Màn Hình | Ctrl+Z: Undo", 
                 bg="#fdfdfd", fg="black", font=("Segoe UI", 14, "bold")).pack(pady=10)

    # --- LOGIC XỬ LÝ CHUỘT PHẢI (PAN / DELETE NODE / DELETE EDGE) ---
    def on_right_click(self, event):
        # Chuyển đổi tọa độ chuột sang World
        wx = self.to_world_x(self.cv.canvasx(event.x))
        wy = self.to_world_y(self.cv.canvasy(event.y))

        # 1. Ưu tiên kiểm tra ĐỈNH (Node) trước
        clicked_node_id = self.find_node(wx, wy)
        
        if clicked_node_id is not None:
            self.target_for_deletion = clicked_node_id
            self.delete_mode = "node"
            self.context_menu.delete(0, tk.END) # Xóa menu cũ
            self.context_menu.add_command(label=f"❌ Xóa Đỉnh {clicked_node_id}", command=self.execute_deletion)
            try: self.context_menu.tk_popup(event.x_root, event.y_root)
            finally: self.context_menu.grab_release()
            return

        # 2. Nếu không trúng đỉnh, kiểm tra CẠNH (Edge)
        clicked_edge = self.find_edge_at_pos(event.x, event.y)
        if clicked_edge:
            self.target_for_deletion = clicked_edge
            self.delete_mode = "edge"
            self.context_menu.delete(0, tk.END)
            self.context_menu.add_command(label="❌ Xóa Cạnh Này", command=self.execute_deletion)
            try: self.context_menu.tk_popup(event.x_root, event.y_root)
            finally: self.context_menu.grab_release()
            return

        # 3. Nếu không trúng gì cả -> Pan màn hình
        self.start_pan(event)

    def execute_deletion(self):
        if self.delete_mode == "node" and self.target_for_deletion is not None:
            self.save_state()
            self.graph.remove_node(self.target_for_deletion)
            # Reset selection nếu lỡ đang chọn đúng đỉnh vừa xóa
            if self.sel_node == self.target_for_deletion:
                self.sel_node = None
            self.draw()
            
        elif self.delete_mode == "edge" and self.target_for_deletion is not None:
            self.save_state()
            u, v, is_directed = self.target_for_deletion
            self.graph.remove_edge(u, v, is_directed)
            self.draw()
            
        self.target_for_deletion = None
        self.delete_mode = None

    def find_edge_at_pos(self, mx, my):
        threshold = 10.0
        for e in self.graph.edges:
            u_node = self.graph.nodes[e.u]
            v_node = self.graph.nodes[e.v]
            sx1, sy1 = self.to_screen_x(u_node.x), self.to_screen_y(u_node.y)
            sx2, sy2 = self.to_screen_x(v_node.x), self.to_screen_y(v_node.y)
            dist = self.dist_point_segment(mx, my, sx1, sy1, sx2, sy2)
            if dist < threshold:
                return (e.u, e.v, e.is_directed)
        return None

    def dist_point_segment(self, px, py, x1, y1, x2, y2):
        l2 = (x1-x2)**2 + (y1-y2)**2
        if l2 == 0: return math.hypot(px-x1, py-y1)
        t = ((px-x1)*(x2-x1) + (py-y1)*(y2-y1)) / l2
        t = max(0, min(1, t))
        proj_x = x1 + t*(x2-x1)
        proj_y = y1 + t*(y2-y1)
        return math.hypot(px-proj_x, py-proj_y)

    # --- (Các hàm cũ giữ nguyên) ---

    def show_adv_menu(self):
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
        d = AlgorithmSelectorDialog(self.root, algo_structure)
        if d.selected_func: d.selected_func()

    def ask_node(self, title, prompt, extra_opt=None):
        if not self.graph.nodes:
            CustomPopup(self.root, "Thông Báo", "Đồ thị chưa có đỉnh nào!\nHãy tạo đỉnh trước.", is_error=True)
            return None, False
        choices = [str(n.id) for n in self.graph.nodes]
        d = ComboSelectionDialog(self.root, title, prompt, choices, extra_option=extra_opt)
        if d.result is not None: return int(d.result), d.extra_val
        return None, False

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
        status, msg, auto_start_node = self.graph.get_euler_status()
        if status == 0: CustomPopup(self.root, "Không thể chạy", f"Lý do: {msg}", is_error=True); return
        CustomPopup(self.root, "Kiểm Tra Euler", f"Phát hiện: {msg}\n\nBấm 'Đã Hiểu' để chọn đỉnh (nếu cần) và chạy mô phỏng.")
        final_start_node = auto_start_node
        if status == 2:
            user_choice, _ = self.ask_node("Fleury", f"Chọn Đỉnh Bắt Đầu:\n(Mặc định: {auto_start_node})")
            if user_choice is not None:
                has_edge = any(e.u==user_choice or e.v==user_choice for e in self.graph.edges)
                if has_edge: final_start_node = user_choice
                else: CustomPopup(self.root, "Lỗi", f"Đỉnh {user_choice} cô lập, dùng mặc định {auto_start_node}", is_error=True)
        try:
            p = self.graph.fleury_algo(final_start_node)
            self.hl_path_fill(p, "#f1c40f")
            CustomPopup(self.root, "Kết Quả Fleury", f"Lộ trình: {p}")
        except Exception as e: CustomPopup(self.root, "Lỗi", str(e), is_error=True)

    def run_hierholzer(self):
        status, msg, auto_start_node = self.graph.get_euler_status()
        if status == 0: CustomPopup(self.root, "Không thể chạy", f"Lý do: {msg}", is_error=True); return
        CustomPopup(self.root, "Kiểm Tra Euler", f"Phát hiện: {msg}\n\nBấm 'Đã Hiểu' để chọn đỉnh (nếu cần) và chạy mô phỏng.")
        final_start_node = auto_start_node
        if status == 2:
            user_choice, _ = self.ask_node("Hierholzer", f"Chọn Đỉnh Bắt Đầu:\n(Mặc định: {auto_start_node})")
            if user_choice is not None:
                has_edge = any(e.u==user_choice or e.v==user_choice for e in self.graph.edges)
                if has_edge: final_start_node = user_choice
                else: CustomPopup(self.root, "Lỗi", f"Đỉnh {user_choice} cô lập, dùng mặc định {auto_start_node}", is_error=True)
        try:
            p = self.graph.hierholzer_algo(final_start_node)
            self.hl_path_fill(p, "#e67e22")
            CustomPopup(self.root, "Kết Quả Hierholzer", f"Lộ trình: {p}")
        except Exception as e: CustomPopup(self.root, "Lỗi", str(e), is_error=True)

    def run_hamilton(self):
        if len(self.graph.nodes) < 2:
            CustomPopup(self.root, "Lỗi", "Đồ thị cần ít nhất 2 đỉnh.", is_error=True); return

        has_cycle, cycle_path = self.graph.check_hamilton()
        if has_cycle:
            CustomPopup(self.root, "Thành Công", "Tìm thấy CHU TRÌNH Hamilton (Quay về đầu)!\nBấm 'Đã Hiểu' để chọn đỉnh xuất phát.")
            default_start = cycle_path[0]
            user_choice, _ = self.ask_node("Hamilton Cycle", f"Chọn Đỉnh Bắt Đầu:\n(Chu trình đi qua mọi đỉnh)")
            final_path = cycle_path
            if user_choice is not None:
                unique_nodes = cycle_path[:-1]
                if user_choice in unique_nodes:
                    idx = unique_nodes.index(user_choice)
                    rotated = unique_nodes[idx:] + unique_nodes[:idx]; rotated.append(user_choice)
                    final_path = rotated
            self.hl_path_fill(final_path, "#e84393")
            CustomPopup(self.root, "Kết Quả", f"Chu trình Hamilton:\n{final_path}")
            return

        has_path, path_nodes = self.graph.check_hamilton_path()
        if has_path:
            CustomPopup(self.root, "Thông Báo", "Không có Chu trình, nhưng tìm thấy ĐƯỜNG ĐI Hamilton!\nLưu ý: Đường đi có đầu/cuối cố định.")
            self.hl_path_fill(path_nodes, "#fd79a8")
            CustomPopup(self.root, "Kết Quả", f"Đường đi Hamilton:\n{path_nodes}")
        else:
            CustomPopup(self.root, "Thất Bại", "Không tồn tại Chu trình hay Đường đi Hamilton.", is_error=True)

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