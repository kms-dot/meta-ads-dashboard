# 다음 단계 가이드

## ✅ 완료된 작업

1. **프로젝트 구조 완성**
   - 쇼핑몰 크롤러 (네이버, 쿠팡, 올리브영)
   - Meta 광고 라이브러리 크롤러
   - Supabase 데이터베이스 연동
   - Next.js 대시보드
   - GitHub Actions 자동화

2. **초기 설정 완료**
   - Git 저장소 초기화 ✓
   - Supabase 연결 테스트 ✓
   - 키워드 초기 데이터 로드 ✓
   - 프론트엔드 빌드 성공 ✓

## 🚀 다음에 해야 할 일

### 1. GitHub 저장소 생성 및 연동

```bash
# GitHub에서 새 저장소 생성 후
cd "C:\Users\MKM 30002\Desktop\개발(1)"
git remote add origin https://github.com/YOUR_USERNAME/meta-ads-dashboard.git
git branch -M main
git push -u origin main
```

### 2. GitHub Secrets 설정

GitHub 저장소 > Settings > Secrets and variables > Actions에서 추가:

- `SUPABASE_URL`: https://ehsgxmasxekrqghxbdcm.supabase.co
- `SUPABASE_KEY`: (현재 .env 파일의 값)

### 3. Meta 크롤러 첫 실행

```bash
# 한 카테고리로 테스트
python main_meta_db.py
```

**주의사항:**
- 크롬 브라우저가 열립니다
- 첫 실행은 5-10분 소요됩니다
- 광고 데이터가 Supabase에 저장됩니다

### 4. 프론트엔드 로컬 테스트

```bash
cd frontend
npm run dev
```

브라우저에서 http://localhost:3000 접속하여 대시보드 확인

### 5. Vercel 배포

#### 방법 1: Vercel CLI (추천)

```bash
cd frontend
npm install -g vercel
vercel login
vercel
```

#### 방법 2: GitHub 연동

1. https://vercel.com 접속
2. "New Project" 클릭
3. GitHub 저장소 연동
4. `frontend` 디렉토리를 Root Directory로 설정
5. 환경 변수 추가:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
6. Deploy 클릭

### 6. GitHub Actions 활성화

저장소에 푸시 후 자동으로 활성화됩니다:

- **매일 00:00 (KST)**: Meta 광고 크롤링
- **매월 1일 09:00 (KST)**: 키워드 갱신

수동 실행 방법:
1. GitHub > Actions 탭
2. 원하는 워크플로우 선택
3. "Run workflow" 클릭

## 📊 시스템 작동 확인

### 데이터베이스 확인

```python
python -c "
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
from database.supabase_client import get_supabase_client

client = get_supabase_client()

# 광고 개수 확인
ads = client.table('ads').select('*', count='exact').limit(0).execute()
print(f'Total ads: {ads.count}')

# 키워드 개수 확인
keywords = client.table('keywords').select('*', count='exact').limit(0).execute()
print(f'Total keywords: {keywords.count}')

# 최근 광고 5개 확인
recent_ads = client.table('ads').select('*').order('collected_at', desc=True).limit(5).execute()
for ad in recent_ads.data:
    print(f'- {ad[\"advertiser\"]}: {ad[\"days_live\"]} days live')
"
```

### 크롤링 이력 확인

```python
python -c "
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'
from database.supabase_client import get_supabase_client

client = get_supabase_client()

logs = client.table('crawl_logs').select('*').order('started_at', desc=True).limit(10).execute()
for log in logs.data:
    print(f'{log[\"crawl_type\"]} | {log[\"category\"]} | {log[\"status\"]} | {log[\"items_collected\"]} items')
"
```

## 🔧 문제 해결

### Python 의존성 설치

```bash
pip install -r requirements.txt
```

### Chrome Driver 설치 (자동)

첫 실행 시 webdriver-manager가 자동으로 설치합니다.

### Supabase 연결 오류

`.env` 파일 확인:
```env
SUPABASE_URL=https://ehsgxmasxekrqghxbdcm.supabase.co
SUPABASE_KEY=sb_publishable_X4QKMhuO11oW1_wEA61lZQ_XRXNmKZ5
```

### 프론트엔드 빌드 오류

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

## 📈 성능 최적화

### 1. 키워드 우선순위 설정

더 나은 결과를 위해 키워드 우선순위를 조정할 수 있습니다:

```python
from database import KeywordRepository

repo = KeywordRepository()

# 특정 키워드 우선순위 상승
repo.supabase.table('keywords').update({
    'search_priority': 10
}).eq('keyword', '라로슈포제').execute()
```

### 2. 크롤링 주기 조정

`.github/workflows/daily_crawl.yml`:
```yaml
schedule:
  - cron: '0 15 * * *'  # 매일 00:00 KST (UTC+9)
```

### 3. 광고 필터 조정

`config/meta_selectors.json`에서 필터 조건 변경 가능

## 🎯 다음 개선 사항

1. **광고 품질 점수**: 게재 일수, 플랫폼 수, 미디어 타입 기반
2. **트렌드 분석**: 카테고리별 신규 광고 트렌드
3. **이메일 알림**: 새로운 장기 라이브 광고 발견 시
4. **대시보드 강화**:
   - 검색 기능
   - 날짜 필터
   - 광고주별 필터
   - 미디어 타입별 필터

## 📞 지원

문제가 발생하면 다음을 확인하세요:

1. `README_FINAL.md` - 전체 시스템 개요
2. `README_META.md` - Meta 크롤러 세부사항
3. `README_DATABASE.md` - 데이터베이스 스키마
4. `README_AUTOMATION.md` - GitHub Actions 설정

---

**시스템이 준비되었습니다! 위 단계를 따라 배포하세요.** 🚀
