# Meta 광고 레퍼런스 대시보드 배포 가이드

## 🚀 Streamlit Cloud 배포 (추천)

### 1단계: GitHub에 푸시

```bash
cd "C:\Users\MKM 30002\Desktop\개발(1)"
git add .
git commit -m "Add Streamlit dashboard for deployment"
git push origin main
```

### 2단계: Streamlit Cloud 배포

1. **Streamlit Cloud 접속**
   - https://share.streamlit.io/ 방문
   - GitHub 계정으로 로그인

2. **New app 클릭**
   - Repository: `kms-dot/meta-ads-dashboard`
   - Branch: `main`
   - Main file path: `streamlit_dashboard.py`

3. **배포 시작**
   - Deploy 버튼 클릭
   - 약 2-3분 후 배포 완료

4. **URL 공유**
   - 배포 완료 시 고유 URL 생성 (예: https://meta-ads-dashboard.streamlit.app)
   - 이 URL을 상부에 공유

---

## 📊 로컬 테스트 (다른 PC에서)

다른 PC에서 로컬로 실행하려면:

```bash
# 1. 저장소 클론
git clone https://github.com/kms-dot/meta-ads-dashboard.git
cd meta-ads-dashboard

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 대시보드 실행
streamlit run streamlit_dashboard.py
```

브라우저에서 http://localhost:8501 접속

---

## 🔧 필수 파일 체크리스트

배포에 필요한 파일들:
- ✅ `streamlit_dashboard.py` - 메인 대시보드
- ✅ `requirements.txt` - Python 패키지 목록
- ✅ `.streamlit/config.toml` - Streamlit 설정
- ✅ `meta_output/meta_all_categories_filtered_*.json` - 데이터 파일

---

## 💡 주의사항

1. **데이터 파일 크기**
   - GitHub 파일 크기 제한: 100MB
   - 현재 데이터 파일이 100MB 초과 시 Git LFS 사용 필요

2. **자동 업데이트**
   - GitHub Actions 워크플로우가 매일 자정에 크롤링 실행
   - 새 데이터는 자동으로 커밋되어 대시보드에 반영

3. **캐시 관리**
   - Streamlit은 1시간 캐시 사용
   - 강제 새로고침: 브라우저에서 Ctrl+F5

---

## 🌐 배포 후 확인사항

- [ ] URL 접속 확인
- [ ] 5개 카테고리 데이터 로드 확인
- [ ] 필터링 기능 작동 확인
- [ ] 페이지네이션 작동 확인
- [ ] 이미지 표시 확인
- [ ] 광고 링크 클릭 확인

---

## 📞 문제 해결

### 데이터 로드 실패
→ `meta_output` 폴더에 필터링된 JSON 파일이 있는지 확인

### 이미지 표시 안 됨
→ 브라우저 캐시 삭제 후 재접속

### 배포 실패
→ requirements.txt의 패키지 버전 확인
