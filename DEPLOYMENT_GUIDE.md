# Meta 광고 레퍼런스 대시보드 배포 가이드

## 🎯 완료된 개선사항

### 1. 중복 제거 로직 강화 ✅
- **기존**: 광고 ID 기준 중복 제거
- **개선**: 광고주 + 광고텍스트 + 썸네일 기준 중복 제거
- **효과**: ID가 달라도 실제 동일한 광고는 자동 제거

### 2. 페이지네이션 추가 ✅
- 카테고리당 최대 **수백~수천 개** 광고 표시 가능
- 페이지당 광고 수 선택: 20 / 50 / 100 / 200 / 500개
- 다음 페이지 / 이전 페이지 버튼

### 3. 자동 업데이트 시스템 ✅
- **매일 자정 (KST)** 자동 크롤링
- GitHub Actions 워크플로우
- 새 광고 자동 수집 및 대시보드 업데이트

### 4. URL 기반 웹 대시보드 ✅
- Streamlit 기반 인터랙티브 대시보드
- URL만 공유하면 전사 배포 완료
- 파일 다운로드 불필요

---

## 🚀 Streamlit Cloud 배포 방법

### Step 1: GitHub 저장소 준비

```bash
cd "C:\Users\MKM 30002\Desktop\개발(1)"

# Git 초기화 (아직 안 했다면)
git init
git add .
git commit -m "Initial commit: Meta Ad Dashboard"

# GitHub 저장소에 푸시
git remote add origin https://github.com/YOUR_USERNAME/meta-ad-dashboard.git
git push -u origin main
```

### Step 2: Streamlit Cloud 배포

1. **Streamlit Cloud 접속**
   - https://streamlit.io/cloud 방문
   - GitHub 계정으로 로그인

2. **New app 클릭**

3. **저장소 설정**
   - Repository: `YOUR_USERNAME/meta-ad-dashboard`
   - Branch: `main`
   - Main file path: `streamlit_dashboard.py`

4. **Deploy 클릭**

5. **배포 완료!**
   - URL 예시: `https://your-app-name.streamlit.app`
   - 이 URL을 팀에 공유

---

## 📊 대시보드 기능

### ✨ 주요 기능

1. **카테고리 필터**
   - 5개 카테고리 선택 가능
   - 각 카테고리별 광고 통계

2. **장기 게재 필터**
   - 최소 게재 일수 설정 (0~365일)
   - 기본값: 30일 이상

3. **페이지네이션**
   - 페이지당 20/50/100/200/500개 선택
   - 총 페이지 수 자동 계산
   - 현재 표시 광고 범위 표시

4. **정렬 옵션**
   - 게재 기간 긴 순
   - 게재 기간 짧은 순
   - 최근 게재일 순

5. **광고 상세 정보**
   - 광고주명
   - 광고 텍스트
   - 썸네일 이미지
   - 게재 일수
   - 노출수
   - Meta 광고 라이브러리 링크

6. **상위 광고주 차트**
   - TOP 10 광고주 시각화
   - 광고 개수 막대 그래프

---

## 🔄 자동 업데이트 설정

### GitHub Actions 워크플로우

파일: `.github/workflows/daily_crawl.yml`

**실행 시간**: 매일 자정 (KST)

**동작**:
1. 5개 카테고리 전체 크롤링
2. 중복 제거
3. GitHub에 자동 커밋
4. Streamlit Cloud 자동 재배포

**수동 실행**:
- GitHub 저장소 → Actions 탭
- "Daily Meta Ad Crawling" 선택
- "Run workflow" 클릭

---

## 📱 사용 방법

### 로컬 실행

```bash
cd "C:\Users\MKM 30002\Desktop\개발(1)"
streamlit run streamlit_dashboard.py
```

브라우저 자동 실행: http://localhost:8501

### 클라우드 접속

배포된 URL로 직접 접속:
```
https://your-app-name.streamlit.app
```

---

## 🎯 성과 측정 기준

### 장기 게재 광고 필터링

- **30일 이상**: 안정적인 성과 광고
- **60일 이상**: 고성과 광고 (🏆 표시)
- **노출수 "적음"**: 자동 제외
- **종료된 광고**: 자동 제외

---

## 🛠 트러블슈팅

### 대시보드가 안 보일 때

1. **로컬 서버 재시작**
   ```bash
   Ctrl + C (기존 서버 종료)
   streamlit run streamlit_dashboard.py
   ```

2. **캐시 삭제**
   - 대시보드에서 `C` 키 누르기
   - 또는 우측 상단 ⋮ → "Clear cache"

3. **데이터 파일 확인**
   ```bash
   ls meta_output/meta_all_categories*.json
   ```

### Streamlit Cloud 배포 실패

1. **requirements.txt 확인**
   - 모든 패키지가 포함되어 있는지 확인

2. **로그 확인**
   - Streamlit Cloud 대시보드 → Manage app → Logs

3. **데이터 파일 경로**
   - `meta_output/` 폴더가 GitHub에 포함되어 있는지 확인

---

## 📊 현재 통계 (2026-02-11 기준)

- **총 광고**: 2,559개
- **고유 광고주**: 1,162개
- **카테고리**: 5개
- **평균 게재 기간**: 80일

### 카테고리별

| 카테고리 | 광고 수 | 광고주 |
|---------|--------|--------|
| 건강기능식품 | 944개 | 362개 |
| 뷰티디바이스 | 517개 | 238개 |
| 스킨케어 | 419개 | 237개 |
| 헤어케어 | 409개 | 167개 |
| 생활용품 | 270개 | 158개 |

---

## 📞 지원

문의사항이 있으시면 GitHub Issues로 남겨주세요.
