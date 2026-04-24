#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
키워드 트렌드 분석 시스템 간단 사용 예제

기본적인 사용법을 보여주는 간단한 예제입니다.
"""

import sys
import os

# UTF-8 출력 설정 (Windows)
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

from keyword_trend_analyzer import KeywordTrendSystem
from datetime import datetime, timedelta


def main():
    """메인 실행 함수"""
    print("="*60)
    print("키워드 트렌드 분석 시스템 예제")
    print("="*60)

    # 1. 시스템 초기화
    print("\n1. 시스템 초기화 중...")
    try:
        system = KeywordTrendSystem(analyzer_type='okt')
        print("   ✓ 시스템 초기화 완료")
    except Exception as e:
        print(f"   ✗ 초기화 실패: {e}")
        return

    # 2. 로그 파일 분석
    print("\n2. 로그 파일 분석 중...")
    results = system.analyze_from_logs('logs')

    if not results:
        print("   ! 분석 결과가 없습니다.")
        print("   ! 먼저 크롤러를 실행하여 로그 파일을 생성하세요.")
        return

    print("   ✓ 로그 분석 완료")

    # 3. 결과 요약 출력
    print("\n3. 분석 결과:")
    system.print_summary(results)

    # 4. 리포트 생성
    print("\n4. 리포트 생성 중...")
    report_files = system.generate_report(results)

    print(f"   ✓ {len(report_files)}개 리포트 생성 완료:")
    for report_type, file_path in report_files.items():
        print(f"     - {report_type}: {file_path}")

    # 5. 리포트 파일 열기
    print("\n5. 리포트 확인:")
    print("   charts/ 디렉토리에서 생성된 HTML 파일을 브라우저로 열어보세요.")
    print("   - keyword_trend_*.html: 키워드 트렌드 차트")
    print("   - keyword_network_*.html: 키워드 연관 네트워크")
    print("   - growth_heatmap_*.html: 키워드 성장률 히트맵")

    print("\n" + "="*60)
    print("분석 완료!")
    print("="*60)


if __name__ == "__main__":
    main()
