#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
인기 급상승 키워드 탐지 및 Excel 차트 삽입 통합 테스트
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

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

from keyword_trend_analyzer import KeywordTrendSystem
from keyword_trend_alert_system import KeywordAlertSystem
from excel_chart_integration import ExcelReportGenerator
from email_notifier import EmailNotifier, EmailAuth


def test_trending_alert_system():
    """급상승 키워드 탐지 시스템 테스트"""
    print("\n" + "="*60)
    print("1. 인기 급상승 키워드 탐지 시스템 테스트")
    print("="*60)

    try:
        # 알림 시스템 초기화
        alert_system = KeywordAlertSystem()

        # 테스트 데이터 생성 (급상승 키워드 포함)
        test_trend_data = []
        base_date = datetime.now()

        # 급상승 키워드: AI (성장률 300%)
        for i in range(7):
            test_trend_data.append({
                'date': (base_date - timedelta(days=6-i)).strftime('%Y-%m-%d'),
                'keyword': 'AI',
                'frequency': 10 + i * 15  # 10, 25, 40, 55, 70, 85, 100
            })

        # 급상승 키워드: 메타버스 (순위 10계급 상승)
        for i in range(7):
            test_trend_data.append({
                'date': (base_date - timedelta(days=6-i)).strftime('%Y-%m-%d'),
                'keyword': '메타버스',
                'frequency': 5 + i * 8  # 5, 13, 21, 29, 37, 45, 53
            })

        # 일반 키워드: 블록체인 (안정적)
        for i in range(7):
            test_trend_data.append({
                'date': (base_date - timedelta(days=6-i)).strftime('%Y-%m-%d'),
                'keyword': '블록체인',
                'frequency': 50  # 고정
            })

        trend_df = pd.DataFrame(test_trend_data)
        trend_df['date'] = pd.to_datetime(trend_df['date'])

        # 모니터링 및 알림
        result = alert_system.monitor_and_alert(trend_df)

        print(f"\n✓ 탐지된 급상승 키워드: {result['detected']}개")
        print(f"✓ 알림 발송: {result['alerted']}개")

        if result['keywords']:
            print("\n급상승 키워드 상세:")
            for i, kw in enumerate(result['keywords'], 1):
                print(f"  {i}. {kw['keyword']} - 점수: {kw['trending_score']:.1f}, "
                     f"성장률: {kw['growth_rate']:.1f}%")

        # 리포트 출력
        print("\n" + alert_system.get_trending_report(trend_df))

        print("✅ 급상승 키워드 탐지 테스트 완료")

        return result

    except Exception as e:
        print(f"❌ 급상승 키워드 탐지 테스트 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_excel_chart_insertion():
    """Excel 차트 자동 삽입 테스트"""
    print("\n" + "="*60)
    print("2. Excel 차트 자동 삽입 시스템 테스트")
    print("="*60)

    try:
        # 먼저 기본 분석 실행
        print("\n키워드 트렌드 분석 실행 중...")
        system = KeywordTrendSystem(analyzer_type='okt')

        # 테스트 문서 생성
        test_documents = [
            {
                'title': 'AI 기술 혁신',
                'content': '인공지능과 머신러닝 기술이 급격히 발전하고 있습니다. AI는 다양한 산업에서 혁신을 주도하고 있으며, 딥러닝과 신경망 기술이 특히 주목받고 있습니다.',
                'date': (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
            },
            {
                'title': '메타버스 플랫폼',
                'content': '메타버스 플랫폼이 확장되고 있습니다. 가상현실과 증강현실 기술이 결합된 메타버스는 게임, 교육, 비즈니스 등 다양한 분야에서 활용되고 있습니다.',
                'date': (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d')
            },
            {
                'title': 'AI와 메타버스의 결합',
                'content': '인공지능 기술이 메타버스 플랫폼에 통합되고 있습니다. AI 기반의 가상 인간, 자연어 처리, 컴퓨터 비전 기술이 메타버스 경험을 향상시키고 있습니다.',
                'date': datetime.now().strftime('%Y-%m-%d')
            }
        ]

        # 문서 분석
        results = system.analyze_documents(test_documents)

        if not results or 'trend_data' not in results:
            print("❌ 분석 결과가 없습니다.")
            return None

        trend_df = results['trend_data']
        growth_df = results.get('growth_data', pd.DataFrame())

        # Excel 파일 경로
        excel_path = "charts/keyword_analysis_with_charts.xlsx"

        # Excel 파일 생성 (기존 데이터)
        from openpyxl import Workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "원본 데이터"

        # 트렌드 데이터 쓰기
        ws.append(['date', 'keyword', 'frequency'])
        for _, row in trend_df.iterrows():
            ws.append([row['date'], row['keyword'], row['frequency']])

        wb.save(excel_path)
        print(f"✓ 기본 Excel 파일 생성: {excel_path}")

        # 차트 삽입
        print("\n차트 삽입 중...")
        generator = ExcelReportGenerator()

        # 키워드 빈도 데이터 준비
        keyword_freq = trend_df.groupby('keyword')['frequency'].sum().items()
        keyword_freq_list = [(k, int(v)) for k, v in keyword_freq]

        # 네트워크 그래프
        network = results.get('network')

        # 워드클라우드 데이터
        word_freq = {}
        for k, v in keyword_freq:
            word_freq[k] = v

        # 종합 리포트 생성
        chart_results = generator.generate_comprehensive_report(
            excel_path=excel_path,
            trend_df=trend_df,
            growth_df=growth_df,
            keyword_freq=keyword_freq_list,
            network_graph=network,
            word_freq=word_freq
        )

        print(f"\n차트 삽입 결과:")
        for chart_type, success in chart_results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {chart_type}: {'성공' if success else '실패'}")

        success_count = sum(1 for v in chart_results.values() if v)
        print(f"\n✅ {success_count}/{len(chart_results)}개 차트 삽입 완료")
        print(f"📊 리포트 파일: {excel_path}")

        return chart_results

    except Exception as e:
        print(f"❌ Excel 차트 삽입 테스트 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_integration_with_email():
    """이메일 알림과의 통합 테스트"""
    print("\n" + "="*60)
    print("3. 이메일 알림 통합 테스트")
    print("="*60)

    try:
        # 이메일 인증 (선택사항)
        try:
            auth = EmailAuth()
            email_notifier = EmailNotifier(auth)
            has_email = True
            print("✓ 이메일 설정 완료")
        except:
            email_notifier = None
            has_email = False
            print("! 이메일 미설정 (콘솔 출력만)")

        # 알림 시스템 초기화
        alert_system = KeywordAlertSystem(
            email_notifier=email_notifier
        )

        # 테스트 데이터
        test_trend_data = []
        base_date = datetime.now()

        # 급상승 키워드
        keywords_data = [
            ('ChatGPT', [5, 10, 20, 40, 80, 160, 320]),    # 폭발적 성장
            ('암호화폐', [100, 90, 80, 70, 60, 50, 40]),   # 하락
            ('웹3', [10, 12, 15, 25, 40, 65, 100])         # 꾸준한 상승
        ]

        for keyword, frequencies in keywords_data:
            for i, freq in enumerate(frequencies):
                test_trend_data.append({
                    'date': (base_date - timedelta(days=6-i)).strftime('%Y-%m-%d'),
                    'keyword': keyword,
                    'frequency': freq
                })

        trend_df = pd.DataFrame(test_trend_data)
        trend_df['date'] = pd.to_datetime(trend_df['date'])

        # 모니터링 및 알림
        recipients = [auth.get_email()] if has_email else None
        result = alert_system.monitor_and_alert(trend_df, recipients=recipients)

        print(f"\n✓ 탐지: {result['detected']}개, 알림: {result['alerted']}개")

        if has_email and result['alerted'] > 0:
            print("✓ 이메일 알림 발송 완료")
        else:
            print("! 콘솔 알림 출력")

        print("✅ 이메일 통합 테스트 완료")

        return result

    except Exception as e:
        print(f"❌ 이메일 통합 테스트 오류: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_all_tests():
    """모든 테스트 실행"""
    print("\n" + "="*60)
    print("인기 급상승 키워드 탐지 및 Excel 차트 삽입 종합 테스트")
    print("="*60)

    # 1. 급상승 키워드 탐지
    alert_result = test_trending_alert_system()

    # 2. Excel 차트 삽입
    chart_result = test_excel_chart_insertion()

    # 3. 이메일 통합
    email_result = test_integration_with_email()

    # 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)

    tests = [
        ("급상승 키워드 탐지", alert_result),
        ("Excel 차트 삽입", chart_result),
        ("이메일 통합", email_result)
    ]

    for test_name, result in tests:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"  {status}: {test_name}")

    print("\n" + "="*60)
    print("모든 테스트 완료!")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()
