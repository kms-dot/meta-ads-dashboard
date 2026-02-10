-- ========================================
-- Supabase 데이터베이스 스키마
-- ========================================

-- UUID 확장 활성화
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- ads 테이블: Meta 광고 데이터
-- ========================================
CREATE TABLE IF NOT EXISTS ads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 분류
    category VARCHAR(50) NOT NULL,

    -- 광고 정보
    advertiser VARCHAR(200),
    ad_id VARCHAR(100),
    ad_text TEXT,

    -- 미디어
    thumbnail_url TEXT,
    video_url TEXT,
    media_type VARCHAR(20),  -- 'image', 'video', 'unknown'

    -- 플랫폼
    platforms TEXT[],  -- ['Facebook', 'Instagram', 'Messenger']

    -- URL
    ad_library_url TEXT NOT NULL UNIQUE,  -- 중복 방지

    -- 게재 정보
    days_live INTEGER DEFAULT 0,
    start_date DATE,
    impression_text TEXT,

    -- 상태
    is_active BOOLEAN DEFAULT true,

    -- 메타데이터
    query VARCHAR(200),  -- 검색 키워드
    collected_at TIMESTAMP DEFAULT NOW(),
    last_checked TIMESTAMP DEFAULT NOW(),

    -- 분석 데이터
    rank INTEGER,
    crawl_date TIMESTAMP
);

-- ads 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_ads_category ON ads(category);
CREATE INDEX IF NOT EXISTS idx_ads_is_active ON ads(is_active);
CREATE INDEX IF NOT EXISTS idx_ads_days_live ON ads(days_live DESC);
CREATE INDEX IF NOT EXISTS idx_ads_advertiser ON ads(advertiser);
CREATE INDEX IF NOT EXISTS idx_ads_collected_at ON ads(collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_ads_query ON ads(query);

-- ads 테이블 코멘트
COMMENT ON TABLE ads IS 'Meta 광고 라이브러리에서 수집한 광고 데이터';
COMMENT ON COLUMN ads.ad_library_url IS '광고 고유 URL (중복 체크 기준)';
COMMENT ON COLUMN ads.days_live IS '광고 게재 시작일로부터 경과 일수';
COMMENT ON COLUMN ads.is_active IS '현재 라이브 중인지 여부';

-- ========================================
-- keywords 테이블: 검색 키워드 관리
-- ========================================
CREATE TABLE IF NOT EXISTS keywords (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 분류
    category VARCHAR(50) NOT NULL,

    -- 키워드 정보
    keyword VARCHAR(200) NOT NULL,
    keyword_type VARCHAR(20),  -- 'product_type', 'brand', 'function'

    -- 출처
    source VARCHAR(50),  -- 'user_provided', 'naver_shopping', 'coupang', 'oliveyoung', 'meta_ads'

    -- 우선순위
    search_priority INTEGER DEFAULT 0,

    -- 통계
    search_count INTEGER DEFAULT 0,
    total_products_found INTEGER DEFAULT 0,
    total_ads_found INTEGER DEFAULT 0,

    -- 상태
    is_active BOOLEAN DEFAULT true,

    -- 메타데이터
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_searched TIMESTAMP
);

-- keywords 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_keywords_category ON keywords(category);
CREATE INDEX IF NOT EXISTS idx_keywords_active ON keywords(is_active);
CREATE INDEX IF NOT EXISTS idx_keywords_type ON keywords(keyword_type);
CREATE INDEX IF NOT EXISTS idx_keywords_priority ON keywords(search_priority DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_keywords_unique ON keywords(category, keyword, keyword_type);

-- keywords 테이블 코멘트
COMMENT ON TABLE keywords IS '쇼핑몰 및 Meta 광고 검색에 사용되는 키워드';
COMMENT ON COLUMN keywords.search_priority IS '검색 우선순위 (높을수록 먼저 검색)';
COMMENT ON COLUMN keywords.search_count IS '검색 실행 횟수';

-- ========================================
-- products 테이블: 쇼핑몰 제품 데이터
-- ========================================
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 분류
    category VARCHAR(50) NOT NULL,

    -- 제품 정보
    name TEXT NOT NULL,
    brand VARCHAR(200),
    price INTEGER,
    original_price INTEGER,
    discount_rate INTEGER,

    -- 리뷰 및 평점
    review_count INTEGER DEFAULT 0,
    rating DECIMAL(3,2),

    -- URL 및 이미지
    link TEXT,
    image_url TEXT,

    -- 플랫폼
    platform VARCHAR(50) NOT NULL,  -- 'naver', 'coupang', 'oliveyoung'

    -- 검색 정보
    keyword VARCHAR(200),
    rank INTEGER,

    -- 특성
    is_sale BOOLEAN DEFAULT false,
    is_best BOOLEAN DEFAULT false,
    is_rocket BOOLEAN DEFAULT false,

    -- 메타데이터
    collected_at TIMESTAMP DEFAULT NOW(),
    last_checked TIMESTAMP DEFAULT NOW()
);

-- products 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_platform ON products(platform);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_keyword ON products(keyword);
CREATE INDEX IF NOT EXISTS idx_products_rating ON products(rating DESC);
CREATE INDEX IF NOT EXISTS idx_products_review_count ON products(review_count DESC);
CREATE INDEX IF NOT EXISTS idx_products_collected_at ON products(collected_at DESC);

-- products 테이블 코멘트
COMMENT ON TABLE products IS '쇼핑몰에서 수집한 제품 데이터';
COMMENT ON COLUMN products.platform IS '제품이 수집된 쇼핑 플랫폼';

-- ========================================
-- brands 테이블: 브랜드 통계
-- ========================================
CREATE TABLE IF NOT EXISTS brands (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 브랜드 정보
    category VARCHAR(50) NOT NULL,
    brand_name VARCHAR(200) NOT NULL,

    -- 통계 (쇼핑몰)
    product_count INTEGER DEFAULT 0,
    avg_price INTEGER,
    avg_rating DECIMAL(3,2),
    total_reviews INTEGER DEFAULT 0,

    -- 통계 (Meta 광고)
    ad_count INTEGER DEFAULT 0,
    avg_days_live INTEGER DEFAULT 0,
    active_ads_count INTEGER DEFAULT 0,

    -- 분류
    is_user_brand BOOLEAN DEFAULT false,

    -- 메타데이터
    updated_at TIMESTAMP DEFAULT NOW()
);

-- brands 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_brands_category ON brands(category);
CREATE INDEX IF NOT EXISTS idx_brands_name ON brands(brand_name);
CREATE INDEX IF NOT EXISTS idx_brands_user_brand ON brands(is_user_brand);
CREATE UNIQUE INDEX IF NOT EXISTS idx_brands_unique ON brands(category, brand_name);

-- brands 테이블 코멘트
COMMENT ON TABLE brands IS '카테고리별 브랜드 통계';
COMMENT ON COLUMN brands.is_user_brand IS '사용자 지정 브랜드 여부';

-- ========================================
-- crawl_logs 테이블: 크롤링 이력
-- ========================================
CREATE TABLE IF NOT EXISTS crawl_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- 크롤링 정보
    crawl_type VARCHAR(20) NOT NULL,  -- 'ecommerce', 'meta_ads'
    category VARCHAR(50),
    platform VARCHAR(50),
    query VARCHAR(200),

    -- 결과
    items_collected INTEGER DEFAULT 0,
    items_new INTEGER DEFAULT 0,
    items_updated INTEGER DEFAULT 0,

    -- 상태
    status VARCHAR(20),  -- 'success', 'failed', 'partial'
    error_message TEXT,

    -- 메타데이터
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    duration_seconds INTEGER
);

