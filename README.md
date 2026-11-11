# Wheelchair Route App (Demo)

POSTECH 캠퍼스 그래프에서 계단 없이 갈 수 있는 최소 비용 경로를 A*로 찾는 데모 앱입니다. 알고리즘(CSED331) PBL1 결과물입니다.

앱: https://wheelchair-route-app-ewdgvkeyemissppjwg4t9p.streamlit.app/

## 비용

간선 비용 = 거리 + 거리 × a × max(0, 경사 − 기준 경사)

계단, 통행 불가 간선, 금지 방향은 그래프에서 뺍니다. 기본값은 a = 5, 기준 경사 5%이고, 앱 사이드바에서 바꿀 수 있습니다.

## 결과

- 모든 노드 쌍 510,510개에서 A*와 Dijkstra의 경로 비용이 같습니다.
- 경로가 있는 랜덤 26,552쌍(C++)에서 A*는 노드를 40%만 탐색하고, 평균 5.9μs로 Dijkstra(10.5μs)보다 빠릅니다. A*가 더 빠른 쌍은 96%입니다.
- 건물 113쌍은 거리 기준 최단 경로가 계단을 지나고, 계단을 피하면 평균 178m 돌아갑니다.

## 파일

| 파일 | 내용 |
|---|---|
| app.py | Streamlit 화면 (경로 요약, 경고, 지도, A* vs Dijkstra) |
| data_loader.py | Graph Builder CSV 읽기 |
| cost_model.py | 간선 비용 계산 |
| pathfinding.py | A*, Dijkstra (비교용으로 ALT, 양방향 Dijkstra도 있음) |
| check_all_pairs.py | 모든 노드 쌍에서 A*와 Dijkstra 비용 비교 |
| benchmark_wide.py | 랜덤 쌍 속도 비교 (Python) |
| cpp/ | 같은 비교의 C++ 버전과 결과 |
| tests/ | 비용식, A* = Dijkstra, 휴리스틱 일관성 테스트 |
| data/ | nodes, edges, buildings, entrances CSV |

## 한계

- 간선이 아직 검수되지 않았습니다(enabled=False). 지금은 계단과 통행 불가만 빼고 씁니다.
- a = 5, 기준 경사 5%는 비용 모델 문서의 예시(100m, 10% → 125)에서 역산한 가정입니다.
- 경사 값이 없는 간선은 경사 비용을 0으로 두고 경고를 띄웁니다.
