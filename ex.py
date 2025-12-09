import tkinter as tk
from tkinter import filedialog, simpledialog, ttk
import heapq
from collections import deque, defaultdict
import copy
import math
import json
import platform
import sys

# =======================================================================================
# CẤU HÌNH ĐỘ NÉT CAO (HIGH-DPI)
# =======================================================================================
if platform.system() == "Windows":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception as e:
        pass

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
        
        msg_font = ("Segoe UI", 14) 
        btn_font = ("Segoe UI", 12, "bold")
        text_color = "#c0392b" if is_error else "#2c3e50"

        lbl = tk.Label(self, text=message, font=msg_font, bg="white", fg=text_color, wraplength=500, justify="left")
        lbl.pack(pady=30, padx=30)

        btn = tk.Button(self, text="Đã Hiểu", font=btn_font, command=self.destroy, 
                        bg="#3498db", fg="white", relief="flat", padx=20, pady=5, cursor="hand2")
        btn.pack(pady=(0, 20))

        w = self.winfo_reqwidth() + 60
        h = self.winfo_reqheight() + 60
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
# NEW: COMBOBOX SELECTION DIALOG (CHỌN TỪ DANH SÁCH)
# =======================================================================================
class ComboSelectionDialog(tk.Toplevel):
    def __init__(self, parent, title, prompt, choices):
        super().__init__(parent)
        self.title(title)
        self.configure(bg="white")
        self.result = None
        self.choices = choices
        
        # Center Window
        w, h = 400, 250
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        # UI Elements
        tk.Label(self, text=prompt, font=("Segoe UI", 14, "bold"), bg="white", fg="#2c3e50").pack(pady=(25, 10))
        
        # Dropdown (Combobox)
        self.cb = ttk.Combobox(self, values=choices, font=("Segoe UI", 14), state="readonly", width=15)
        if choices: self.cb.current(0) # Chọn mặc định phần tử đầu tiên
        self.cb.pack(pady=10, ipady=5)
        self.cb.focus()

        # Buttons
        f_btn = tk.Frame(self, bg="white")
        f_btn.pack(pady=20)
        
        tk.Button(f_btn, text="Xác Nhận", command=self.ok, bg="#27ae60", fg="white", 
                  font=("Segoe UI", 12, "bold"), padx=15, pady=5, relief="flat", cursor="hand2").pack(side=tk.LEFT, padx=10)
        
        tk.Button(f_btn, text="Hủy", command=self.destroy, bg="#e74c3c", fg="white", 
                  font=("Segoe UI", 12, "bold"), padx=15, pady=5, relief="flat", cursor="hand2").pack(side=tk.LEFT, padx=10)

        self.bind('<Return>', self.ok)
        self.transient(parent)
        self.grab_set()
        self.wait_window(self)

    def ok(self, event=None):
        val = self.cb.get()
        if val:
            self.result = val
            self.destroy()

# ==========================================
# 1. MODEL (LOGIC & THUẬT TOÁN)
# ==========================================
class Node:
    def __init__(self, node_id, x, y):
        self.id, self.x, self.y = node_id, x, y

class Edge:
    def __init__(self, u, v, w=1.0, d=False):
        self.u, self.v, self.weight, self.is_directed = u, v, w, d

