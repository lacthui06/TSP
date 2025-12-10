import heapq
from collections import deque, defaultdict
import math

class Node:
    def __init__(self, node_id, x, y):
        self.id, self.x, self.y = node_id, x, y

class Edge:
    def __init__(self, u, v, w=1.0, d=False):
        self.u, self.v, self.weight, self.is_directed = u, v, w, d

class Graph:
    def __init__(self):
        self.nodes = []
        self.edges = []
    
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

    # --- ALGORITHMS ---
    
    def bfs(self, s, descending=False):
        if s is None or s >= len(self.nodes): return []
        adj = self.get_adj() 
        vis = set(); q = deque([s]); vis.add(s); p = []
        while q:
            u = q.popleft(); p.append(u)
            neighbors = [item for item in adj[u] if item[0] not in vis]
            neighbors.sort(key=lambda x: x[0], reverse=descending)
            for v, w in neighbors:
                if v not in vis: vis.add(v); q.append(v)
        return p
    
    def dfs(self, s, descending=False):
        if s is None or s >= len(self.nodes): return []
        adj = self.get_adj(); vis = set(); stack = [s]; p = []
        while stack:
            u = stack.pop()
            if u not in vis:
                vis.add(u); p.append(u)
                neighbors = [item for item in adj[u] if item[0] not in vis]
                sort_order_for_stack = not descending 
                neighbors.sort(key=lambda x: x[0], reverse=sort_order_for_stack)
                for v, w in neighbors: stack.append(v)
        return p

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
        n = len(self.nodes); dist = {i: float('inf') for i in range(n)}; dist[s] = 0; par = {i: None for i in range(n)}
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
        while curr is not None: p.append(curr); curr = par[curr]
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

    # --- HÀM MỚI: TÌM ĐƯỜNG ĐI HAMILTON (KHÔNG CẦN KÍN) ---
    def check_hamilton_path(self):
        n = len(self.nodes)
        if n == 0: return False, []
        adj = self.get_adj()
        visited = [False] * n
        path = []

        def is_safe(v, pos, path):
            u = path[pos-1]
            is_adjacent = False
            for neighbor, _ in adj[u]:
                if neighbor == v: is_adjacent = True; break
            if not is_adjacent: return False
            if visited[v]: return False
            return True

        def ham_path_util(pos):
            if pos == n: return True
            for v in range(n):
                if is_safe(v, pos, path):
                    path.append(v); visited[v] = True
                    if ham_path_util(pos + 1): return True
                    visited[v] = False; path.pop()
            return False

        for start_node in range(n):
            path = [start_node]; visited = [False] * n; visited[start_node] = True
            if ham_path_util(1): return True, path
        return False, []

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