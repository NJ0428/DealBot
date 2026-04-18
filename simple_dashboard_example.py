#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 시각화 예시 - 출처별 파이차트와 HTML 대시보드
"""

from web_crawler import WebCrawler, DataVisualizer, DataAnalyzer
from datetime import datetime

def create_sample_data():
    """샘플 데이터 생성"""
    sample_data = []
    sources = ["연합뉴스", "Reuters", "Bloomberg", "CNN", "BBC",
              "로이터", "Yonhap", "Korean Herald", "TechCrunch", "WSJ"]

    for i in range(30):
        import random
        source = random.choice(sources)
        sample_data.append({
            '키워드': 'AI',
            '제목': f'AI 뉴스 제목 {i+1}',
            '요약': f'이것은 AI 뉴스 {i+1}의 요약 내용입니다.',
            '출처/날짜': f'{source} · {i}시간 전',
            '링크': f'https://example.com/news/{i+1}',
            '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    return sample_data

def main():
    print("간단한 데이터 시각화 예시 (샘플 데이터)")
    print("=" * 50)

    # 시각화 초기화
    visualizer = DataVisualizer()
    analyzer = DataAnalyzer()

    # 샘플 데이터 생성
    print(f"\n샘플 데이터 생성 중...")
    data = create_sample_data()
    print(f"데이터 생성 완료: {len(data)}개 항목")

    if data:
        # 출처별 분석
        source_counts = analyzer.analyze_by_source(data)
        print(f"\n출처 분석 결과:")
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   - {source}: {count}개")

        # 출처별 파이차트 생성
        print(f"\n출처별 파이차트 생성 중...")
        pie_chart_path = visualizer.create_pie_chart(
            source_counts,  # 모든 출처
            "출처별 뉴스 비율 (샘플 데이터)",
            open_browser=False  # PNG 파일은 브라우저 자동 열기 안함
        )
        print(f"파이차트 저장: {pie_chart_path}")

        # HTML 대시보드 생성 (자동으로 브라우저에서 열림)
        print(f"\nHTML 대시보드 생성 중...")
        print("브라우저가 자동으로 열립니다...")

        dashboard_path = visualizer.create_dashboard(
            data,
            title="AI 뉴스 데이터 분석 대시보드 (샘플)",
            open_browser=True  # 브라우저 자동 열기
        )
        print(f"대시보드 저장: {dashboard_path}")
        print(f"브라우저에서 대시보드를 확인하세요!")

        # 추가 정보
        print(f"\n생성된 파일들:")
        print(f"   - 파이차트: {pie_chart_path}")
        print(f"   - 대시보드: {dashboard_path}")

        # 전체 차트 생성 (모든 차트 한번에)
        print(f"\n전체 차트 패키지 생성 중...")
        all_charts = visualizer.generate_all_charts(data, "sample_analysis", open_browser=False)
        print(f"전체 차트 생성 완료: {len(all_charts)}개 파일")
        for chart_type, path in all_charts.items():
            print(f"   - {chart_type}: {path}")

    else:
        print("데이터 생성 실패")

    print("\n" + "=" * 50)
    print("시각화 완료!")

if __name__ == "__main__":
    main()