class Graph:
    def __init__(self):
        self.nodes = []; self.edges = []
    
    def add_node(self, x, y):
        self.nodes.append(Node(len(self.nodes), x, y))
    
    def add_edge(self, u, v, w, d):
        for e in self.edges:
            if e.u == u and e.v == v: 
                e.weight = w; e.is_directed = d; return
            if not d and not e.is_directed and e.u == v and e.v == u:
                e.weight = w; return
        self.edges.append(Edge(u, v, w, d))
    
    def clear(self): self.nodes=[]; self.edges=[]
    
    def to_dict(self):
        return {"nodes": [{"id":n.id,"x":n.x,"y":n.y} for n in self.nodes],
                "edges": [{"u":e.u,"v":e.v,"w":e.weight,"d":e.is_directed} for e in self.edges]}
    
    def from_dict(self, data):
        self.clear()
        nodes = sorted(data["nodes"], key=lambda k: k['id'])
        for n in nodes: self.nodes.append(Node(n['id'], n['x'], n['y']))
        for e in data["edges"]: self.edges.append(Edge(e['u'], e['v'], e['w'], e.get('d',False)))

    def get_adj(self, directed=False):
        adj = {n.id: [] for n in self.nodes}
        for e in self.edges:
            adj[e.u].append((e.v, e.weight))
            if not directed and not e.is_directed: adj[e.v].append((e.u, e.weight))
        return adj
    
    def get_matrix(self):
        n = len(self.nodes); mat = [[0]*n for _ in range(n)]
        for e in self.edges:
            mat[e.u][e.v] = e.weight
            if not e.is_directed: mat[e.v][e.u] = e.weight
        return mat

    # --- BASIC ALGORITHMS ---
    def bfs(self, s):
        if s is None or s>=len(self.nodes): return []
        adj = self.get_adj() 
        vis=set(); q=deque([s]); vis.add(s); p=[]
        while q:
            u=q.popleft(); p.append(u)
            for v,w in sorted(adj[u], key=lambda x: x[0]):
                if v not in vis: vis.add(v); q.append(v)
        return p
    
    def dfs(self, s):
        if s is None or s>=len(self.nodes): return []
        adj = self.get_adj()
        vis=set(); p=[]
        def _d(u):
            vis.add(u); p.append(u)
            for v,w in sorted(adj[u], key=lambda x: x[0]):
                if v not in vis: _d(v)
        _d(s); return p

    def dijkstra(self, s, e):
        adj=self.get_adj(); pq=[(0,s)]
        dist={i:float('inf') for i in range(len(self.nodes))}; dist[s]=0
        par={i:None for i in range(len(self.nodes))}
        while pq:
            d,u = heapq.heappop(pq)
            if d>dist[u]: continue
            if u==e: break
            for v,w in adj[u]:
                if dist[u]+w < dist[v]:
                    dist[v]=dist[u]+w; par[v]=u; heapq.heappush(pq,(dist[v],v))
        if dist[e]==float('inf'): return None, float('inf')
        p=[]; c=e
        while c is not None: p.append(c); c=par[c]
        return p[::-1], dist[e]

    def bellman_ford(self, s, e):
        n = len(self.nodes)
        dist = {i: float('inf') for i in range(n)}
        dist[s] = 0
        par = {i: None for i in range(n)}
        for _ in range(n - 1):
            changed = False
            for edge in self.edges:
                if dist[edge.u] != float('inf') and dist[edge.u] + edge.weight < dist[edge.v]:
                    dist[edge.v] = dist[edge.u] + edge.weight; par[edge.v] = edge.u; changed = True
                if not edge.is_directed:
                    if dist[edge.v] != float('inf') and dist[edge.v] + edge.weight < dist[edge.u]:
                        dist[edge.u] = dist[edge.v] + edge.weight; par[edge.u] = edge.v; changed = True
            if not changed: break
        for edge in self.edges:
            if dist[edge.u] != float('inf') and dist[edge.u] + edge.weight < dist[edge.v]: return None, float('-inf')
            if not edge.is_directed and dist[edge.v] != float('inf') and dist[edge.v] + edge.weight < dist[edge.u]: return None, float('-inf')
        if dist[e] == float('inf'): return None, float('inf')
        p = []; curr = e
        while curr is not None:
            p.append(curr); 
            if curr == s: break
            curr = par[curr]
        return p[::-1], dist[e]

    def prim(self):
        if not self.nodes: return [],0
        adj={n.id:[] for n in self.nodes}
        for e in self.edges: 
            adj[e.u].append((e.v,e.weight)); adj[e.v].append((e.u,e.weight)) 
        vis={0}; pq=[]; me=[]; mw=0
        for v,w in adj[0]: heapq.heappush(pq,(w,0,v))
        while pq and len(vis)<len(self.nodes):
            w,u,v=heapq.heappop(pq)
            if v in vis: continue
            vis.add(v); me.append(Edge(u,v,w)); mw+=w
            for nv,nw in adj[v]: 
                if nv not in vis: heapq.heappush(pq,(nw,v,nv))
        return me, mw

    def kruskal(self):
        se=sorted(self.edges, key=lambda x:x.weight); par=list(range(len(self.nodes))); me=[]; mw=0
        def find(i): 
            if par[i]==i: return i
            par[i]=find(par[i]); return par[i]
        def union(i,j):
            ri,rj=find(i),find(j)
            if ri!=rj: par[ri]=rj; return True
            return False
        for e in se:
            if union(e.u,e.v): me.append(Edge(e.u,e.v,e.weight)); mw+=e.weight
        return me, mw

    # --- HAMILTON ---
    def check_hamilton(self):
        n = len(self.nodes)
        if n == 0: return False, []
        adj = self.get_adj()
        path = []; visited = [False] * n
        def is_safe(v, pos, path):
            u = path[pos-1]; is_adjacent = False
            for neighbor, _ in adj[u]:
                if neighbor == v: is_adjacent = True; break
            if not is_adjacent: return False
            if visited[v]: return False
            return True
        def ham_cycle_util(pos):
            if pos == n:
                start, last = path[0], path[-1]
                for v, _ in adj[last]:
                    if v == start: return True
                return False
            for v in range(n):
                if is_safe(v, pos, path):
                    path.append(v); visited[v] = True
                    if ham_cycle_util(pos + 1): return True
                    visited[v] = False; path.pop()
            return False
        for start_node in range(n):
            path = [start_node]; visited = [False] * n; visited[start_node] = True
            if ham_cycle_util(1):
                path.append(path[0])
                return True, path
        return False, []

    # --- EULER ---
    def get_euler_status(self):
        if not self.nodes: return 0, "Đồ thị trống", None
        is_directed_graph = any(e.is_directed for e in self.edges)
        adj_undirected = defaultdict(list); degrees_check = defaultdict(int) 
        for e in self.edges:
            adj_undirected[e.u].append(e.v); adj_undirected[e.v].append(e.u)
            degrees_check[e.u] += 1; degrees_check[e.v] += 1
        non_zero_degree = [n.id for n in self.nodes if degrees_check[n.id] > 0]
        if not non_zero_degree: return 0, "Không có cạnh nào", None
        start_node_bfs = non_zero_degree[0]; q = deque([start_node_bfs]); vis = {start_node_bfs}; count = 0
        while q:
            u = q.popleft(); count += 1
            for v in adj_undirected[u]:
                if v not in vis: vis.add(v); q.append(v)
        if count != len(non_zero_degree): return 0, "Đồ thị không liên thông", None
        if is_directed_graph:
            in_degree = defaultdict(int); out_degree = defaultdict(int)
            for e in self.edges:
                if e.is_directed: out_degree[e.u] += 1; in_degree[e.v] += 1
                else: out_degree[e.u] += 1; in_degree[e.v] += 1; out_degree[e.v] += 1; in_degree[e.u] += 1
            is_cycle = True
            for n in self.nodes:
                if in_degree[n.id] != out_degree[n.id]: is_cycle = False; break
            if is_cycle: return 2, "Đồ thị CÓ HƯỚNG: Chu trình Euler", non_zero_degree[0]
            start_nodes = []; end_nodes = []; others_balanced = True
            for n in self.nodes:
                diff = out_degree[n.id] - in_degree[n.id]
                if diff == 1: start_nodes.append(n.id)
                elif diff == -1: end_nodes.append(n.id)
                elif diff == 0: continue
                else: others_balanced = False; break
            if others_balanced and len(start_nodes) == 1 and len(end_nodes) == 1:
                return 1, "Đồ thị CÓ HƯỚNG: Đường đi Euler", start_nodes[0]
            return 0, "Đồ thị CÓ HƯỚNG: Không Euler", None
        else:
            degree = defaultdict(int)
            for e in self.edges: degree[e.u] += 1; degree[e.v] += 1
            odd_nodes = [n.id for n in self.nodes if degree[n.id] % 2 != 0]
            if len(odd_nodes) == 0: return 2, "Đồ thị VÔ HƯỚNG: Chu trình Euler", non_zero_degree[0]
            elif len(odd_nodes) == 2: return 1, "Đồ thị VÔ HƯỚNG: Đường đi Euler", odd_nodes[0]
            else: return 0, f"Đồ thị VÔ HƯỚNG: Không Euler ({len(odd_nodes)} lẻ)", None

    def fleury_algo(self, start_node):
        is_directed = any(e.is_directed for e in self.edges)
        adj = defaultdict(list)
        for e in self.edges:
            adj[e.u].append(e.v)
            if not is_directed and not e.is_directed: adj[e.v].append(e.u)
            elif is_directed and not e.is_directed: adj[e.v].append(e.u)
        path = [start_node]; curr = start_node
        while True:
            if not adj[curr]: break
            chosen_v = -1; 
            if len(adj[curr]) == 1: chosen_v = adj[curr][0]
            else:
                for v in adj[curr]:
                    adj[curr].remove(v)
                    if not is_directed: adj[v].remove(curr)
                    adj[curr].append(v)
                    if not is_directed: adj[v].append(curr)
                    chosen_v = v; break 
                if chosen_v == -1: chosen_v = adj[curr][0]
            adj[curr].remove(chosen_v)
            if not is_directed: 
                try: adj[chosen_v].remove(curr)
                except: pass
            path.append(chosen_v); curr = chosen_v
        return path

    def hierholzer_algo(self, start_node):
        is_directed = any(e.is_directed for e in self.edges)
        adj = defaultdict(list)
        for e in self.edges: 
            adj[e.u].append(e.v)
            if not is_directed and not e.is_directed: adj[e.v].append(e.u) 
            elif is_directed and not e.is_directed: adj[e.v].append(e.u)
        for u in adj: adj[u].sort(reverse=True)
        stack=[start_node]; path=[]
        while stack:
            v = stack[-1]
            if adj[v]:
                u = adj[v].pop()
                if not is_directed and u in adj:
                    try: adj[u].remove(v)
                    except ValueError: pass
                stack.append(u)
            else: path.append(stack.pop())
        return path[::-1]

    # --- OTHER ---
    def check_bipartite(self):
        if not self.nodes: return False,{}
        adj={n.id:[] for n in self.nodes}
        for e in self.edges: adj[e.u].append(e.v); adj[e.v].append(e.u)
        col={}; valid=True
        for i in range(len(self.nodes)):
            if i not in col:
                col[i]=0; q=deque([i])
                while q:
                    u=q.popleft()
                    for v in adj[u]:
                        if v not in col: col[v]=1-col[u]; q.append(v)
                        elif col[v]==col[u]: return False, {}
        return True, col

    def ford_fulkerson(self, s, t):
        n = len(self.nodes)
        cap = [[0.0]*n for _ in range(n)]
        for e in self.edges:
            cap[e.u][e.v] = e.weight
            if not e.is_directed: cap[e.v][e.u] = e.weight
        max_f = 0.0
        while True:
            par = [-1]*n; q = deque([(s, float('inf'))]); par[s] = -2; path_f = 0.0
            while q:
                u, flow = q.popleft()
                for v in range(n):
                    if par[v]==-1 and cap[u][v] > 0:
                        par[v] = u; new_f = min(flow, cap[u][v])
                        if v==t: path_f=new_f; break
                        q.append((v, new_f))
                if path_f > 0: break
            if path_f == 0: break
            max_f += path_f; curr = t
            while curr!=s:
                p = par[curr]; cap[p][curr] -= path_f; cap[curr][p] += path_f; curr = p
        return max_f

