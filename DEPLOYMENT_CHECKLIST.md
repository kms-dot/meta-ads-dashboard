# 배포 체크리스트

**마지막 업데이트:** 2026-02-10

## ✅ 완료된 작업

### 백엔드 시스템
- [x] 쇼핑몰 크롤러 (네이버, 쿠팡, 올리브영)
- [x] Meta 광고 라이브러리 크롤러
- [x] Supabase 데이터베이스 연동
- [x] 키워드 자동 수집 시스템
- [x] 데이터 처리 및 분석

### 프론트엔드
- [x] Next.js 14 대시보드
- [x] Supabase 실시간 연동
- [x] 반응형 디자인
- [x] 빌드 테스트 성공

### 자동화
- [x] GitHub Actions 워크플로우
  - [x] 매일 자동 크롤링
  - [x] 월간 키워드 갱신
- [x] Git 저장소 초기화

### 데이터베이스
- [x] Supabase 스키마 생성
- [x] 연결 테스트 성공
- [x] 초기 키워드 로드 (97개)
- [x] 테이블 구조 확인

## 📋 배포 전 확인 사항

### 1. 환경 변수 확인

#### 로컬 백엔드 (`.env`)
```env
✅ SUPABASE_URL=https://ehsgxmasxekrqghxbdcm.supabase.co
✅ SUPABASE_KEY=sb_publishable_X4QKMhuO11oW1_wEA61lZQ_XRXNmKZ5
✅ LOG_LEVEL=INFO
✅ CRAWL_DELAY_MIN=3
✅ CRAWL_DELAY_MAX=7
✅ MAX_RETRY=3
✅ MAX_PRODUCTS_PER_KEYWORD=100
✅ TOP_BRANDS_COUNT=50
```

#### 로컬 프론트엔드 (`frontend/.env.local`)
```env
✅ NEXT_PUBLIC_SUPABASE_URL=https://ehsgxmasxekrqghxbdcm.supabase.co
✅ NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_X4QKMhuO11oW1_wEA61lZQ_XRXNmKZ5
```

### 2. 패키지 설치 확인

#### Python 패키지
```bash
✅ selenium 4.40.0
✅ supabase 2.27.3
✅ webdriver-manager 4.0.2
✅ python-dotenv
```

#### Node.js 패키지
```bash
✅ next 14.1.0
✅ react 18.2.0
✅ @supabase/supabase-js
✅ tailwindcss
```

### 3. 데이터베이스 상태

```
✅ ads 테이블: 1개 (테스트 데이터)
✅ keywords 테이블: 97개
✅ products 테이블: 생성됨
✅ crawl_logs 테이블: 생성됨
✅ brands 테이블: 생성됨
```

### 4. 빌드 테스트

```bash
✅ Python 모듈 임포트 성공
✅ Supabase 연결 성공
✅ Next.js 빌드 성공
✅ 프론트엔드 로컬 실행 가능
```

## 🚀 배포 단계

### Step 1: GitHub 저장소 푸시 (5분)

```bash
# 원격 저장소 연결 (GitHub에서 저장소 생성 후)
cd "C:\Users\MKM 30002\Desktop\개발(1)"
git remote add origin https://github.com/YOUR_USERNAME/meta-ads-dashboard.git
git branch -M main
git push -u origin main
```

**확인사항:**
- [ ] GitHub에 저장소 생성됨
- [ ] 코드가 정상적으로 푸시됨
- [ ] `.env` 파일이 제외되었는지 확인 (.gitignore)

### Step 2: GitHub Secrets 설정 (5분)

GitHub 저장소 > Settings > Secrets and variables > Actions

**추가할 Secrets:**
- [ ] `SUPABASE_URL`: `https://ehsgxmasxekrqghxbdcm.supabase.co`
- [ ] `SUPABASE_KEY`: `sb_publishable_X4QKMhuO11oW1_wEA61lZQ_XRXNmKZ5`

### Step 3: GitHub Actions 활성화 (자동)

저장소 푸시 후 자동으로 활성화됩니다.

**확인사항:**
- [ ] GitHub > Actions 탭에서 워크플로우 확인
- [ ] "Daily Meta Ads Crawling" 워크플로우 표시됨
- [ ] "Monthly Keyword Update" 워크플로우 표시됨

### Step 4: Vercel 배포 (10분)

#### 방법 1: Vercel CLI (추천)

```bash
cd frontend
npm install -g vercel
vercel login
vercel
```

#### 방법 2: GitHub 연동

1. https://vercel.com 접속 및 로그인
2. "New Project" 클릭
3. GitHub 저장소 연동
4. **중요:** Root Directory를 `frontend`로 설정
5. 환경 변수 추가:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
6. "Deploy" 클릭

**확인사항:**
- [ ] Vercel 프로젝트 생성됨
- [ ] 환경 변수 설정됨
- [ ] 빌드 성공
- [ ] 배포 URL 확인 (예: `https://meta-ads-dashboard.vercel.app`)

### Step 5: 첫 크롤링 실행 (수동) (15분)

#### 방법 1: 로컬에서 실행

```bash
cd "C:\Users\MKM 30002\Desktop\개발(1)"
python main_meta_db.py
```

#### 방법 2: GitHub Actions에서 실행

