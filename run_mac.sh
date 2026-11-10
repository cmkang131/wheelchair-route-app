#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/python ]]; then
  echo '[1/3] Python 가상환경 생성 (최초 1회)'
  python3 -m venv .venv
fi
if ! ./.venv/bin/python -c 'import streamlit, folium, streamlit_folium, pandas' >/dev/null 2>&1; then
  echo '[2/3] 패키지 설치'
  ./.venv/bin/python -m pip install --no-cache-dir -r requirements.txt
fi
echo '[3/3] http://localhost:8502 에서 실행'
./.venv/bin/python -m streamlit run app.py --server.port 8502