# ==========================================
# 2. UI COMPONENTS
# ==========================================
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
        self.create_text(w/2, h/2, text=self.text_str, fill=self.fg_color, font=("Segoe UI", 12, "bold"))

    def on_click(self, event):
        if self.command: self.command()
    def on_enter(self, event): self.draw_button(self.hover_color); self.config(cursor="hand2")
    def on_leave(self, event): self.draw_button(self.bg_color)

class EdgeDialog(tk.Toplevel):
    def __init__(self, parent, u, v):
        super().__init__(parent); self.title("Thêm Cạnh"); self.geometry("500x350")
        self.configure(bg="white"); self.result = None
        main_font = ("Segoe UI", 14)
        header_font = ("Segoe UI", 18, "bold")
        btn_font = ("Segoe UI", 12, "bold")
        tk.Label(self, text=f"Kết nối: {u}  ➜  {v}", font=header_font, bg="white", fg="#2c3e50").pack(pady=25)
        f1 = tk.Frame(self, bg="white"); f1.pack(pady=15)
        tk.Label(f1, text="Trọng số:", bg="white", font=main_font).pack(side=tk.LEFT)
        self.ew = tk.Entry(f1, width=10, font=("Segoe UI", 14, "bold"), bd=2, relief="groove", justify='center')
        self.ew.insert(0,"1"); self.ew.pack(side=tk.LEFT, padx=10, ipady=3); self.ew.focus()
        self.vd = tk.BooleanVar(value=True) 
        tk.Checkbutton(self, text="Có hướng (Mũi tên)", variable=self.vd, bg="white", font=main_font, fg="#e67e22", cursor="hand2").pack(pady=15)
        f_btn = tk.Frame(self, bg="white"); f_btn.pack(pady=15)
        tk.Button(f_btn, text="Xác Nhận", command=self.ok, bg="#27ae60", fg="white", font=btn_font, width=15, pady=10, bd=0, relief="flat", activebackground="#2ecc71", activeforeground="white", cursor="hand2").pack(side=tk.LEFT, padx=15)
        tk.Button(f_btn, text="Hủy Bỏ", command=self.destroy, bg="#e74c3c", fg="white", font=btn_font, width=15, pady=10, bd=0, relief="flat", activebackground="#c0392b", activeforeground="white", cursor="hand2").pack(side=tk.LEFT, padx=15)
        self.bind('<Return>', self.ok) 
        self.transient(parent); self.grab_set(); self.wait_window(self)
    def ok(self, event=None):
        try: 
            w = float(self.ew.get()) 
            self.result = (w, self.vd.get())
            self.destroy()
        except ValueError: 
            CustomPopup(self, "Lỗi Nhập Liệu", "Vui lòng nhập số thực hợp lệ!", is_error=True)

