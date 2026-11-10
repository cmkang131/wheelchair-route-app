// Check A* cost == Dijkstra cost on every ordered node pair of G'.
// g++ -O2 -std=c++17 cpp/allpairs.cpp -o cpp/allpairs && ./cpp/allpairs cpp/graph.txt
#define main bench_main
#include "bench.cpp"
#undef main
int main(int argc, char** argv) {
    ifstream gf(argv[1]); int m; gf >> n >> m; X.resize(n); Y.resize(n);
    for (int i = 0; i < n; i++) gf >> X[i] >> Y[i];
    vector<tuple<int,int,double>> E(m); alpha = 1.0;
    for (auto& [u, v, c] : E) gf >> u >> v >> c;
    for (auto& [u, v, c] : E) { double D = hypot(X[u] - X[v], Y[u] - Y[v]); if (D > 0) alpha = min(alpha, c / D); }
    F = build(E, false); Rv = build(E, true);
    for (int k = 0; k < 2; k++) { dist_[k].assign(n, INF); seen[k].assign(n, 0); closed_[k].assign(n, 0); heap_[k].reserve(4 * m); }
    long pairs = 0, reach = 0, nopath = 0, mism = 0, reachMism = 0; double maxdiff = 0, sumD = 0, sumA = 0;
    long expD = 0, expA = 0;
    for (int s = 0; s < n; s++) for (int t = 0; t < n; t++) if (s != t) {
        Res d = astar<false>(s, t), a = astar<true>(s, t); pairs++; expD += d.expanded; expA += a.expanded;
        bool fd = d.cost < INF, fa = a.cost < INF;
        if (fd != fa) { reachMism++; continue; }
        if (!fd) { nopath++; continue; }
        reach++; double diff = fabs(d.cost - a.cost); maxdiff = max(maxdiff, diff);
        if (diff > 1e-6) mism++; sumD += d.cost; sumA += a.cost;
    }
    printf("ordered pairs %ld\nwith route %ld\nno route %ld (both agree)\nreachability disagreements %ld\n"
           "cost mismatches (>1e-6) %ld\nmax |A*-Dijkstra| %.3g\nsum of costs: Dijkstra %.3f  A* %.3f\nnodes expanded total: Dijkstra %ld  A* %ld (%.1f%%)\n",
           pairs, reach, nopath, reachMism, mism, maxdiff, sumD, sumA, expD, expA, 100.0 * expA / expD);
}
