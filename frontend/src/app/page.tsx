'use client';

import { useState, useEffect } from 'react';
import { supabase, Ad, AdStats } from '@/lib/supabase';
import AdCard from '@/components/AdCard';

const CATEGORIES = [
  '전체',
  '뷰티디바이스',
  '스킨케어',
  '헤어케어',
  '생활용품',
  '건강기능식품',
];

export default function Dashboard() {
  const [ads, setAds] = useState<Ad[]>([]);
  const [stats, setStats] = useState<AdStats | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('전체');
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<'days_live' | 'collected_at'>('days_live');

  useEffect(() => {
    fetchAds();
    fetchStats();
  }, [selectedCategory, sortBy]);

  async function fetchAds() {
    setLoading(true);

    try {
      let query = supabase
        .from('ads')
        .select('*')
        .eq('is_active', true);

      if (selectedCategory !== '전체') {
        query = query.eq('category', selectedCategory);
      }

      if (sortBy === 'days_live') {
        query = query.order('days_live', { ascending: false });
      } else {
        query = query.order('collected_at', { ascending: false });
      }

      query = query.limit(100);

      const { data, error } = await query;

      if (error) throw error;

      setAds(data || []);
    } catch (error) {
      console.error('Error fetching ads:', error);
    } finally {
      setLoading(false);
    }
  }

  async function fetchStats() {
    try {
      const { data, error } = await supabase
        .from('active_ads_stats')
        .select('*')
        .eq('category', selectedCategory === '전체' ? null : selectedCategory)
        .single();

      if (error && error.code !== 'PGRST116') {
        // PGRST116 = no rows returned
        console.error('Error fetching stats:', error);
      }

      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* 헤더 */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                META 광고 레퍼런스 대시보드
              </h1>
              <p className="text-gray-600 mt-1">
                성과 광고 자동 수집 시스템
              </p>
            </div>

            {/* 정렬 옵션 */}
            <div className="flex gap-2">
              <button
                onClick={() => setSortBy('days_live')}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  sortBy === 'days_live'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                라이브 일수순
              </button>
              <button
                onClick={() => setSortBy('collected_at')}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  sortBy === 'collected_at'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                최신순
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 통계 카드 */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600">총 광고</div>
              <div className="text-2xl font-bold text-gray-900 mt-1">
                {stats.total_ads}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600">광고주</div>
              <div className="text-2xl font-bold text-gray-900 mt-1">
                {stats.unique_advertisers}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600">평균 라이브</div>
              <div className="text-2xl font-bold text-gray-900 mt-1">
                {Math.round(stats.avg_days_live)}일
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600">비디오</div>
              <div className="text-2xl font-bold text-red-600 mt-1">
                {stats.video_ads}
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600">이미지</div>
              <div className="text-2xl font-bold text-blue-600 mt-1">
                {stats.image_ads}
              </div>
            </div>
          </div>
        )}

        {/* 카테고리 필터 */}
        <div className="mb-6 flex gap-2 flex-wrap">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                selectedCategory === cat
                  ? 'bg-blue-600 text-white shadow-lg scale-105'
                  : 'bg-white text-gray-700 hover:bg-gray-50 hover:scale-105'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* 광고 그리드 */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">광고를 불러오는 중...</p>
            </div>
          </div>
        ) : ads.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-lg shadow">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <p className="mt-4 text-gray-600">
              {selectedCategory}에 대한 광고가 아직 없습니다.
            </p>
          </div>
        ) : (
          <>
            <div className="mb-4 text-sm text-gray-600">
              {ads.length}개의 광고를 찾았습니다
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {ads.map((ad) => (
                <AdCard key={ad.id} ad={ad} />
              ))}
            </div>
          </>
        )}
      </main>

      {/* 푸터 */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-gray-500 text-sm">
            © 2026 META 광고 레퍼런스 대시보드. 매일 자동 업데이트됩니다.
          </p>
        </div>
      </footer>
    </div>
  );
}
