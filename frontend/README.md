# META 광고 레퍼런스 대시보드

Next.js 14 + TypeScript + Tailwind CSS로 구축된 Meta 광고 레퍼런스 대시보드입니다.

## 주요 기능

- ✅ **카테고리별 필터링**: 5개 카테고리 (뷰티디바이스, 스킨케어, 헤어케어, 생활용품, 건강기능식품)
- ✅ **광고 카드 디스플레이**: 썸네일/비디오, 광고주, 라이브 일수, 카테고리 태그
- ✅ **정렬 기능**: 라이브 일수순 / 최신순
- ✅ **실시간 통계**: 총 광고 수, 광고주 수, 평균 라이브 일수, 미디어 타입 분포
- ✅ **반응형 디자인**: 모바일, 태블릿, 데스크톱 지원
- ✅ **Meta 광고 라이브러리 직접 연결**: 클릭 시 원본 광고로 이동

## 기술 스택

- **Frontend**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Database**: Supabase
- **Deployment**: Vercel

## 시작하기

### 1. 환경 변수 설정

`.env.local` 파일 생성:

```bash
cp .env.local.example .env.local
```

환경 변수 입력:

```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 2. 의존성 설치

```bash
npm install
```

### 3. 개발 서버 실행

```bash
npm run dev
```

브라우저에서 [http://localhost:3000](http://localhost:3000) 열기

### 4. 프로덕션 빌드

```bash
npm run build
npm start
```

## 프로젝트 구조

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx        # 레이아웃
│   │   ├── page.tsx          # 메인 대시보드
│   │   └── globals.css       # 글로벌 스타일
│   ├── components/
│   │   └── AdCard.tsx        # 광고 카드 컴포넌트
│   └── lib/
│       └── supabase.ts       # Supabase 클라이언트 & 타입
├── public/                   # 정적 파일
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## 주요 컴포넌트

### AdCard

광고 카드 컴포넌트 - 개별 광고 표시

**Props:**
```typescript
interface AdCardProps {
  ad: Ad;
}
```

**기능:**
- 썸네일/비디오 표시
- 라이브 일수 배지
- 광고주명
- 카테고리 태그
- 플랫폼 아이콘 (Facebook, Instagram, Messenger)
- Meta 광고 라이브러리 링크

### Dashboard (page.tsx)

메인 대시보드 페이지

**기능:**
- 카테고리 필터
- 정렬 옵션 (라이브 일수순/최신순)
- 실시간 통계
- 광고 그리드 레이아웃
- 무한 스크롤 (향후 추가 가능)

## Supabase 연동

### 데이터 페칭

```typescript
// 활성 광고 조회
const { data, error } = await supabase
  .from('ads')
  .select('*')
  .eq('is_active', true)
  .order('days_live', { ascending: false })
  .limit(100);
```

### 타입 정의

```typescript
export interface Ad {
  id: string;
  category: string;
  advertiser: string;
  thumbnail_url: string | null;
  video_url: string | null;
  ad_library_url: string;
  days_live: number;
  is_active: boolean;
  // ... 기타 필드
}
```

## Vercel 배포

### 1. Vercel CLI 설치

```bash
npm install -g vercel
```

### 2. 로그인

```bash
vercel login
```

### 3. 배포

```bash
vercel
```

### 4. 환경 변수 설정

Vercel 대시보드에서:

1. 프로젝트 선택 > **Settings** > **Environment Variables**
2. 다음 변수 추가:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### 5. 프로덕션 배포

```bash
vercel --prod
```

## 자동 배포 (GitHub 연동)

### 1. GitHub 저장소 연결

1. Vercel 대시보드 > **Add New** > **Project**
2. GitHub 저장소 선택
3. 환경 변수 설정
4. **Deploy** 클릭

### 2. 자동 배포 설정

- **main 브랜치 푸시** → 프로덕션 배포
- **다른 브랜치 푸시** → 프리뷰 배포

## 성능 최적화

### 이미지 최적화

Next.js Image 컴포넌트 사용 (향후 개선):

```typescript
import Image from 'next/image';

<Image
  src={ad.thumbnail_url!}
  alt={ad.advertiser}
  width={400}
  height={400}
  className="object-cover"
/>
```

### 데이터 캐싱

React Query 사용 (향후 개선):

```typescript
import { useQuery } from '@tanstack/react-query';

const { data: ads } = useQuery({
  queryKey: ['ads', selectedCategory],
  queryFn: fetchAds,
  staleTime: 5 * 60 * 1000, // 5분
});
```

### 무한 스크롤

Intersection Observer 사용:

```typescript
const { ref, inView } = useInView();

useEffect(() => {
  if (inView) {
    loadMore();
  }
}, [inView]);
```

## 트러블슈팅

### Supabase 연결 오류

**증상:** `Missing Supabase environment variables`

**해결:**
1. `.env.local` 파일 확인
2. 환경 변수 이름 확인 (`NEXT_PUBLIC_` 접두사 필수)
3. 개발 서버 재시작

### 이미지 로딩 오류

**증상:** 이미지가 표시되지 않음

**해결:**
1. `next.config.js`에서 `remotePatterns` 확인
2. 이미지 URL이 HTTPS인지 확인
3. CORS 설정 확인

### 빌드 오류

**증상:** TypeScript 타입 오류

**해결:**
```bash
# 타입 체크
npm run build

# 타입 오류 무시 (임시)
# next.config.js에 추가:
typescript: {
  ignoreBuildErrors: true,
}
```

## 향후 개선 사항

- [ ] 무한 스크롤
- [ ] 검색 기능 (광고주명, 광고 텍스트)
- [ ] 필터 조합 (미디어 타입, 플랫폼, 라이브 일수 범위)
- [ ] 광고 상세 페이지
- [ ] 즐겨찾기 기능
- [ ] 다크 모드
- [ ] 광고 비교 기능
- [ ] 내보내기 (Excel, CSV)

## 라이선스

MIT License
