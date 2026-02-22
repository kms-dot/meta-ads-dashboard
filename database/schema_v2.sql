-- ============================================================
-- schema_v2.sql  — Instagram 성과 데이터 컬럼 추가
-- ============================================================
-- 기존 ads 테이블에 ALTER TABLE 로 컬럼 추가 (데이터 보존)
-- Supabase SQL Editor 또는 psql 에서 실행하세요.
-- ============================================================

-- 1) Instagram 원본 URL
ALTER TABLE ads
  ADD COLUMN IF NOT EXISTS instagram_url VARCHAR(500);

-- 2) Instagram 조회수 (릴스/비디오 재생 수)
ALTER TABLE ads
  ADD COLUMN IF NOT EXISTS instagram_views INTEGER DEFAULT 0;

-- 3) Instagram 좋아요 수
ALTER TABLE ads
  ADD COLUMN IF NOT EXISTS instagram_likes INTEGER DEFAULT 0;

-- 4) Instagram 댓글 수
ALTER TABLE ads
  ADD COLUMN IF NOT EXISTS instagram_comments INTEGER DEFAULT 0;

-- 5) 포스트 게시일
ALTER TABLE ads
  ADD COLUMN IF NOT EXISTS post_date DATE;

-- 6) CTA 포함 여부
--    (캡션에 URL·행동유도 문구·쇼핑태그 포함 시 TRUE)
ALTER TABLE ads
  ADD COLUMN IF NOT EXISTS has_cta BOOLEAN DEFAULT FALSE;

-- 7) 바이럴 점수
--    = (instagram_views*1 + instagram_likes*10 + instagram_comments*50)
--      / days_since_posted
ALTER TABLE ads
  ADD COLUMN IF NOT EXISTS viral_score FLOAT DEFAULT 0.0;

-- 8) 캡션 전문
ALTER TABLE ads
  ADD COLUMN IF NOT EXISTS caption_text TEXT;

-- 9) Instagram 데이터 마지막 수집일
ALTER TABLE ads
  ADD COLUMN IF NOT EXISTS ig_collected_at TIMESTAMP;

-- ============================================================
-- 인덱스 추가 (탭 2·3 필터링 성능)
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_ads_has_cta
  ON ads (has_cta);

CREATE INDEX IF NOT EXISTS idx_ads_viral_score
  ON ads (viral_score DESC);

CREATE INDEX IF NOT EXISTS idx_ads_post_date
  ON ads (post_date DESC);

CREATE INDEX IF NOT EXISTS idx_ads_instagram_views
  ON ads (instagram_views DESC);

-- ============================================================
-- 바이럴 점수 자동 재계산 함수 (Supabase Cron 또는 수동 호출)
-- ============================================================
CREATE OR REPLACE FUNCTION refresh_viral_scores()
RETURNS void AS $$
BEGIN
  UPDATE ads
  SET viral_score = ROUND(
    (
      COALESCE(instagram_views,    0) * 1.0
      + COALESCE(instagram_likes,    0) * 10.0
      + COALESCE(instagram_comments, 0) * 50.0
    ) / GREATEST(
      EXTRACT(DAY FROM (NOW() - post_date::TIMESTAMP)), 1
    ),
    2
  )
  WHERE post_date IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_viral_scores IS
  '바이럴 점수를 현재 날짜 기준으로 일괄 재계산';

-- ============================================================
-- 뷰: Instagram 성과 광고 (CTA 있는 광고만)
-- ============================================================
CREATE OR REPLACE VIEW performance_ads AS
SELECT
  id,
  category,
  advertiser,
  ad_text,
  thumbnail_url,
  ad_library_url,
  instagram_url,
  instagram_views,
  instagram_likes,
  instagram_comments,
  post_date,
  has_cta,
  viral_score,
  caption_text,
  days_live,
  is_active
FROM ads
WHERE has_cta = TRUE
  AND instagram_url IS NOT NULL
ORDER BY instagram_views DESC;

COMMENT ON VIEW performance_ads IS
  'CTA 포함 + Instagram 연동된 성과 광고 목록';

-- ============================================================
-- 뷰: 바이럴 컨텐츠 TOP (최근 30일 게시)
-- ============================================================
CREATE OR REPLACE VIEW viral_content AS
SELECT
  id,
  category,
  advertiser,
  instagram_url,
  instagram_views,
  instagram_likes,
  instagram_comments,
  post_date,
  viral_score,
  caption_text,
  has_cta,
  ad_library_url,
  thumbnail_url
FROM ads
WHERE post_date >= CURRENT_DATE - INTERVAL '30 days'
  AND viral_score > 0
  AND instagram_url IS NOT NULL
ORDER BY viral_score DESC;

COMMENT ON VIEW viral_content IS
  '최근 30일 게시된 바이럴 점수 TOP 콘텐츠';
