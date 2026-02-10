# GitHub Actions 자동화 가이드

Meta 광고 크롤링 및 키워드 업데이트를 GitHub Actions로 자동화하는 시스템입니다.

## 목차

1. [자동화 워크플로우 개요](#자동화-워크플로우-개요)
2. [설정 방법](#설정-방법)
3. [워크플로우 상세](#워크플로우-상세)
4. [수동 실행](#수동-실행)
5. [모니터링 및 알림](#모니터링-및-알림)
6. [문제 해결](#문제-해결)

## 자동화 워크플로우 개요

### 1. 매일 자동 크롤링 (daily_crawl.yml)

**실행 시간:** 매일 오전 12시 (KST)

**작업 내용:**
1. Meta 광고 라이브러리 크롤링
2. 수집된 광고 Supabase DB에 저장
3. 90일 이상 된 광고 자동 비활성화
4. 크롤링 결과 아티팩트로 저장

**예상 소요 시간:** 30-60분

### 2. 월간 키워드 갱신 (monthly_keywords.yml)

**실행 시간:** 매월 1일 오전 9시 (KST)

**작업 내용:**
1. 쇼핑몰(네이버, 쿠팡, 올리브영)에서 제품 크롤링
2. 상위 브랜드 추출
3. 추출된 브랜드를 DB에 키워드로 저장
4. 브랜드 통계 갱신

**예상 소요 시간:** 60-120분

## 설정 방법

### 1. GitHub Secrets 설정

GitHub 저장소에 Supabase 인증 정보를 Secrets로 추가해야 합니다.

1. GitHub 저장소 > **Settings** > **Secrets and variables** > **Actions**
2. **New repository secret** 클릭
3. 다음 Secrets 추가:

| Name | Value | 설명 |
|------|-------|------|
| `SUPABASE_URL` | `https://your-project.supabase.co` | Supabase 프로젝트 URL |
| `SUPABASE_KEY` | `your-anon-key-here` | Supabase Anon Key |

**Supabase 정보 확인 방법:**
- Supabase 대시보드 > Settings > API
- Project URL → `SUPABASE_URL`
- Project API keys > `anon` `public` → `SUPABASE_KEY`

### 2. 워크플로우 활성화

1. `.github/workflows/` 디렉토리에 워크플로우 파일 확인
2. GitHub 저장소에 푸시:

```bash
git add .github/workflows/
git commit -m "Add GitHub Actions workflows"
git push origin main
```

3. GitHub 저장소 > **Actions** 탭에서 워크플로우 확인

### 3. 초기 실행 테스트

워크플로우가 제대로 작동하는지 수동으로 테스트:

1. GitHub 저장소 > **Actions** 탭
2. 워크플로우 선택 (예: "Daily Meta Ads Crawling")
3. **Run workflow** 버튼 클릭
4. 실행 결과 확인

## 워크플로우 상세

### Daily Meta Ads Crawling

#### 워크플로우 구조

```yaml
jobs:
  crawl-meta-ads:
    # Meta 광고 크롤링
    - Chrome/ChromeDriver 설치
    - Python 환경 설정
    - 크롤링 실행
    - 결과 업로드

  cleanup-old-ads:
    # 오래된 광고 정리
    - 90일 이상 광고 비활성화
```

#### 실행 로그 예시

```
✓ Checkout repository
✓ Set up Python 3.10
✓ Install Python dependencies
✓ Install Chrome and ChromeDriver
✓ Run Meta Ads Crawler
  - 뷰티디바이스: 50개 광고 수집
  - 건강기능식품: 45개 광고 수집
✓ Upload crawling results
✓ Deactivate old ads (15개 비활성화)
```

#### 결과 아티팩트

크롤링 결과는 GitHub Actions 아티팩트로 저장됩니다:

- `crawl-results-{실행번호}.zip`
  - `meta_output/*.json` - 크롤링 데이터
  - `meta_output/*.log` - 실행 로그
  - **보관 기간:** 30일

**다운로드 방법:**
1. GitHub 저장소 > Actions > 실행 기록 선택
2. 하단 **Artifacts** 섹션에서 다운로드

### Monthly Keyword Update

#### 워크플로우 구조

```yaml
jobs:
  update-keywords:
    # 키워드 수집 및 업데이트
    - 쇼핑몰 크롤링
    - 브랜드 추출
    - DB에 저장

  refresh-brand-stats:
    # 브랜드 통계 갱신
    - SQL 함수 실행
```

#### 실행 로그 예시

```
✓ Crawl e-commerce for brand keywords
  - 뷰티디바이스: 네이버 쇼핑 크롤링... 200개 제품
  - 뷰티디바이스: 쿠팡 크롤링... 150개 제품
  - 상위 50개 브랜드 추출
✓ Update keywords in database
  - 뷰티디바이스: 50개 키워드 저장
✓ Refresh brand statistics
```

#### 결과 아티팩트

- `keyword-update-{실행번호}.zip`
  - `output/extracted_brands.json` - 추출된 브랜드
  - `logs/*.log` - 실행 로그
  - **보관 기간:** 90일

## 수동 실행

### Daily Meta Ads Crawling 수동 실행

1. GitHub 저장소 > **Actions** > **Daily Meta Ads Crawling**
2. **Run workflow** 클릭
3. 옵션 설정 (선택사항):
   - **category**: 특정 카테고리만 크롤링 (예: `뷰티디바이스`)
   - **max_ads**: 수집할 최대 광고 수 (기본값: 100)
4. **Run workflow** 확인

### Monthly Keyword Update 수동 실행

1. GitHub 저장소 > **Actions** > **Monthly Keyword Update**
2. **Run workflow** 클릭
3. 옵션 설정 (선택사항):
   - **categories**: 업데이트할 카테고리 (예: `뷰티디바이스,스킨케어`)
   - **top_brands_count**: 추출할 상위 브랜드 수 (기본값: 50)
4. **Run workflow** 확인

## 모니터링 및 알림

### 1. GitHub Actions 대시보드

**실행 상태 확인:**
- GitHub 저장소 > **Actions** 탭
- 각 워크플로우의 실행 기록 및 상태 확인

**상태 종류:**
- ✅ **Success**: 성공
- ❌ **Failure**: 실패
- ⏸️ **Cancelled**: 취소됨
- 🔄 **In Progress**: 실행 중

### 2. 이메일 알림

GitHub는 워크플로우 실패 시 자동으로 이메일 알림을 보냅니다.

**알림 설정:**
1. GitHub 프로필 > **Settings** > **Notifications**
2. **Actions** 섹션에서 알림 활성화

### 3. Slack/Discord 알림 (선택사항)

워크플로우 파일에 웹훅 추가:

```yaml
# .github/workflows/daily_crawl.yml

- name: Notify on success
  if: success()
  run: |
    curl -X POST -H 'Content-type: application/json' \
      --data '{"text":"✅ Meta ads crawling completed!"}' \
      ${{ secrets.SLACK_WEBHOOK_URL }}

- name: Notify on failure
  if: failure()
  run: |
    curl -X POST -H 'Content-type: application/json' \
      --data '{"text":"❌ Meta ads crawling failed!"}' \
      ${{ secrets.SLACK_WEBHOOK_URL }}
```

**Slack 웹훅 설정:**
1. Slack 워크스페이스 > Apps > Incoming Webhooks
2. 웹훅 URL 생성
3. GitHub Secrets에 `SLACK_WEBHOOK_URL` 추가

## 크롤링 스케줄 커스터마이징

### Cron 표현식 이해

GitHub Actions는 UTC 시간 기준으로 작동합니다. **KST = UTC + 9시간**

```yaml
# 형식: 분 시 일 월 요일
on:
  schedule:
    - cron: '0 15 * * *'  # UTC 15:00 = KST 00:00 (다음날)
```

#### 자주 사용하는 스케줄

| 설명 | Cron 표현식 | UTC 시간 | KST 시간 |
|------|-------------|----------|----------|
| 매일 자정 (KST) | `0 15 * * *` | 15:00 | 00:00 (다음날) |
| 매일 오전 9시 (KST) | `0 0 * * *` | 00:00 | 09:00 |
| 매일 오후 6시 (KST) | `0 9 * * *` | 09:00 | 18:00 |
| 매주 월요일 오전 9시 | `0 0 * * 1` | 00:00 월요일 | 09:00 월요일 |
| 매월 1일 오전 9시 | `0 0 1 * *` | 00:00 1일 | 09:00 1일 |

#### 스케줄 변경 방법

1. `.github/workflows/daily_crawl.yml` 파일 열기
2. `cron` 값 수정:

```yaml
on:
  schedule:
    - cron: '0 9 * * *'  # UTC 09:00 = KST 18:00 (매일 저녁 6시)
```

3. 변경사항 커밋 및 푸시

## 문제 해결

### 1. 워크플로우 실행 실패

**증상:** ❌ Failure 상태

**해결 방법:**
1. Actions 탭 > 실패한 실행 클릭
2. 각 단계의 로그 확인
3. 오류 메시지 확인

**일반적인 원인:**
- Supabase Secrets 미설정 또는 잘못된 값
- Python 패키지 설치 실패
- Chrome/ChromeDriver 버전 불일치
- 크롤링 대상 사이트 구조 변경

### 2. Supabase 연결 오류

**증상:** `ValueError: Supabase 환경 변수가 설정되지 않았습니다`

**해결:**
1. GitHub Secrets 확인:
   - `SUPABASE_URL` 올바른지 확인
   - `SUPABASE_KEY` 올바른지 확인
2. Supabase 프로젝트가 활성 상태인지 확인

### 3. Chrome/ChromeDriver 오류

**증상:** `SessionNotCreatedException`

**해결:**
워크플로우 파일에서 Chrome 설치 방법 업데이트:

```yaml
- name: Install Chrome and ChromeDriver
  run: |
    # 최신 버전 설치
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
    sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
    sudo apt-get update
    sudo apt-get install -y google-chrome-stable
```

### 4. 크롤링 타임아웃

**증상:** 워크플로우가 1시간 후 자동 종료

**해결:**
타임아웃 시간 증가:

```yaml
jobs:
  crawl-meta-ads:
    timeout-minutes: 120  # 60 -> 120으로 증가
```

### 5. 메모리 부족

**증상:** `MemoryError` 또는 `Killed`

**해결:**
- 한 번에 수집하는 광고 수 줄이기
- 카테고리를 나눠서 실행

```yaml
# 수동 실행 시 max_ads 줄이기
max_ads: 50  # 100 -> 50
```

## GitHub Actions 사용량 제한

### 무료 플랜 제한

- **Public 저장소**: 무제한
- **Private 저장소**: 월 2,000분

### 사용량 확인

1. GitHub 프로필 > **Settings** > **Billing**
2. **Actions** 섹션에서 사용량 확인

### 비용 절감 팁

1. **헤드리스 모드 활성화**
   - Chrome을 헤드리스로 실행하여 속도 향상

2. **캐시 활용**
   ```yaml
   - uses: actions/setup-python@v5
     with:
       cache: 'pip'  # pip 캐시 활성화
   ```

3. **조건부 실행**
   ```yaml
   # 특정 조건에서만 실행
   if: github.event_name == 'schedule' && github.ref == 'refs/heads/main'
   ```

4. **아티팩트 보관 기간 조정**
   ```yaml
   retention-days: 7  # 30 -> 7일로 줄이기
   ```

## 고급 설정

### 1. 여러 카테고리 병렬 실행

```yaml
strategy:
  matrix:
    category: ['뷰티디바이스', '건강기능식품', '스킨케어']

steps:
  - name: Crawl ${{ matrix.category }}
    run: |
      python main_meta_db.py --category ${{ matrix.category }}
```

### 2. 실행 결과 Slack 알림

```yaml
- name: Slack notification
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'Meta ads crawling completed!'
    webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
  if: always()
```

### 3. 크롤링 결과 자동 커밋

```yaml
- name: Commit results
  run: |
    git config user.name "GitHub Actions"
    git config user.email "actions@github.com"
    git add output/
    git commit -m "Update crawl results [skip ci]"
    git push
```

## 라이선스

MIT License
