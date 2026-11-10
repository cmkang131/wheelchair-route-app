# Wheelchair Route App (PBL1)

팀 앱 설계(컴포넌트 1~6)대로 만든 실행 버전. 실제 Graph Builder 데이터(11/10 버전, 경사 포함)를 씀.

| 파일 | 역할 |
|---|---|
| data_loader.py | 1. Graph Builder CSV 읽기 |
| cost_model.py | 2. 파트1 비용 (팀 비용 모델 의사코드 그대로) |
| pathfinding.py | 3. 파트2 A*, ALT(랜드마크), 양방향 Dijkstra, 기준 Dijkstra |
| benchmark.py | 276쌍에서 Dijkstra·양방향 Dijkstra·A*·ALT 탐색 노드·시간 비교 (5회 평균) |
| app.py | 4~6. 경로 요약, 경고, 지도, 화면 |
| data/ | nodes, edges, buildings, entrances CSV |
| tests/ | 비용식 예시(100m·10%→125), A*=Dijkstra 비용 일치, h 일관성 검사 |

실행: `bash run_mac.sh` → http://localhost:8502 (그래프 빌더 8501과 안 겹치게 8502)
테스트: `python3 -m unittest discover tests`

데이터 갱신: Graph Builder에서 내보낸 nodes/edges/buildings/entrances.csv를 data/에 덮어쓰기.

가정(팀 확인 필요)
- a=5, 기준 경사 5%: 비용 모델 문서 예시(100m, 10% → 125)에서 역산. 사이드바에서 바꿀 수 있음.
- 엘리베이터·장애물 페널티 기본 0 (현재 데이터에 값이 없음).
- 경사 값이 빈 엣지는 경사 비용 0, 경고로 표시.
- 엣지가 전부 미검증(enabled=False)이라 검증 여부로는 거르지 않음. 계단·BLOCKED·통행 금지 방향만 제외.

## 웹 버전 (설치 없이 링크로)

`web/index.html`은 같은 비용식과 A*를 JavaScript로 옮긴 단일 페이지. 데이터 갱신 후 `python3 web/build.py`로 다시 만든다.