# ==========================================
# 3. GIAO DIỆN CHÍNH (GRAPH GUI)
# ==========================================
class GraphGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DSA Graph Master - Optimized (Dropdown Selection)")
        self.root.geometry("1600x900")
        self.root.configure(bg="#fdfdfd")
        
        self.history = [] 
        self.root.bind("<Control-z>", self.undo)
        self.root.bind("<Control-Z>", self.undo)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="white", foreground="#333", rowheight=35, font=("Segoe UI", 12))
        style.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"))
        
        self.graph = Graph()
        self.sel_node = None; self.drag_node = None; self.is_drag = False
        
        # --- CAMERA ---
        self.base_r = 35 
        self.zoom_scale = 1.0 
        self.offset_x = 0; self.offset_y = 0
        self.last_mouse_x = 0; self.last_mouse_y = 0

        self.setup_ui()

    def to_screen_x(self, world_x):
        return (world_x + self.offset_x) * self.zoom_scale
    def to_screen_y(self, world_y):
        return (world_y + self.offset_y) * self.zoom_scale
    def to_world_x(self, screen_x):
        return (screen_x / self.zoom_scale) - self.offset_x
    def to_world_y(self, screen_y):
        return (screen_y / self.zoom_scale) - self.offset_y

    def setup_ui(self):
        sb_bg = "#2c3e50"
        sb = tk.Frame(self.root, bg=sb_bg, width=350); sb.pack(side=tk.LEFT, fill=tk.Y); sb.pack_propagate(False)
        tk.Label(sb, text="GRAPH", font=("Segoe UI", 30, "bold"), bg=sb_bg, fg="white").pack(pady=20)
        
        def group_lbl(txt): tk.Label(sb, text=txt, bg=sb_bg, fg="#bdc3c7", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=25, pady=(20, 5))

        group_lbl("HỆ THỐNG")
        RoundedButton(sb, "Hoàn Tác (Ctrl+Z)", self.undo, bg_color="#e67e22", hover_color="#d35400", width=280, height=50).pack(pady=4)
        RoundedButton(sb, "Xóa Tất Cả", self.clear, bg_color="#c0392b", hover_color="#e74c3c", width=280, height=50).pack(pady=4)

        group_lbl("DỮ LIỆU")
        RoundedButton(sb, "Lưu File (.json)", self.save, bg_color="#16a085", hover_color="#1abc9c", width=280, height=50).pack(pady=4)
        RoundedButton(sb, "Mở File (.json)", self.load, bg_color="#16a085", hover_color="#1abc9c", width=280, height=50).pack(pady=4)
        RoundedButton(sb, "Xem Bảng Dữ Liệu", self.show_data, bg_color="#8e44ad", hover_color="#9b59b6", width=280, height=50).pack(pady=4)

        group_lbl("THUẬT TOÁN")
        RoundedButton(sb, "BFS (Loang)", self.run_bfs, bg_color="#2980b9", hover_color="#3498db", width=280, height=50).pack(pady=4)
        RoundedButton(sb, "DFS (Sâu)", self.run_dfs, bg_color="#2980b9", hover_color="#3498db", width=280, height=50).pack(pady=4)
        RoundedButton(sb, "Dijkstra / Euler / MST", self.show_adv_menu, bg_color="#f39c12", hover_color="#f1c40f", width=280, height=50).pack(pady=4)

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
                 bg="#fdfdfd", fg="black", font=("Segoe UI", 12, "bold")).pack(pady=8)

    def show_adv_menu(self):
        top = tk.Toplevel(self.root); top.title("Nâng Cao"); top.geometry("350x660"); top.configure(bg="white")
        tk.Label(top, text="Chọn Thuật Toán", font=("Segoe UI", 16, "bold"), bg="white", fg="#2c3e50").pack(pady=15)
        def run_and_close(func): func(); top.destroy()
        
        RoundedButton(top, "Dijkstra", lambda: run_and_close(self.run_dijkstra), width=300, height=45).pack(pady=5)
        RoundedButton(top, "Bellman-Ford", lambda: run_and_close(self.run_bellman_ford), width=300, height=45, bg_color="#e74c3c").pack(pady=5)
        
        f_euler = tk.Frame(top, bg="#ecf0f1", bd=1, relief="solid"); f_euler.pack(pady=10, padx=20, ipadx=5, ipady=5)
        tk.Label(f_euler, text="--- Euler (Vô hướng/Có hướng) ---", bg="#ecf0f1", font=("Segoe UI", 10, "bold"), fg="#7f8c8d").pack(pady=2)
        RoundedButton(f_euler, "Thuật toán Fleury", lambda: run_and_close(self.run_fleury), width=280, height=40, bg_color="#e67e22").pack(pady=3)
        RoundedButton(f_euler, "Thuật toán Hierholzer", lambda: run_and_close(self.run_hierholzer), width=280, height=40, bg_color="#d35400").pack(pady=3)
        
        RoundedButton(top, "Chu trình Hamilton", lambda: run_and_close(self.run_hamilton), width=300, height=45, bg_color="#fd79a8").pack(pady=5)
        RoundedButton(top, "Prim (MST)", lambda: run_and_close(self.run_prim), width=300, height=45).pack(pady=5)
        RoundedButton(top, "Kruskal (MST)", lambda: run_and_close(self.run_kruskal), width=300, height=45).pack(pady=5)
        RoundedButton(top, "Max Flow", lambda: run_and_close(self.run_maxflow), width=300, height=45).pack(pady=5)
        RoundedButton(top, "Kiểm tra 2 Phía", lambda: run_and_close(self.run_bi), width=300, height=45).pack(pady=5)

    # --- HELPER: SHOW DROPDOWN DIALOG ---
    def ask_node(self, title, prompt):
        if not self.graph.nodes:
            CustomPopup(self.root, "Thông Báo", "Đồ thị chưa có đỉnh nào!\nHãy tạo đỉnh trước.", is_error=True)
            return None
        
        # Get list of node IDs as strings for the dropdown
        choices = [str(n.id) for n in self.graph.nodes]
        d = ComboSelectionDialog(self.root, title, prompt, choices)
        
        if d.result is not None:
            return int(d.result) # Convert back to int for logic
        return None

    # --- ALGORITHM RUNNERS (UPDATED WITH DROPDOWN) ---
    def run_bfs(self):
        s = self.ask_node("BFS", "Chọn Đỉnh Bắt Đầu:")
        if s is not None:
            p = self.graph.bfs(s); self.hl_path_fill(p); CustomPopup(self.root, "Kết Quả BFS", f"Thứ tự: {p}")

    def run_dfs(self):
        s = self.ask_node("DFS", "Chọn Đỉnh Bắt Đầu:")
        if s is not None:
            p = self.graph.dfs(s); self.hl_path_fill(p); CustomPopup(self.root, "Kết Quả DFS", f"Thứ tự: {p}")

    def run_dijkstra(self):
        if any(e.weight < 0 for e in self.graph.edges):
            CustomPopup(self.root, "Lỗi Thuật Toán", "Dijkstra KHÔNG hoạt động với trọng số ÂM!", is_error=True); return
        s = self.ask_node("Dijkstra", "Chọn Điểm Đi (Start):")
        if s is None: return
        e = self.ask_node("Dijkstra", "Chọn Điểm Đến (End):")
        if e is None: return
        
        p, w = self.graph.dijkstra(s,e)
        if p: self.hl_path_fill(p, "#e74c3c"); CustomPopup(self.root, "Kết Quả", f"Tổng Chi Phí: {w}\nLộ Trình: {p}")
        else: CustomPopup(self.root, "Lỗi", "Không tìm thấy đường đi!", is_error=True)

    def run_bellman_ford(self):
        s = self.ask_node("Bellman-Ford", "Chọn Điểm Đi (Start):")
        if s is None: return
        e = self.ask_node("Bellman-Ford", "Chọn Điểm Đến (End):")
        if e is None: return

        path, cost = self.graph.bellman_ford(s, e)
        if cost == float('-inf'):
            CustomPopup(self.root, "Cảnh Báo", "Phát hiện CHU TRÌNH ÂM!\nKhông thể tính đường đi ngắn nhất.", is_error=True)
        elif path:
            self.hl_path_fill(path, "#e74c3c"); CustomPopup(self.root, "Kết Quả", f"Tổng Chi Phí: {cost}\nLộ Trình: {path}")
        else: CustomPopup(self.root, "Lỗi", "Không tìm thấy đường đi!", is_error=True)

    def run_maxflow(self):
        s = self.ask_node("Flow", "Chọn Nguồn (Source):")
        if s is None: return
        t = self.ask_node("Flow", "Chọn Đích (Sink):")
        if t is None: return
        
        f = self.graph.ford_fulkerson(s,t); CustomPopup(self.root, "Max Flow", f"Luồng Cực Đại: {f}")

    def run_fleury(self):
        status, msg, auto_start_node = self.graph.get_euler_status()
        if status == 0: CustomPopup(self.root, "Không thể chạy", f"Lý do: {msg}", is_error=True); return
        final_start_node = auto_start_node
        if status == 2:
            # Dropdown for user choice
            user_choice = self.ask_node("Fleury", f"Chọn Đỉnh Bắt Đầu:\n(Mặc định: {auto_start_node})")
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
        final_start_node = auto_start_node
        if status == 2:
            user_choice = self.ask_node("Hierholzer", f"Chọn Đỉnh Bắt Đầu:\n(Mặc định: {auto_start_node})")
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
        if len(self.graph.nodes) < 3:
            CustomPopup(self.root, "Lỗi", "Đồ thị cần ít nhất 3 đỉnh để xét chu trình Hamilton.", is_error=True); return
        found, path = self.graph.check_hamilton()
        if found:
            self.hl_path_fill(path, "#e84393") 
            CustomPopup(self.root, "Thành Công", f"Tìm thấy Chu trình Hamilton:\n{path}")
        else:
            CustomPopup(self.root, "Thất Bại", "Không tồn tại chu trình Hamilton trong đồ thị này.", is_error=True)

    def run_prim(self): 
        if any(e.is_directed for e in self.graph.edges):
            CustomPopup(self.root, "Lỗi Thuật Toán", "MST (Prim) chỉ áp dụng cho đồ thị VÔ HƯỚNG!", is_error=True); return
        e,w=self.graph.prim(); self.hl_edge(e, "#3498db"); CustomPopup(self.root, "Prim MST", f"Tổng Trọng Số: {w}")

    def run_kruskal(self):
        if any(e.is_directed for e in self.graph.edges):
            CustomPopup(self.root, "Lỗi Thuật Toán", "MST (Kruskal) chỉ áp dụng cho đồ thị VÔ HƯỚNG!", is_error=True); return
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
                self.cv.create_text(sx,sy,text=str(n.id),font=("Segoe UI",int(14*self.zoom_scale),"bold"), fill="white")
            CustomPopup(self.root, "Kết Quả", "Là Đồ Thị 2 Phía")
        else: CustomPopup(self.root, "Kết Quả", "KHÔNG Phải Đồ Thị 2 Phía", is_error=True)

    # --- SAVE/LOAD/UNDO/ZOOM ---
    def save_state(self):
        state = self.graph.to_dict()
        self.history.append(state)
        if len(self.history) > 20: self.history.pop(0)

    def undo(self, event=None):
        if not self.history:
            CustomPopup(self.root, "Thông báo", "Không còn thao tác nào để quay lại!")
            return
        last_state = self.history.pop()
        self.graph.from_dict(last_state)
        self.sel_node = None
        self.draw()

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

    def start_pan(self, event):
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y

    def motion_pan(self, event):
        dx = event.x - self.last_mouse_x
        dy = event.y - self.last_mouse_y
        self.offset_x += dx / self.zoom_scale
        self.offset_y += dy / self.zoom_scale
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.draw()

    def down(self, e):
        wx = self.to_world_x(self.cv.canvasx(e.x)); wy = self.to_world_y(self.cv.canvasy(e.y))
        nid = self.find_node(wx, wy)
        if nid is not None: 
            self.drag_node = nid; self.is_drag = False
        else: 
            self.save_state(); self.graph.add_node(wx, wy); self.draw(); self.sel_node=None
            
    def drag(self, e):
        if self.drag_node is not None: 
            self.is_drag=True
            n=self.graph.nodes[self.drag_node]
            n.x = self.to_world_x(self.cv.canvasx(e.x))
            n.y = self.to_world_y(self.cv.canvasy(e.y))
            self.draw()
            
    def up(self, e):
        if self.is_drag: self.drag_node=None; self.is_drag=False; return
        wx = self.to_world_x(self.cv.canvasx(e.x)); wy = self.to_world_y(self.cv.canvasy(e.y))
        nid = self.find_node(wx, wy)
        if nid is not None:
            if self.sel_node is None: self.sel_node=nid; self.draw()
            elif self.sel_node!=nid:
                d=EdgeDialog(self.root, self.sel_node, nid)
                if d.result: 
                    self.save_state(); self.graph.add_edge(self.sel_node, nid, d.result[0], d.result[1])
                self.sel_node=None; self.draw()
        else: self.sel_node=None; self.draw()
        self.drag_node=None; self.is_drag=False

    def find_node(self, wx, wy):
        for n in self.graph.nodes:
            if math.hypot(n.x - wx, n.y - wy) < self.base_r + 5: return n.id
        return None

    def draw(self):
        self.cv.delete("all")
        self.cv.create_rectangle(-10000, -10000, 10000, 10000, fill="white", outline="white")
        current_r = self.base_r * self.zoom_scale
        font_size_node = int(14 * self.zoom_scale)
        font_size_edge = int(12 * self.zoom_scale)
        line_width_node = max(1, 3.0 * self.zoom_scale)
        line_width_edge = max(1, 3.0 * self.zoom_scale)
        line_width_sel = max(2, 6.0 * self.zoom_scale)
        
        existing_edges = set()
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
                mx, my = (sx+ex)/2, (sy+ey)/2
                offset = 40 * self.zoom_scale 
                nx, ny = -dy/l * offset, dx/l * offset
                qx, qy = mx + nx, my + ny
                reduction = current_r + (5 * self.zoom_scale)
                ex_arrow = ex - (dx/l) * reduction
                ey_arrow = ey - (dy/l) * reduction
                self.cv.create_line(sx, sy, qx, qy, ex_arrow, ey_arrow, smooth=True, 
                                    fill="#34495e", width=line_width_edge, arrow=arr, 
                                    arrowshape=arrow_shape, capstyle=tk.ROUND)
                lbl_x, lbl_y = qx, qy
            else:
                reduction = current_r + (5 * self.zoom_scale)
                if e.is_directed:
                    ex_arrow = ex - (dx/l) * reduction
                    ey_arrow = ey - (dy/l) * reduction
                else: ex_arrow, ey_arrow = ex, ey 
                self.cv.create_line(sx, sy, ex_arrow, ey_arrow, fill="#34495e", width=line_width_edge, 
                                    arrow=arr, arrowshape=arrow_shape, capstyle=tk.ROUND)
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
            self.cv.create_oval(sx - current_r, sy - current_r, sx + current_r, sy + current_r, 
                                fill=fill, outline="#27ae60", width=width)
            self.cv.create_text(sx, sy, text=str(n.id), font=("Segoe UI", font_size_node, "bold"), fill="white")

    def hl_path_fill(self, p, col="#f1c40f", delay=500):
        self.draw()
        current_r = self.base_r * self.zoom_scale
        line_width_sel = max(2, 6.0 * self.zoom_scale)
        font_size_node = int(14 * self.zoom_scale)
        for nid in p:
            n = self.graph.nodes[nid]
            sx, sy = self.to_screen_x(n.x), self.to_screen_y(n.y)
            self.cv.create_oval(sx - current_r, sy - current_r, sx + current_r, sy + current_r, 
                                fill=col, outline="#e67e22", width=line_width_sel)
            self.cv.create_text(sx, sy, text=str(n.id), font=("Segoe UI", font_size_node, "bold"), fill="white")
            self.root.update(); self.root.after(delay)
    
    def hl_edge(self, elist, col="#9b59b6"):
        self.draw()
        for e in elist:
            u,v = self.graph.nodes[e.u], self.graph.nodes[e.v]
            sx, sy = self.to_screen_x(u.x), self.to_screen_y(u.y)
            ex, ey = self.to_screen_x(v.x), self.to_screen_y(v.y)
            arr = tk.LAST if e.is_directed else tk.NONE
            if e.is_directed:
                dx, dy = ex-sx, ey-sy; l = math.hypot(dx,dy)
                current_r = self.base_r * self.zoom_scale
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
            with open(f,"r") as file: self.graph.from_dict(json.load(file))
            self.draw()
            self.history = [] 
    def clear(self): 
        self.save_state()
        self.graph.clear(); self.sel_node=None; self.draw()

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
        node_ids = [str(n.id) for n in self.graph.nodes]
        mat_cols = [""] + node_ids
        tv_mat = ttk.Treeview(f_mat, columns=mat_cols, show="headings")
        for c in mat_cols:
            tv_mat.heading(c, text=c)
            tv_mat.column(c, width=60, anchor="center")
        matrix = self.graph.get_matrix()
        for i, row in enumerate(matrix):
            row_vals = []
            row_vals.append(str(self.graph.nodes[i].id))
            for x in row:
                if x == 0: row_vals.append(".")
                else: row_vals.append(str(int(x)) if isinstance(x, float) and x.is_integer() else str(x))
            tv_mat.insert("", "end", values=row_vals)
        sb_mat_x = ttk.Scrollbar(f_mat, orient="horizontal", command=tv_mat.xview)
        sb_mat_y = ttk.Scrollbar(f_mat, orient="vertical", command=tv_mat.yview)
        tv_mat.configure(xscrollcommand=sb_mat_x.set, yscrollcommand=sb_mat_y.set)
        sb_mat_x.pack(side=tk.BOTTOM, fill=tk.X)
        sb_mat_y.pack(side=tk.RIGHT, fill=tk.Y)
        tv_mat.pack(fill=tk.BOTH, expand=True)

        f_adj = tk.Frame(nb); nb.add(f_adj, text="Danh Sách Kề")
        t = tk.Text(f_adj, font=("Consolas", 14), padx=10, pady=10); t.pack(fill=tk.BOTH, expand=True)
        adj = self.graph.get_adj(directed=False) 
        for k,v in adj.items(): t.insert(tk.END, f"Node {k} -> {v}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = GraphGUI(root)
    root.mainloop()