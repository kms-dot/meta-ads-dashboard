-- ============================================================
-- schema_hashtag.sql — Instagram 해시태그 바이럴 포스트 테이블
-- ============================================================
-- 실행: Supabase SQL Editor 또는 psql 에서 실행
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─────────────────────────────────────────────────────────
-- viral_posts 테이블
-- ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS viral_posts (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 출처
    source             VARCHAR(30)  NOT NULL DEFAULT 'instagram_hashtag',
    hashtag            VARCHAR(200) NOT NULL,
    category           VARCHAR(50)  NOT NULL,

    -- Instagram 포스트 정보
    instagram_url      TEXT         NOT NULL UNIQUE,
    thumbnail_url      TEXT,
    is_reel            BOOLEAN      DEFAULT FALSE,

    -- 성과 지표
    instagram_views    INTEGER      DEFAULT 0,
    instagram_likes    INTEGER      DEFAULT 0,
    instagram_comments INTEGER      DEFAULT 0,
    instagram_shares   INTEGER      DEFAULT 0,  -- 가능 시 수집, 없으면 0

    -- 바이럴 점수
    -- = views×1 + likes×10 + comments×50 + shares×100
    -- (게시일 미사용 — 날짜는 화면 표기용만)
    viral_score        FLOAT        DEFAULT 0.0,

    -- 게시 정보
    post_date          DATE,
    caption_text       TEXT,
    has_cta            BOOLEAN      DEFAULT FALSE,

    -- 메타데이터
    collected_at       TIMESTAMP    DEFAULT NOW(),
    last_updated       TIMESTAMP    DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────
-- 인덱스
-- ─────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_viral_category
    ON viral_posts (category);

CREATE INDEX IF NOT EXISTS idx_viral_score
    ON viral_posts (viral_score DESC);

CREATE INDEX IF NOT EXISTS idx_viral_post_date
    ON viral_posts (post_date DESC);

CREATE INDEX IF NOT EXISTS idx_viral_hashtag
    ON viral_posts (hashtag);

CREATE INDEX IF NOT EXISTS idx_viral_source
    ON viral_posts (source);

CREATE INDEX IF NOT EXISTS idx_viral_collected_at
    ON viral_posts (collected_at DESC);

CREATE INDEX IF NOT EXISTS idx_viral_views
    ON viral_posts (instagram_views DESC);

-- ─────────────────────────────────────────────────────────
-- 코멘트
-- ─────────────────────────────────────────────────────────
COMMENT ON TABLE viral_posts IS
    'Instagram 해시태그 탐색으로 수집한 바이럴 포스트 (릴스/비디오)';
COMMENT ON COLUMN viral_posts.viral_score IS
    'views×1 + likes×10 + comments×50 + shares×100 (날짜 미적용)';
COMMENT ON COLUMN viral_posts.post_date IS
    '게시 날짜 (화면 "N일 전" 표기용, 점수 계산에 미사용)';
COMMENT ON COLUMN viral_posts.instagram_shares IS
    'Instagram 공개 미지원 시 0 저장';

-- ─────────────────────────────────────────────────────────
-- 뷰: 카테고리별 바이럴 TOP
-- ─────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW viral_top_by_category AS
SELECT
    category,
    COUNT(*)                        AS total_posts,
    MAX(viral_score)                AS max_viral_score,
    ROUND(AVG(viral_score)::NUMERIC, 0) AS avg_viral_score,
    SUM(instagram_views)            AS total_views,
    MAX(collected_at)               AS last_crawled
FROM viral_posts
GROUP BY category
ORDER BY max_viral_score DESC;

COMMENT ON VIEW viral_top_by_category IS
    '카테고리별 바이럴 점수 집계';

-- ─────────────────────────────────────────────────────────
-- 뷰: 최근 30일 바이럴 TOP 100
-- ─────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW viral_recent_top AS
SELECT
    category,
    hashtag,
    instagram_url,
    thumbnail_url,
    is_reel,
    instagram_views,
    instagram_likes,
    instagram_comments,
    instagram_shares,
    viral_score,
    post_date,
    caption_text,
    has_cta,
    collected_at
FROM viral_posts
WHERE post_date >= CURRENT_DATE - INTERVAL '30 days'
   OR post_date IS NULL
ORDER BY viral_score DESC
LIMIT 100;

COMMENT ON VIEW viral_recent_top IS
    '최근 30일 바이럴 TOP 100 (점수 기준 정렬)';

-- ─────────────────────────────────────────────────────────
-- 함수: viral_score 전체 재계산
-- ─────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION refresh_viral_post_scores()
RETURNS void AS $$
BEGIN
    UPDATE viral_posts
    SET
        viral_score  = (
            instagram_views    * 1.0  +
            instagram_likes    * 10.0 +
            instagram_comments * 50.0 +
            instagram_shares   * 100.0
        ),
        last_updated = NOW();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_viral_post_scores IS
    '모든 포스트의 바이럴 점수를 현재 공식으로 일괄 재계산';

-- ─────────────────────────────────────────────────────────
-- Upsert 헬퍼 함수 (Python 에서 호출)
-- ─────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION upsert_viral_post(
    p_instagram_url      TEXT,
    p_hashtag            VARCHAR,
    p_category           VARCHAR,
    p_thumbnail_url      TEXT,
    p_is_reel            BOOLEAN,
    p_instagram_views    INTEGER,
    p_instagram_likes    INTEGER,
    p_instagram_comments INTEGER,
    p_instagram_shares   INTEGER,
    p_post_date          DATE,
    p_caption_text       TEXT,
    p_has_cta            BOOLEAN,
    p_viral_score        FLOAT
)
RETURNS void AS $$
BEGIN
    INSERT INTO viral_posts (
        instagram_url, hashtag, category,
        thumbnail_url, is_reel,
        instagram_views, instagram_likes, instagram_comments, instagram_shares,
        post_date, caption_text, has_cta, viral_score,
        collected_at, last_updated
    ) VALUES (
        p_instagram_url, p_hashtag, p_category,
        p_thumbnail_url, p_is_reel,
        p_instagram_views, p_instagram_likes, p_instagram_comments, p_instagram_shares,
        p_post_date, p_caption_text, p_has_cta, p_viral_score,
        NOW(), NOW()
    )
    ON CONFLICT (instagram_url) DO UPDATE SET
        hashtag            = EXCLUDED.hashtag,
        instagram_views    = EXCLUDED.instagram_views,
        instagram_likes    = EXCLUDED.instagram_likes,
        instagram_comments = EXCLUDED.instagram_comments,
        instagram_shares   = EXCLUDED.instagram_shares,
        viral_score        = EXCLUDED.viral_score,
        post_date          = COALESCE(EXCLUDED.post_date, viral_posts.post_date),
        caption_text       = COALESCE(EXCLUDED.caption_text, viral_posts.caption_text),
        has_cta            = EXCLUDED.has_cta,
        last_updated       = NOW();
END;
$$ LANGUAGE plpgsql;
