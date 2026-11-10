// Dijkstra vs A* vs bidirectional Dijkstra on G' (exported by export_graph.py).
// Per-query fixed costs removed: CSR arrays, int node ids, timestamped arrays
// (no clearing between queries), reused heaps. h = alpha * planar distance.
// g++ -O2 -std=c++17 cpp/bench.cpp -o cpp/bench && ./cpp/bench cpp/graph.txt cpp/pairs.txt > cpp/results.csv
#include <bits/stdc++.h>
using namespace std;
using P = pair<double, int>;
const double INF = 1e300;

struct CSR { vector<int> off, to; vector<double> w; };
int n; vector<double> X, Y; CSR F, Rv; double alpha;
vector<double> dist_[2]; vector<unsigned> seen[2], closed_[2]; unsigned cur = 0;
vector<P> heap_[2];

CSR build(const vector<tuple<int,int,double>>& E, bool rev) {
    CSR g; g.off.assign(n + 1, 0);
    for (auto& [u, v, c] : E) g.off[(rev ? v : u) + 1]++;
    for (int i = 0; i < n; i++) g.off[i + 1] += g.off[i];
    g.to.resize(E.size()); g.w.resize(E.size()); vector<int> pos(g.off.begin(), g.off.end() - 1);
    for (auto& [u, v, c] : E) { int a = rev ? v : u, b = rev ? u : v; g.to[pos[a]] = b; g.w[pos[a]++] = c; }
    return g;
}
inline void hpush(vector<P>& h, double k, int v) { h.push_back({k, v}); push_heap(h.begin(), h.end(), greater<P>()); }
inline P hpop(vector<P>& h) { pop_heap(h.begin(), h.end(), greater<P>()); P x = h.back(); h.pop_back(); return x; }

struct Res { double cost; int expanded; };

template <bool UseH> Res astar(int s, int t) {
    ++cur; auto& d = dist_[0]; auto& sn = seen[0]; auto& cl = closed_[0]; auto& h = heap_[0]; h.clear();
    double tx = X[t], ty = Y[t];
    auto H = [&](int v) { if (!UseH) return 0.0; double dx = X[v] - tx, dy = Y[v] - ty; return alpha * sqrt(dx * dx + dy * dy); };
    d[s] = 0; sn[s] = cur; hpush(h, H(s), s); int ex = 0;
    while (!h.empty()) {
        int u = hpop(h).second;
        if (cl[u] == cur) continue;
        cl[u] = cur; ex++;
        if (u == t) return {d[t], ex};
        double du = d[u];
        for (int i = F.off[u]; i < F.off[u + 1]; i++) {
            int v = F.to[i]; double nd = du + F.w[i];
            if (sn[v] != cur || nd < d[v]) { d[v] = nd; sn[v] = cur; hpush(h, nd + H(v), v); }
        }
    }
    return {INF, ex};
}

Res bidi(int s, int t) {
    ++cur; heap_[0].clear(); heap_[1].clear();
    dist_[0][s] = 0; seen[0][s] = cur; hpush(heap_[0], 0, s);
    dist_[1][t] = 0; seen[1][t] = cur; hpush(heap_[1], 0, t);
    double mu = INF; int ex = 0;
    while (!heap_[0].empty() && !heap_[1].empty()) {
        double a = heap_[0].front().first, b = heap_[1].front().first;
        if (a + b >= mu) break;
        int sd = a <= b ? 0 : 1;
        auto [du, u] = hpop(heap_[sd]);
        if (closed_[sd][u] == cur) continue;
        closed_[sd][u] = cur; ex++;
        const CSR& g = sd ? Rv : F; auto& d = dist_[sd]; auto& sn = seen[sd];
        auto& od = dist_[1 - sd]; auto& os = seen[1 - sd];
        for (int i = g.off[u]; i < g.off[u + 1]; i++) {
            int v = g.to[i]; double nd = du + g.w[i];
            if (sn[v] != cur || nd < d[v]) { d[v] = nd; sn[v] = cur; hpush(heap_[sd], nd, v); }
            if (os[v] == cur && nd + od[v] < mu) mu = nd + od[v];
        }
    }
    return {mu, ex};
}

int main(int argc, char** argv) {
    ifstream gf(argv[1]); int m; gf >> n >> m; X.resize(n); Y.resize(n);
    for (int i = 0; i < n; i++) gf >> X[i] >> Y[i];
    vector<tuple<int,int,double>> E(m); alpha = 1.0;
    for (auto& [u, v, c] : E) gf >> u >> v >> c;
    for (auto& [u, v, c] : E) { double D = hypot(X[u] - X[v], Y[u] - Y[v]); if (D > 0) alpha = min(alpha, c / D); }
    F = build(E, false); Rv = build(E, true);
    for (int k = 0; k < 2; k++) { dist_[k].assign(n, INF); seen[k].assign(n, 0); closed_[k].assign(n, 0); heap_[k].reserve(4 * m); }
    ifstream pf(argv[2]); int q; pf >> q;
    const int REPS = 30;
    printf("group,s,t,algo,cost,expanded,ns\n");
    fprintf(stderr, "alpha %.6f\n", alpha);
    const char* names[3] = {"Dijkstra", "A*", "Bidirectional"};
    for (int k = 0; k < q; k++) {
        string grp; int s, t; pf >> grp >> s >> t;
        Res r[3]; double best[3] = {INF, INF, INF};
        for (int rep = 0; rep < REPS; rep++)
            for (int j = 0; j < 3; j++) {
                int a = (j + rep + k) % 3;                          // rotate order
                auto t0 = chrono::steady_clock::now();
                Res x = a == 0 ? astar<false>(s, t) : a == 1 ? astar<true>(s, t) : bidi(s, t);
                double ns = chrono::duration<double, nano>(chrono::steady_clock::now() - t0).count();
                r[a] = x; best[a] = min(best[a], ns);
            }
        for (int a = 0; a < 3; a++)
            printf("%s,%d,%d,%s,%.6f,%d,%.0f\n", grp.c_str(), s, t, names[a], r[a].cost >= INF ? -1.0 : r[a].cost, r[a].expanded, best[a]);
    }
}
