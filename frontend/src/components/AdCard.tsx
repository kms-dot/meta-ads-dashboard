'use client';

import { Ad } from '@/lib/supabase';
import { useState } from 'react';

interface AdCardProps {
  ad: Ad;
}

export default function AdCard({ ad }: AdCardProps) {
  const [imageError, setImageError] = useState(false);
  const [videoError, setVideoError] = useState(false);

  const hasVideo = ad.video_url && !videoError;
  const hasImage = ad.thumbnail_url && !imageError;

  return (
    <a
      href={ad.ad_library_url}
      target="_blank"
      rel="noopener noreferrer"
      className="block bg-white rounded-lg shadow hover:shadow-xl transition-shadow duration-300 overflow-hidden group"
    >
      {/* 썸네일/비디오 */}
      <div className="aspect-square bg-gray-200 relative overflow-hidden">
        {hasVideo ? (
          <video
            src={ad.video_url!}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            muted
            loop
            playsInline
            onError={() => setVideoError(true)}
          />
        ) : hasImage ? (
          <img
            src={ad.thumbnail_url!}
            alt={ad.advertiser}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200">
            <svg
              className="w-20 h-20 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </div>
        )}

        {/* 라이브 일수 배지 */}
        <div className="absolute top-2 right-2 bg-black/70 backdrop-blur-sm text-white px-3 py-1 rounded-full text-sm font-medium">
          🔥 {ad.days_live}일째
        </div>

        {/* 미디어 타입 배지 */}
        {ad.media_type === 'video' && (
          <div className="absolute top-2 left-2 bg-red-500 text-white px-2 py-1 rounded text-xs font-medium">
            VIDEO
          </div>
        )}
      </div>

      {/* 광고 정보 */}
      <div className="p-4">
        {/* 광고주 */}
        <h3 className="font-semibold text-gray-900 truncate mb-2 group-hover:text-blue-600 transition-colors">
          {ad.advertiser}
        </h3>

        {/* 광고 텍스트 (있는 경우) */}
        {ad.ad_text && (
          <p className="text-sm text-gray-600 line-clamp-2 mb-3">
            {ad.ad_text}
          </p>
        )}

        {/* 하단 정보 */}
        <div className="flex items-center justify-between">
          {/* 카테고리 태그 */}
          <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full font-medium">
            {ad.category}
          </span>

          {/* 플랫폼 아이콘 */}
          {ad.platforms && ad.platforms.length > 0 && (
            <div className="flex gap-1">
              {ad.platforms.map((platform) => (
                <span
                  key={platform}
                  className="text-xs text-gray-500"
                  title={platform}
                >
                  {platform === 'Facebook' && '📘'}
                  {platform === 'Instagram' && '📷'}
                  {platform === 'Messenger' && '💬'}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* 게재 시작일 */}
        {ad.start_date && (
          <div className="mt-2 text-xs text-gray-500">
            게재 시작: {new Date(ad.start_date).toLocaleDateString('ko-KR')}
          </div>
        )}
      </div>
    </a>
  );
}
