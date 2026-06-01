"""
HTML 리포트 템플릿 시스템

HTML 템플릿 기반 리포트 렌더링을 제공합니다.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)


class HTMLReportTemplate:
    """HTML 리포트 템플릿 클래스"""

    def __init__(self, template_dir: str = "report_templates", theme: str = "default"):
        """
        HTML 리포트 템플릿 초기화

        Args:
            template_dir: 템플릿 파일 디렉토리
            theme: 테마 이름 (default, dark, corporate, minimal)
        """
        self.template_dir = template_dir
        self.theme = theme
        self.template_cache = {}
        self.theme_styles = self._get_theme_styles(theme)
        self._ensure_template_dir()
        self._load_templates()

    def _ensure_template_dir(self):
        """템플릿 디렉토리 확인 및 생성"""
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
            logger.info(f"템플릿 디렉토리 생성: {self.template_dir}")

        # 하위 디렉토리 생성
        components_dir = os.path.join(self.template_dir, "components")
        if not os.path.exists(components_dir):
            os.makedirs(components_dir)

        # 테마 디렉토리 생성
        themes_dir = os.path.join(self.template_dir, "themes")
        if not os.path.exists(themes_dir):
            os.makedirs(themes_dir)

    def _load_templates(self):
        """템플릿 파일 로드"""
        template_files = [
            "base_report_template.html",
            "daily_summary_template.html",
            "weekly_analysis_template.html",
            "monthly_overview_template.html"
        ]

        for template_file in template_files:
            template_path = os.path.join(self.template_dir, template_file)
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    self.template_cache[template_file] = f.read()
                logger.info(f"템플릿 로드 완료: {template_file}")
            else:
                logger.warning(f"템플릿 파일 없음: {template_file}")

    def _load_component(self, component_name: str) -> str:
        """컴포넌트 템플릿 로드"""
        component_path = os.path.join(self.template_dir, "components", f"{component_name}.html")
        if os.path.exists(component_path):
            with open(component_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def _get_theme_styles(self, theme: str) -> Dict[str, str]:
        """테마별 스타일 정의"""
        theme_styles = {
            'default': {
                'primary_color': '#4a90e2',
                'secondary_color': '#357abd',
                'background_color': '#f5f5f5',
                'text_color': '#333',
                'heading_color': '#2c3e50',
                'border_color': '#ecf0f1',
                'success_color': '#27ae60',
                'error_color': '#c0392b',
                'warning_color': '#f39c12'
            },
            'dark': {
                'primary_color': '#5c9aff',
                'secondary_color': '#4a7cc9',
                'background_color': '#1a1a1a',
                'text_color': '#e0e0e0',
                'heading_color': '#ffffff',
                'border_color': '#333',
                'success_color': '#4cd964',
                'error_color': '#ff3b30',
                'warning_color': '#ffcc00'
            },
            'corporate': {
                'primary_color': '#2c5aa0',
                'secondary_color': '#1e3d6f',
                'background_color': '#f8f9fa',
                'text_color': '#231f20',
                'heading_color': '#1e3a8a',
                'border_color': '#d1d5db',
                'success_color': '#059669',
                'error_color': '#dc2626',
                'warning_color': '#d97706'
            },
            'minimal': {
                'primary_color': '#000000',
                'secondary_color': '#333333',
                'background_color': '#ffffff',
                'text_color': '#000000',
                'heading_color': '#000000',
                'border_color': '#e5e5e5',
                'success_color': '#16a34a',
                'error_color': '#dc2626',
                'warning_color': '#ca8a04'
            }
        }
        return theme_styles.get(theme, theme_styles['default'])

    def set_theme(self, theme: str) -> bool:
        """
        테마 변경

        Args:
            theme: 테마 이름

        Returns:
            변경 성공 여부
        """
        if theme in ['default', 'dark', 'corporate', 'minimal']:
            self.theme = theme
            self.theme_styles = self._get_theme_styles(theme)
            logger.info(f"테마 변경 완료: {theme}")
            return True
        else:
            logger.warning(f"잘못된 테마: {theme}")
            return False

    def get_available_themes(self) -> list:
        """사용 가능한 테마 목록 반환"""
        return ['default', 'dark', 'corporate', 'minimal']

    def apply_custom_styles(self, custom_styles: Dict[str, str]) -> bool:
        """
        사용자 정의 스타일 적용

        Args:
            custom_styles: 사용자 정의 스타일 딕셔너리

        Returns:
            적용 성공 여부
        """
        try:
            self.theme_styles.update(custom_styles)
            logger.info("사용자 정의 스타일 적용 완료")
            return True
        except Exception as e:
            logger.error(f"사용자 정의 스타일 적용 실패: {e}")
            return False

    def _render_template(self, template_content: str, context: Dict[str, Any]) -> str:
        """
        템플릿 렌더링 (단순 변수 치환)

        Args:
            template_content: 템플릿 내용
            context: 치환할 변수 딕셔너리

        Returns:
            렌더링된 HTML
        """
        rendered = template_content
        for key, value in context.items():
            placeholder = f"{{{{ {key} }}}}"
            rendered = rendered.replace(placeholder, str(value))
        return rendered

    def render_daily_summary(self, data: Dict[str, Any]) -> str:
        """
        일일 요약 리포트 렌더링

        Args:
            data: 리포트 데이터

        Returns:
            렌더링된 HTML
        """
        logger.info("일일 요약 리포트 렌더링 시작")

        # 기본 컨텍스트 구성
        context = self._build_base_context(data, "일일 요약 리포트", "daily")

        # 일일 리포트 특정 데이터
        context.update({
            'summary_content': self._render_summary_section(data),
            'top_keywords': self._render_top_keywords(data),
            'sentiment_overview': self._render_sentiment_overview(data),
            'recent_items': self._render_recent_items(data),
            'quick_stats': self._render_quick_stats(data)
        })

        # 기본 템플릿 사용 또는 전용 템플릿
        template_content = self.template_cache.get(
            "daily_summary_template.html",
            self._get_default_daily_template()
        )

        return self._render_template(template_content, context)

    def render_weekly_analysis(self, data: Dict[str, Any]) -> str:
        """
        주간 분석 리포트 렌더링

        Args:
            data: 리포트 데이터

        Returns:
            렌더링된 HTML
        """
        logger.info("주간 분석 리포트 렌더링 시작")

        # 기본 컨텍스트 구성
        context = self._build_base_context(data, "주간 분석 리포트", "weekly")

        # 주간 리포트 특정 데이터
        context.update({
            'weekly_summary': self._render_weekly_summary(data),
            'keyword_trends': self._render_keyword_trends(data),
            'sentiment_analysis': self._render_sentiment_analysis(data),
            'growth_metrics': self._render_growth_metrics(data),
            'recommendations': self._render_recommendations(data)
        })

        # 기본 템플릿 사용 또는 전용 템플릿
        template_content = self.template_cache.get(
            "weekly_analysis_template.html",
            self._get_default_weekly_template()
        )

        return self._render_template(template_content, context)

    def render_monthly_overview(self, data: Dict[str, Any]) -> str:
        """
        월간 개요 리포트 렌더링

        Args:
            data: 리포트 데이터

        Returns:
            렌더링된 HTML
        """
        logger.info("월간 개요 리포트 렌더링 시작")

        # 기본 컨텍스트 구성
        context = self._build_base_context(data, "월간 개요 리포트", "monthly")

        # 월간 리포트 특정 데이터
        context.update({
            'monthly_overview': self._render_monthly_overview(data),
            'detailed_trends': self._render_detailed_trends(data),
            'comprehensive_analysis': self._render_comprehensive_analysis(data),
            'yearly_comparison': self._render_yearly_comparison(data),
            'strategic_insights': self._render_strategic_insights(data)
        })

        # 기본 템플릿 사용 또는 전용 템플릿
        template_content = self.template_cache.get(
            "monthly_overview_template.html",
            self._get_default_monthly_template()
        )

        return self._render_template(template_content, context)

    def render_custom_report(self, template_name: str, data: Dict[str, Any]) -> str:
        """
        사용자 정의 리포트 렌더링

        Args:
            template_name: 템플릿 이름
            data: 리포트 데이터

        Returns:
            렌더링된 HTML
        """
        logger.info(f"사용자 정의 리포트 렌더링 시작: {template_name}")

        context = self._build_base_context(data, f"사용자 정의 리포트: {template_name}", "custom")
        context.update(data.get('custom_data', {}))

        template_content = self.template_cache.get(
            f"{template_name}.html",
            self._get_default_custom_template()
        )

        return self._render_template(template_content, context)

    def _build_base_context(self, data: Dict[str, Any], title: str, report_type: str) -> Dict[str, Any]:
        """기본 컨텍스트 구성"""
        now = datetime.now(pytz.timezone('Asia/Seoul'))

        return {
            'title': title,
            'report_type': report_type,
            'generated_at': now.strftime('%Y년 %m월 %d일 %H:%M:%S'),
            'generated_date': now.strftime('%Y-%m-%d'),
            'company_name': 'DealBot',
            'version': '1.0.0',
            'period': self._format_period(data),
            'total_items': data.get('summary', {}).get('total_items', 0)
        }

    def _format_period(self, data: Dict[str, Any]) -> str:
        """기간 포맷팅"""
        summary = data.get('summary', {})
        period = summary.get('period', {})

        start = period.get('start', '')
        end = period.get('end', '')

        if start and end:
            start_date = datetime.fromisoformat(start).strftime('%Y년 %m월 %d일')
            end_date = datetime.fromisoformat(end).strftime('%Y년 %m월 %d일')
            return f"{start_date} ~ {end_date}"
        return ""

    def _render_summary_section(self, data: Dict[str, Any]) -> str:
        """요약 섹션 렌더링"""
        summary = data.get('summary', {})
        period = summary.get('period', {})

        return f"""
        <div class="summary-section">
            <h3>📊 기간 개요</h3>
            <p><strong>분석 기간:</strong> {self._format_period(data)}</p>
            <p><strong>총 분석 항목:</strong> {summary.get('total_items', 0)}개</p>
            <p><strong>주요 키워드:</strong> {len(data.get('keyword_data', []))}개</p>
        </div>
        """

    def _render_top_keywords(self, data: Dict[str, Any]) -> str:
        """상위 키워드 렌더링"""
        keywords = data.get('keyword_data', [])

        if not keywords:
            return "<div class='top-keywords'><h3>🔥 상위 키워드</h3><p>데이터가 없습니다.</p></div>"

        keyword_rows = ""
        for i, keyword in enumerate(keywords[:10], 1):
            growth_emoji = "📈" if keyword.get('growth_rate', 0) > 0 else "📉"
            sentiment_emoji = {
                'positive': '😊',
                'negative': '😟',
                'neutral': '😐'
            }.get(keyword.get('sentiment', 'neutral'), '😐')

            keyword_rows += f"""
            <tr>
                <td>{i}</td>
                <td><strong>{keyword['keyword']}</strong></td>
                <td>{keyword['count']}</td>
                <td>{growth_emoji} {keyword.get('growth_rate', 0):.1f}%</td>
                <td>{sentiment_emoji} {keyword.get('sentiment', 'neutral')}</td>
            </tr>
            """

        return f"""
        <div class="top-keywords">
            <h3>🔥 상위 키워드</h3>
            <table>
                <thead>
                    <tr>
                        <th>순위</th>
                        <th>키워드</th>
                        <th>언급 수</th>
                        <th>성장률</th>
                        <th>감성</th>
                    </tr>
                </thead>
                <tbody>
                    {keyword_rows}
                </tbody>
            </table>
        </div>
        """

    def _render_sentiment_overview(self, data: Dict[str, Any]) -> str:
        """감성 개요 렌더링"""
        sentiment = data.get('sentiment_data', {})

        total = sentiment.get('total_items', 0)
        positive = sentiment.get('positive', 0)
        negative = sentiment.get('negative', 0)
        neutral = sentiment.get('neutral', 0)

        if total == 0:
            return "<div class='sentiment-overview'><h3>😊 감성 분석</h3><p>데이터가 없습니다.</p></div>"

        positive_pct = (positive / total) * 100
        negative_pct = (negative / total) * 100
        neutral_pct = (neutral / total) * 100

        return f"""
        <div class="sentiment-overview">
            <h3>😊 감성 분석</h3>
            <div class="sentiment-bars">
                <div class="sentiment-bar positive">
                    <span>긍정적</span>
                    <div class="bar" style="width: {positive_pct}%"></div>
                    <span>{positive_pct:.1f}%</span>
                </div>
                <div class="sentiment-bar neutral">
                    <span>중립적</span>
                    <div class="bar" style="width: {neutral_pct}%"></div>
                    <span>{neutral_pct:.1f}%</span>
                </div>
                <div class="sentiment-bar negative">
                    <span>부정적</span>
                    <div class="bar" style="width: {negative_pct}%"></div>
                    <span>{negative_pct:.1f}%</span>
                </div>
            </div>
            <p><strong>평균 감성 점수:</strong> {sentiment.get('average_score', 0):.2f}</p>
        </div>
        """

    def _render_recent_items(self, data: Dict[str, Any]) -> str:
        """최신 항목 렌더링"""
        recent_items = data.get('recent_items', [])

        if not recent_items:
            return "<div class='recent-items'><h3>📰 최신 항목</h3><p>데이터가 없습니다.</p></div>"

        items_html = ""
        for item in recent_items[:5]:
            items_html += f"""
            <div class="recent-item">
                <h4>{item.get('title', '제목 없음')}</h4>
                <p>{item.get('summary', '요약 없음')}</p>
                <p><strong>키워드:</strong> {', '.join(item.get('keywords', []))}</p>
                <p><strong>감성:</strong> {item.get('sentiment', 'neutral')}</p>
            </div>
            """

        return f"""
        <div class="recent-items">
            <h3>📰 최신 항목</h3>
            <div class="items-container">
                {items_html}
            </div>
        </div>
        """

    def _render_quick_stats(self, data: Dict[str, Any]) -> str:
        """빠른 통계 렌더링"""
        summary = data.get('summary', {})
        sentiment = data.get('sentiment_data', {})

        return f"""
        <div class="quick-stats">
            <h3>📈 빠른 통계</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-label">총 항목</span>
                    <span class="stat-value">{summary.get('total_items', 0)}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">키워드 수</span>
                    <span class="stat-value">{len(data.get('keyword_data', []))}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">긍정 비율</span>
                    <span class="stat-value">{(sentiment.get('positive', 0) / max(sentiment.get('total_items', 1), 1)) * 100:.1f}%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">평균 감성</span>
                    <span class="stat-value">{sentiment.get('average_score', 0):.2f}</span>
                </div>
            </div>
        </div>
        """

    def _render_weekly_summary(self, data: Dict[str, Any]) -> str:
        """주간 요약 렌더링"""
        return self._render_summary_section(data)

    def _render_keyword_trends(self, data: Dict[str, Any]) -> str:
        """키워드 트렌드 렌더링"""
        return self._render_top_keywords(data)

    def _render_sentiment_analysis(self, data: Dict[str, Any]) -> str:
        """감성 분석 렌더링"""
        sentiment = data.get('sentiment_data', {})

        analysis_html = f"""
        <div class="sentiment-analysis">
            <h3>😊 상세 감성 분석</h3>
            <p><strong>긍정적 단어:</strong> {', '.join(sentiment.get('top_positive_words', []))}</p>
            <p><strong>부정적 단어:</strong> {', '.join(sentiment.get('top_negative_words', []))}</p>
            {self._render_sentiment_overview(data)}
        </div>
        """

        return analysis_html

    def _render_growth_metrics(self, data: Dict[str, Any]) -> str:
        """성장 지표 렌더링"""
        growth = data.get('growth_metrics', {})

        if not growth:
            return "<div class='growth-metrics'><h3>📊 성장 지표</h3><p>데이터가 없습니다.</p></div>"

        current = growth.get('current_period', {})
        previous = growth.get('previous_period', {})
        growth_rate = growth.get('growth_percentage', 0)

        growth_emoji = "📈" if growth_rate > 0 else "📉"

        return f"""
        <div class="growth-metrics">
            <h3>📊 성장 지표</h3>
            <div class="growth-comparison">
                <div class="growth-period">
                    <h4>현재 기간</h4>
                    <p><strong>항목 수:</strong> {current.get('total_items', 0)}</p>
                </div>
                <div class="growth-period">
                    <h4>이전 기간</h4>
                    <p><strong>항목 수:</strong> {previous.get('total_items', 0)}</p>
                </div>
            </div>
            <p class="growth-rate">{growth_emoji} 성장률: {growth_rate:.2f}%</p>
        </div>
        """

    def _render_recommendations(self, data: Dict[str, Any]) -> str:
        """추천사항 렌더링"""
        return """
        <div class="recommendations">
            <h3>💡 추천사항</h3>
            <ul>
                <li>상위 키워드와 관련된 콘텐츠를 모니터링하세요.</li>
                <li>부정적 감성이 높은 키워드에 주의를 기울이세요.</li>
                <li>성장률이 높은 키워드를 집중적으로 분석하세요.</li>
                <li>정기적인 리포트를 통해 트렌드 변화를 추적하세요.</li>
            </ul>
        </div>
        """

    def _render_monthly_overview(self, data: Dict[str, Any]) -> str:
        """월간 개요 렌더링"""
        return self._render_summary_section(data)

    def _render_detailed_trends(self, data: Dict[str, Any]) -> str:
        """상세 트렌드 렌더링"""
        return self._render_keyword_trends(data)

    def _render_comprehensive_analysis(self, data: Dict[str, Any]) -> str:
        """포괄적 분석 렌더링"""
        return self._render_sentiment_analysis(data)

    def _render_yearly_comparison(self, data: Dict[str, Any]) -> str:
        """연간 비교 렌더링"""
        custom_data = data.get('custom_data', {})
        yearly = custom_data.get('yearly_comparison', {})

        if not yearly:
            return "<div class='yearly-comparison'><h3>📅 연간 비교</h3><p>데이터가 없습니다.</p></div>"

        current = yearly.get('current_year', {})
        previous = yearly.get('previous_year', {})
        yoy_growth = yearly.get('yoy_growth', 0)

        return f"""
        <div class="yearly-comparison">
            <h3>📅 연간 비교 (YoY)</h3>
            <div class="yearly-data">
                <div class="year-item">
                    <h4>금년 {current.get('month', 0)}월</h4>
                    <p><strong>항목 수:</strong> {current.get('total_items', 0)}</p>
                    <p><strong>평균 감성:</strong> {current.get('avg_sentiment', 0):.2f}</p>
                </div>
                <div class="year-item">
                    <h4>작년 {previous.get('month', 0)}월</h4>
                    <p><strong>항목 수:</strong> {previous.get('total_items', 0)}</p>
                    <p><strong>평균 감성:</strong> {previous.get('avg_sentiment', 0):.2f}</p>
                </div>
            </div>
            <p><strong>YoY 성장률:</strong> {yoy_growth:.2f}%</p>
        </div>
        """

    def _render_strategic_insights(self, data: Dict[str, Any]) -> str:
        """전략적 통찰 렌더링"""
        return """
        <div class="strategic-insights">
            <h3>🎯 전략적 통찰</h3>
            <ul>
                <li>계절성 패턴을 식별하고 마케팅 전략에 반영하세요.</li>
                <li>장기 트렌드 변화를 모니터링하여 비즈니스 기회를 포착하세요.</li>
                <li>경쟁사 활동과 시장 동향을 주기적으로 분석하세요.</li>
                <li>고객 선호도 변화에 따라 제품/서비스를 조정하세요.</li>
            </ul>
        </div>
        """

    def _get_default_daily_template(self) -> str:
        """기본 일일 리포트 템플릿"""
        return self._get_base_template() + """
        <div class="content">
            <h2>{{ title }}</h2>
            <p><strong>생성일:</strong> {{ generated_at }}</p>
            <p><strong>분석 기간:</strong> {{ period }}</p>

            {{ summary_content }}
            {{ quick_stats }}
            {{ top_keywords }}
            {{ sentiment_overview }}
            {{ recent_items }}
        </div>
        """

    def _get_default_weekly_template(self) -> str:
        """기본 주간 리포트 템플릿"""
        return self._get_base_template() + """
        <div class="content">
            <h2>{{ title }}</h2>
            <p><strong>생성일:</strong> {{ generated_at }}</p>
            <p><strong>분석 기간:</strong> {{ period }}</p>

            {{ weekly_summary }}
            {{ quick_stats }}
            {{ keyword_trends }}
            {{ sentiment_analysis }}
            {{ growth_metrics }}
            {{ recommendations }}
        </div>
        """

    def _get_default_monthly_template(self) -> str:
        """기본 월간 리포트 템플릿"""
        return self._get_base_template() + """
        <div class="content">
            <h2>{{ title }}</h2>
            <p><strong>생성일:</strong> {{ generated_at }}</p>
            <p><strong>분석 기간:</strong> {{ period }}</p>

            {{ monthly_overview }}
            {{ quick_stats }}
            {{ detailed_trends }}
            {{ comprehensive_analysis }}
            {{ yearly_comparison }}
            {{ strategic_insights }}
        </div>
        """

    def _get_default_custom_template(self) -> str:
        """기본 사용자 정의 리포트 템플릿"""
        return self._get_base_template() + """
        <div class="content">
            <h2>{{ title }}</h2>
            <p><strong>생성일:</strong> {{ generated_at }}</p>

            <div class="custom-content">
                <p>사용자 정의 리포트 내용이 여기에 표시됩니다.</p>
            </div>
        </div>
        """

    def _get_base_template(self) -> str:
        """기본 템플릿 (헤더, 스타일, 푸터)"""
        styles = self.theme_styles
        return f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{{{{ title }}}}</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}

                body {{
                    font-family: 'Noto Sans KR', sans-serif;
                    line-height: 1.6;
                    color: {styles['text_color']};
                    background-color: {styles['background_color']};
                    padding: 20px;
                }}

                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}

                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid {styles['primary_color']};
                }}

                .header h1 {{
                    color: {styles['primary_color']};
                    font-size: 28px;
                    margin-bottom: 10px;
                }}

                .header .meta {{
                    color: #666;
                    font-size: 14px;
                }}

                .content {{
                    margin-bottom: 40px;
                }}

                .content h2 {{
                    color: {styles['heading_color']};
                    font-size: 24px;
                    margin-bottom: 20px;
                }}

                .content h3 {{
                    color: {styles['heading_color']};
                    font-size: 18px;
                    margin: 25px 0 15px 0;
                    padding-bottom: 8px;
                    border-bottom: 1px solid {styles['border_color']};
                }}

                .content h4 {{
                    color: {styles['text_color']};
                    font-size: 16px;
                    margin: 15px 0 10px 0;
                }}

                .content p {{
                    margin-bottom: 15px;
                    color: {styles['text_color']};
                }}

                .content strong {{
                    color: {styles['heading_color']};
                }}

                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}

                thead {{
                    background-color: #f8f9fa;
                }}

                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}

                th {{
                    font-weight: 600;
                    color: {styles['heading_color']};
                }}

                tbody tr:hover {{
                    background-color: #f8f9fa;
                }}

                .sentiment-bars {{
                    margin: 20px 0;
                }}

                .sentiment-bar {{
                    margin-bottom: 15px;
                }}

                .sentiment-bar span {{
                    display: inline-block;
                    width: 100px;
                    font-weight: 500;
                }}

                .sentiment-bar .bar {{
                    display: inline-block;
                    height: 20px;
                    background: linear-gradient(to right, {styles['primary_color']}, {styles['secondary_color']});
                    border-radius: 3px;
                }}

                .sentiment-bar.positive .bar {{
                    background: linear-gradient(to right, {styles['success_color']}, #2ecc71);
                }}

                .sentiment-bar.negative .bar {{
                    background: linear-gradient(to right, {styles['error_color']}, #e74c3c);
                }}

                .sentiment-bar.neutral .bar {{
                    background: linear-gradient(to right, #7f8c8d, #95a5a6);
                }}

                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }}

                .stat-item {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 6px;
                    text-align: center;
                }}

                .stat-label {{
                    display: block;
                    color: #666;
                    font-size: 14px;
                    margin-bottom: 10px;
                }}

                .stat-value {{
                    display: block;
                    color: {styles['primary_color']};
                    font-size: 24px;
                    font-weight: 700;
                }}

                .recent-item {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 6px;
                    margin-bottom: 15px;
                    border-left: 4px solid {styles['primary_color']};
                }}

                .growth-comparison {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin: 20px 0;
                }}

                .growth-period {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 6px;
                }}

                .growth-rate {{
                    font-size: 18px;
                    font-weight: 600;
                    color: {styles['success_color']};
                    text-align: center;
                    margin: 20px 0;
                }}

                .yearly-data {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin: 20px 0;
                }}

                .year-item {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 6px;
                }}

                ul, ol {{
                    margin-left: 30px;
                    margin-bottom: 20px;
                }}

                li {{
                    margin-bottom: 8px;
                    color: {styles['text_color']};
                }}

                .footer {{
                    text-align: center;
                    padding-top: 20px;
                    border-top: 1px solid {styles['border_color']};
                    color: #666;
                    font-size: 12px;
                }}

                @media print {{
                    body {{
                        background: white;
                        padding: 0;
                    }}

                    .container {{
                        box-shadow: none;
                        padding: 20px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{{{{ title }}}}</h1>
                    <div class="meta">
                        <p>{{{{ company_name }}}} | 버전 {{{{ version }}}}</p>
                        <p>{{{{ generated_at }}}}</p>
                    </div>
                </div>
        """

    def add_footer_to_template(self, html_content: str) -> str:
        """템플릿에 푸터 추가"""
        footer = """
                <div class="footer">
                    <p>이 리포트는 DealBot 자동 리포트 시스템에 의해 생성되었습니다.</p>
                    <p>문의사항이 있으시면 관리자에게 연락해 주세요.</p>
                    <p>&copy; {{ generated_date }} DealBot. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html_content + footer