1. GitHub > Actions 탭
2. "Daily Meta Ads Crawling" 선택
3. "Run workflow" 클릭
4. 실행 완료 대기

**확인사항:**
- [ ] 크롤링 성공
- [ ] Supabase에 광고 데이터 저장됨
- [ ] 대시보드에서 광고 확인됨

### Step 6: 대시보드 확인 (5분)

1. Vercel 배포 URL 접속
2. 광고 표시 확인
3. 카테고리 필터 동작 확인
4. 정렬 기능 확인

**확인사항:**
- [ ] 대시보드 접속 가능
- [ ] 광고 목록 표시됨
- [ ] 필터 및 정렬 동작
- [ ] 반응형 디자인 확인

## 🧪 테스트 시나리오

### 기능 테스트

1. **크롤링 테스트**
   ```bash
   python main_meta_db.py
   ```
   - [ ] 광고 수집됨
   - [ ] DB에 저장됨
   - [ ] 중복 제거됨

2. **대시보드 테스트**
   - [ ] 로컬 실행: `cd frontend && npm run dev`
   - [ ] 프로덕션 빌드: `cd frontend && npm run build`
   - [ ] Vercel 배포 확인

3. **자동화 테스트**
   - [ ] GitHub Actions 수동 실행
   - [ ] 크롤링 로그 확인
   - [ ] 아티팩트 다운로드 확인

### 데이터 무결성 테스트

```python
# Supabase 데이터 확인
from database.supabase_client import get_supabase_client

client = get_supabase_client()

# 광고 개수 확인
ads = client.table('ads').select('*', count='exact').limit(0).execute()
print(f'Total ads: {ads.count}')

# 최근 광고 확인
recent = client.table('ads').select('*').order('collected_at', desc=True).limit(5).execute()
for ad in recent.data:
    print(f'- {ad["advertiser"]}: {ad["days_live"]} days')
```

- [ ] 광고 데이터 존재
- [ ] 중복 없음
- [ ] days_live 계산 정확

## 📊 배포 후 모니터링

### 첫 주 (Week 1)

- [ ] 매일 크롤링 실행 확인
- [ ] 데이터 품질 확인
- [ ] 오류 로그 확인
- [ ] 대시보드 접속 확인

### 첫 달 (Month 1)

- [ ] 월간 키워드 갱신 확인
- [ ] 광고 데이터 증가 추이 확인
- [ ] Vercel 사용량 확인
- [ ] GitHub Actions 사용량 확인

## 🔧 문제 해결

### 크롤링 실패

**증상:** GitHub Actions에서 크롤링 실패
**해결:**
1. Actions 탭에서 로그 확인
2. Secrets 설정 재확인
3. Supabase 연결 테스트

### 대시보드 빈 화면

**증상:** 배포된 대시보드에 광고가 표시되지 않음
**해결:**
1. Vercel 환경 변수 확인
2. Supabase에 데이터 존재 확인
3. 브라우저 콘솔 에러 확인
4. `NEXT_PUBLIC_` 접두사 확인

### GitHub Actions 타임아웃

**증상:** 1시간 후 워크플로우 자동 종료
**해결:**
1. `.github/workflows/daily_crawl.yml`에서 `timeout-minutes` 증가
2. 크롤링할 광고 수 줄이기
3. 카테고리를 나눠서 실행

## 📞 지원 및 문서

### 문서
- [README_FINAL.md](README_FINAL.md) - 전체 시스템 개요
- [README_META.md](README_META.md) - Meta 크롤러 상세
- [README_DATABASE.md](README_DATABASE.md) - 데이터베이스 스키마
- [README_AUTOMATION.md](README_AUTOMATION.md) - 자동화 가이드
- [NEXT_STEPS.md](NEXT_STEPS.md) - 다음 단계
- [STATUS.md](STATUS.md) - 현재 상태

### 유용한 링크
- Supabase: https://supabase.com/dashboard
- Vercel: https://vercel.com/dashboard
- GitHub Actions: 저장소 > Actions 탭
- Meta Ad Library: https://www.facebook.com/ads/library

## ⚠️ 보안 주의사항

1. **환경 변수 보호**
   - `.env` 파일은 절대 Git에 커밋하지 마세요
   - GitHub Secrets로만 관리
   - Vercel 환경 변수로만 관리

2. **Supabase 키**
   - 현재 사용 중인 키는 `anon/public` 키입니다
   - 서비스 키는 절대 노출하지 마세요
   - 필요시 키 재발급 가능

3. **API 제한**
   - Meta 광고 라이브러리: 과도한 요청 자제
   - 쇼핑몰: 적절한 딜레이 유지
   - GitHub Actions: 무료 플랜 제한 확인

## 🎉 배포 완료 체크

배포가 완료되면 다음을 확인하세요:

- [ ] GitHub 저장소에 코드 푸시됨
- [ ] GitHub Secrets 설정됨
- [ ] GitHub Actions 활성화됨
- [ ] Vercel 배포 성공
- [ ] 대시보드 접속 가능
- [ ] 첫 크롤링 완료
- [ ] 데이터 확인됨
- [ ] 자동화 스케줄 확인됨

**모든 항목이 체크되면 시스템이 정상 작동하고 있습니다!** 🚀

---

**다음 단계:** 일주일 동안 데이터를 모니터링하고, 필요시 키워드나 필터를 조정하세요.
