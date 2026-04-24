#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
키워드 트렌드 분석 시스템 테스트 스크립트

다양한 예제 데이터로 시스템 기능을 테스트합니다.
"""

import sys
import os

# UTF-8 출력 설정 (Windows)
if sys.platform == 'win32':
    import locale
    import codecs
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass  # Python 3.7 이전 버전 호환성
from datetime import datetime, timedelta
from keyword_trend_analyzer import (
    KeywordTrendSystem,
    KoreanMorphemeAnalyzer,
    KeywordTrendAnalyzer,
    RelatedKeywordAnalyzer,
    KeywordVisualizer,
    AnalyzerConfig
)


def create_test_documents():
    """테스트용 문서 데이터 생성"""
    base_date = datetime.now()

    documents = [
        {
            'title': 'AI 기술 동향',
            'content': '인공지능과 머신러닝 기술이 급격히 발전하고 있습니다. 딥러닝과 신경망 기술이 다양한 분야에서 활용되고 있으며, 자연어 처리와 컴퓨터 비전 기술도 향상되고 있습니다.',
            'date': (base_date - timedelta(days=28)).strftime('%Y-%m-%d')
        },
        {
            'title': '블록체인 기술',
            'content': '블록체인과 암호화폐 기술이 금융 산업을 변화시키고 있습니다. 스마트 컨트랙트와 탈중앙화 금융 시스템이 주목받고 있으며, 비트코인과 이더리움이 대표적인 암호화폐입니다.',
            'date': (base_date - timedelta(days=25)).strftime('%Y-%m-%d')
        },
        {
            'title': '클라우드 컴퓨팅',
            'content': '클라우드 컴퓨팅 서비스가 기업 IT 인프라의 핵심이 되고 있습니다. AWS, Azure, GCP와 같은 퍼블릭 클라우드와 프라이빗 클라우드, 하이브리드 클라우드 솔루션이 인기를 끌고 있습니다.',
            'date': (base_date - timedelta(days=21)).strftime('%Y-%m-%d')
        },
        {
            'title': 'AI와 머신러닝의 미래',
            'content': '머신러닝과 딥러닝 기술이 의료, 금융, 제조 등 다양한 산업에서 혁신을 일으키고 있습니다. 특히 생성형 AI와 대규모 언어 모델이 주목받고 있으며, GPT와 같은 모델이 자연어 처리의 새로운 기준을 제시하고 있습니다.',
            'date': (base_date - timedelta(days=14)).strftime('%Y-%m-%d')
        },
        {
            'title': '암호화폐 시장 동향',
            'content': '암호화폐 시장이 변동성을 보이고 있지만, 블록체인 기술에 대한 관심은 지속되고 있습니다. DeFi와 NFT, Web3 기술이 발전하고 있으며, 메타버스와 연계된 새로운 응용 분야가 등장하고 있습니다.',
            'date': (base_date - timedelta(days=7)).strftime('%Y-%m-%d')
        },
        {
            'title': 'AI와 클라우드의 결합',
            'content': '인공지능과 머신러닝 서비스가 클라우드 플랫폼을 통해 확산되고 있습니다. MLOps와 AI 서비스가 기술 기업의 핵심 경쟁력이 되고 있으며, 데이터 분석과 예측 모델링이 중요해지고 있습니다.',
            'date': (base_date - timedelta(days=3)).strftime('%Y-%m-%d')
        },
        {
            'title': '최신 기술 트렌드',
            'content': 'AI, 블록체인, 클라우드 컴퓨팅이 IT 산업의 3대 축으로 자리잡았습니다. 디지털 전환이 가속화되면서 데이터 분석, 자동화, 인텔리전트 시스템이 기업의 필수 요소가 되고 있습니다.',
            'date': base_date.strftime('%Y-%m-%d')
        }
    ]

    return documents


def test_morpheme_analysis():
    """형태소 분석 테스트"""
    print("\n" + "="*60)
    print("1. 형태소 분석 테스트")
    print("="*60)

    try:
        analyzer = KoreanMorphemeAnalyzer(analyzer_type='okt')

        test_text = """
        인공지능과 머신러닝 기술이 급격히 발전하고 있습니다.
        딥러닝과 신경망 기술이 다양한 분야에서 활용되고 있습니다.
        """

        print(f"\n분석 텍스트: {test_text.strip()}")

        # 명사 추출
        nouns = analyzer.extract_nouns(test_text)
        print(f"\n추출된 명사: {nouns}")

        # 품사 태깅
        pos_tags = analyzer.extract_pos_tags(test_text)
        print(f"\n품사 태깅 결과 (상위 10개):")
        for word, tag in pos_tags[:10]:
            print(f"  - {word}: {tag}")

        # 키워드 추출
        keywords = analyzer.extract_keywords(test_text, top_n=5)
        print(f"\n상위 키워드:")
        for keyword, freq in keywords:
            print(f"  - {keyword}: {freq}회")

        print("\n✅ 형태소 분석 테스트 완료")

    except Exception as e:
        print(f"\n❌ 형태소 분석 테스트 오류: {e}")


def test_trend_analysis():
    """트렌드 분석 테스트"""
    print("\n" + "="*60)
    print("2. 트렌드 분석 테스트")
    print("="*60)

    try:
        system = KeywordTrendSystem(analyzer_type='okt')
        documents = create_test_documents()

        # 문서 분석
        results = system.analyze_documents(documents)

        # 인기 키워드 출력
        if 'hot_keywords' in results:
            print("\n🔥 상위 인기 키워드:")
            for i, (keyword, freq) in enumerate(results['hot_keywords'][:10], 1):
                print(f"  {i}. {keyword} ({freq}회)")

        # 트렌드 데이터 확인
        if 'trend_data' in results:
            trend_df = results['trend_data']
            print(f"\n📊 트렌드 데이터 포인트: {len(trend_df)}개")
            if not trend_df.empty:
                print("최근 트렌드 (상위 5개):")
                print(trend_df.tail(10).to_string(index=False))

        print("\n✅ 트렌드 분석 테스트 완료")

    except Exception as e:
        print(f"\n❌ 트렌드 분석 테스트 오류: {e}")
        import traceback
        traceback.print_exc()


def test_network_analysis():
    """네트워크 분석 테스트"""
    print("\n" + "="*60)
    print("3. 네트워크 분석 테스트")
    print("="*60)

    try:
        system = KeywordTrendSystem(analyzer_type='okt')
        documents = create_test_documents()

        results = system.analyze_documents(documents)

        if 'network' in results:
            import networkx as nx
            G = results['network']

            print(f"\n🌐 네트워크 통계:")
            print(f"  - 노드 수: {G.number_of_nodes()}")
            print(f"  - 엣지 수: {G.number_of_edges()}")
            print(f"  - 연결 밀도: {nx.density(G):.4f}")

            # 중심성 분석
            centrality = nx.degree_centrality(G)
            top_central = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"\n  중심성 상위 키워드:")
            for keyword, score in top_central:
                print(f"    - {keyword}: {score:.4f}")

            # 커뮤니티 탐지
            if G.number_of_nodes() > 2:
                communities = list(nx.community.greedy_modularity_communities(G))
                print(f"\n  발견된 커뮤니티: {len(communities)}개")
                for i, community in enumerate(communities, 1):
                    print(f"    커뮤니티 {i}: {', '.join(list(community)[:5])}")

        if 'clusters' in results:
            print(f"\n📊 클러스터링 결과:")
            for cluster_id, keywords in results['clusters'].items():
                print(f"  클러스터 {cluster_id}: {', '.join(keywords[:5])}")

        print("\n✅ 네트워크 분석 테스트 완료")

    except Exception as e:
        print(f"\n❌ 네트워크 분석 테스트 오류: {e}")
        import traceback
        traceback.print_exc()


def test_visualization():
    """시각화 테스트"""
    print("\n" + "="*60)
    print("4. 시각화 테스트")
    print("="*60)

    try:
        system = KeywordTrendSystem(analyzer_type='okt')
        documents = create_test_documents()

        # 문서 분석
        results = system.analyze_documents(documents)

        # 리포트 생성
        report_files = system.generate_report(results)

        print(f"\n📊 생성된 리포트 ({len(report_files)}개):")
        for report_type, file_path in report_files.items():
            print(f"  - {report_type}: {file_path}")

        print("\n✅ 시각화 테스트 완료")
        print("💡 charts/ 디렉토리에서 생성된 파일을 확인하세요.")

    except Exception as e:
        print(f"\n❌ 시각화 테스트 오류: {e}")
        import traceback
        traceback.print_exc()


def test_log_analysis():
    """로그 파일 분석 테스트"""
    print("\n" + "="*60)
    print("5. 로그 파일 분석 테스트")
    print("="*60)

    try:
        system = KeywordTrendSystem(analyzer_type='okt')

        # 로그 파일 분석
        results = system.analyze_from_logs('logs')

        if results:
            # 결과 요약 출력
            system.print_summary(results)

            # 리포트 생성
            report_files = system.generate_report(results)

            print(f"\n📊 생성된 리포트 ({len(report_files)}개):")
            for report_type, file_path in report_files.items():
                print(f"  - {report_type}: {file_path}")

            print("\n✅ 로그 파일 분석 테스트 완료")
        else:
            print("\n⚠️  분석 결과가 없습니다.")

    except Exception as e:
        print(f"\n❌ 로그 파일 분석 테스트 오류: {e}")
        import traceback
        traceback.print_exc()


def run_all_tests():
    """모든 테스트 실행"""
    print("\n" + "="*60)
    print("키워드 트렌드 분석 시스템 테스트")
    print("="*60)

    # 사전 요구사항 확인
    try:
        import konlpy
        print("✅ KoNLPy 설치됨")
    except ImportError:
        print("❌ KoNLPy 미설치")
        print("\n설치 방법:")
        print("1. Java JDK 8 이상 설치")
        print("2. pip install konlpy")
        return

    try:
        import networkx
        print("✅ NetworkX 설치됨")
    except ImportError:
        print("❌ NetworkX 미설치")
        print("pip install networkx")
        return

    try:
        from wordcloud import WordCloud
        print("✅ WordCloud 설치됨")
    except ImportError:
        print("❌ WordCloud 미설치")
        print("pip install wordcloud")
        return

    # 테스트 실행
    test_morpheme_analysis()
    test_trend_analysis()
    test_network_analysis()
    test_visualization()
    test_log_analysis()

    print("\n" + "="*60)
    print("모든 테스트 완료!")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()