-- crawl_logs 테이블 인덱스
CREATE INDEX IF NOT EXISTS idx_crawl_logs_type ON crawl_logs(crawl_type);
CREATE INDEX IF NOT EXISTS idx_crawl_logs_category ON crawl_logs(category);
CREATE INDEX IF NOT EXISTS idx_crawl_logs_status ON crawl_logs(status);
CREATE INDEX IF NOT EXISTS idx_crawl_logs_started_at ON crawl_logs(started_at DESC);

-- crawl_logs 테이블 코멘트
COMMENT ON TABLE crawl_logs IS '크롤링 실행 이력';

-- ========================================
-- 뷰: 활성 광고 통계
-- ========================================
CREATE OR REPLACE VIEW active_ads_stats AS
SELECT
    category,
    COUNT(*) as total_ads,
    COUNT(DISTINCT advertiser) as unique_advertisers,
    AVG(days_live) as avg_days_live,
    COUNT(CASE WHEN media_type = 'video' THEN 1 END) as video_ads,
    COUNT(CASE WHEN media_type = 'image' THEN 1 END) as image_ads
FROM ads
WHERE is_active = true
GROUP BY category;

COMMENT ON VIEW active_ads_stats IS '카테고리별 활성 광고 통계';

-- ========================================
-- 뷰: 브랜드별 광고 현황
-- ========================================
CREATE OR REPLACE VIEW brand_ads_summary AS
SELECT
    category,
    advertiser,
    COUNT(*) as ad_count,
    AVG(days_live) as avg_days_live,
    MIN(start_date) as earliest_ad,
    MAX(start_date) as latest_ad,
    COUNT(CASE WHEN is_active = true THEN 1 END) as active_ads
FROM ads
GROUP BY category, advertiser
ORDER BY ad_count DESC;

COMMENT ON VIEW brand_ads_summary IS '광고주별 광고 현황 요약';

-- ========================================
-- 함수: 광고 상태 업데이트
-- ========================================
CREATE OR REPLACE FUNCTION update_ad_status()
RETURNS void AS $$
BEGIN
    -- 90일 이상 된 광고는 비활성화
    UPDATE ads
    SET is_active = false
    WHERE days_live > 90 AND is_active = true;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_ad_status IS '오래된 광고의 is_active 상태를 자동으로 업데이트';

-- ========================================
-- 함수: 브랜드 통계 갱신
-- ========================================
CREATE OR REPLACE FUNCTION refresh_brand_stats()
RETURNS void AS $$
BEGIN
    -- 기존 데이터 삭제
    DELETE FROM brands;

    -- 쇼핑몰 데이터 집계
    INSERT INTO brands (category, brand_name, product_count, avg_price, avg_rating, total_reviews)
    SELECT
        category,
        brand,
        COUNT(*) as product_count,
        AVG(price)::INTEGER as avg_price,
        AVG(rating) as avg_rating,
        SUM(review_count) as total_reviews
    FROM products
    WHERE brand IS NOT NULL AND brand != ''
    GROUP BY category, brand;

    -- Meta 광고 데이터 추가/업데이트
    UPDATE brands b
    SET
        ad_count = a.ad_count,
        avg_days_live = a.avg_days_live,
        active_ads_count = a.active_ads_count
    FROM (
        SELECT
            category,
            advertiser as brand_name,
            COUNT(*) as ad_count,
            AVG(days_live)::INTEGER as avg_days_live,
            COUNT(CASE WHEN is_active = true THEN 1 END) as active_ads_count
        FROM ads
        GROUP BY category, advertiser
    ) a
    WHERE b.category = a.category AND b.brand_name = a.brand_name;

END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_brand_stats IS '브랜드 통계를 쇼핑몰 및 광고 데이터로 갱신';
