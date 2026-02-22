# 🚀 Streamlit Cloud 배포 가이드

## ✅ 1단계: GitHub 푸시 완료

이미 완료되었습니다!
- Repository: https://github.com/kms-dot/meta-ads-dashboard
- 커밋 완료: befb9b7

---

## 🌐 2단계: Streamlit Cloud 배포

### 방법 1: 직접 배포 (추천)

1. **Streamlit Cloud 접속**
   ```
   https://share.streamlit.io/
   ```

2. **로그인**
   - "Continue with GitHub" 클릭
   - GitHub 계정으로 로그인 (kms-dot 계정)

3. **New app 생성**
   - 우측 상단 "New app" 버튼 클릭
   
4. **앱 설정**
   ```
   Repository: kms-dot/meta-ads-dashboard
   Branch: main
   Main file path: streamlit_dashboard.py
   ```

5. **Advanced settings (선택사항)**
   - Python version: 3.11 (기본값)
   - 그대로 두고 진행

6. **Deploy!**
   - "Deploy" 버튼 클릭
   - 2-3분 대기

7. **URL 확인**
   - 배포 완료 시 자동으로 생성되는 URL 확인
   - 예시: `https://meta-ads-dashboard-[고유ID].streamlit.app`

---

### 방법 2: 원클릭 배포 링크

아래 링크를 클릭하면 자동으로 설정됩니다:

```
https://share.streamlit.io/deploy?repository=kms-dot/meta-ads-dashboard&branch=main&mainModule=streamlit_dashboard.py
```

---

## 📊 배포 후 확인사항

배포된 URL에 접속해서 확인:

- [ ] 페이지 로딩 확인
- [ ] 카테고리 필터 작동 (뷰티디바이스, 스킨케어, 헤어케어, 생활용품, 건강기능식품)
- [ ] 필터링된 광고 수 확인 (총 1,900개)
- [ ] 4열 그리드 레이아웃 표시
- [ ] 이미지/썸네일 정상 표시
- [ ] 페이지네이션 작동 (20/50/100/200/500)
- [ ] 광고 클릭 시 Meta 라이브러리 이동
- [ ] 60일+ 장기 게재 배지 표시
- [ ] TOP 10 광고주 차트 표시

---

## 🎯 상부 보고용 정보

### 대시보드 URL
```
배포 완료 후 여기에 URL 기입
예시: https://meta-ads-dashboard.streamlit.app
```

### 주요 기능
1. **5개 카테고리** 광고 레퍼런스 수집
   - 뷰티디바이스: 408개
   - 스킨케어: 325개
   - 헤어케어: 281개
   - 생활용품: 229개
   - 건강기능식품: 657개

2. **필터링 기능**
   - 카테고리별 필터
   - 최소 게재 일수 설정 (0-365일)
   - 페이지당 표시 개수 조절
   - 정렬 (게재 기간순, 최근 게재일순)

3. **고성과 광고 하이라이트**
   - 60일 이상 장기 게재 광고 배지 표시
   - TOP 10 광고주 차트

4. **자동 업데이트**
   - 매일 자정(KST) 자동 크롤링
   - 부적합 광고 자동 필터링
   - 중복 광고 자동 제거

---

## 🔧 문제 해결

### 배포 실패 시
1. Streamlit Cloud 로그 확인
2. requirements.txt 패키지 확인
3. GitHub 저장소 public 설정 확인

### 데이터 로드 실패 시
- `meta_output/meta_all_categories_filtered_*.json` 파일 확인
- 파일 크기: 4MB (정상)

### 이미지 표시 안 됨
- Facebook CDN 접근 가능 여부 확인
- 브라우저 캐시 삭제 후 재시도

---

## 📞 추가 도움

배포 과정에서 문제가 발생하면:
1. Streamlit Community Forum: https://discuss.streamlit.io/
2. GitHub Issues: https://github.com/kms-dot/meta-ads-dashboard/issues

---

## 🎉 완료!

배포 URL을 상부에 공유하여 컨펌 받으세요!
