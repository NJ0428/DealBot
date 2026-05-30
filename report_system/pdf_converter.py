"""
PDF 변환 모듈

HTML 내용을 PDF로 변환하는 기능을 제공합니다.
"""

import os
import logging
import tempfile
from typing import Optional, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class PDFConverter:
    """HTML to PDF 변환 클래스"""

    def __init__(self, config=None):
        """
        PDF 변환기 초기화

        Args:
            config: PDF 설정 객체
        """
        self.config = config or self._get_default_config()
        self._weasyprint_available = self._check_weasyprint()

        if not self._weasyprint_available:
            logger.warning("WeasyPrint를 사용할 수 없습니다. 설치를 확인해주세요.")

    def _get_default_config(self):
        """기본 설정 반환"""
        from .config import PDFSettings
        return PDFSettings()

    def _check_weasyprint(self) -> bool:
        """WeasyPrint 사용 가능 여부 확인"""
        try:
            import weasyprint
            logger.info("WeasyPrint 라이브러리를 찾았습니다.")
            return True
        except ImportError:
            logger.warning("WeasyPrint 라이브러리를 찾을 수 없습니다.")
            logger.warning("설치 명령어: pip install weasyprint")
            return False

    def convert_html_to_pdf(self, html_content: str, output_path: str) -> bool:
        """
        HTML 내용을 PDF로 변환

        Args:
            html_content: HTML 내용
            output_path: 출력 PDF 파일 경로

        Returns:
            변환 성공 여부
        """
        if not self._weasyprint_available:
            logger.error("WeasyPrint를 사용할 수 없어 PDF 변환을 수행할 수 없습니다.")
            return False

        try:
            logger.info(f"PDF 변환 시작: {output_path}")

            # 출력 디렉토리 생성
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # WeasyPrint 임포트
            from weasyprint import HTML, CSS

            # HTML 변환
            html_doc = HTML(string=html_content, base_url='.')

            # PDF 설정 적용
            pdf_kwargs = {
                'presentational_hints': True,
            }

            # 페이지 설정
            if self.config.page_size:
                pdf_kwargs['pagesize'] = self.config.page_size

            # 변환 수행
            html_doc.write_pdf(
                target=output_path,
                stylesheets=self._get_default_stylesheets(),
                **pdf_kwargs
            )

            logger.info(f"PDF 변환 완료: {output_path}")
            return True

        except Exception as e:
            logger.error(f"PDF 변환 실패: {e}")
            return False

    def convert_url_to_pdf(self, url: str, output_path: str) -> bool:
        """
        URL을 PDF로 변환

        Args:
            url: 변환할 URL
            output_path: 출력 PDF 파일 경로

        Returns:
            변환 성공 여부
        """
        if not self._weasyprint_available:
            logger.error("WeasyPrint를 사용할 수 없어 PDF 변환을 수행할 수 없습니다.")
            return False

        try:
            logger.info(f"URL PDF 변환 시작: {url} -> {output_path}")

            # 출력 디렉토리 생성
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # WeasyPrint 임포트
            from weasyprint import HTML

            # URL 변환
            html_doc = HTML(url=url)

            # 변환 수행
            html_doc.write_pdf(
                target=output_path,
                stylesheets=self._get_default_stylesheets()
            )

            logger.info(f"URL PDF 변환 완료: {output_path}")
            return True

        except Exception as e:
            logger.error(f"URL PDF 변환 실패: {e}")
            return False

    def convert_html_file_to_pdf(self, html_file_path: str, output_path: str) -> bool:
        """
        HTML 파일을 PDF로 변환

        Args:
            html_file_path: HTML 파일 경로
            output_path: 출력 PDF 파일 경로

        Returns:
            변환 성공 여부
        """
        if not os.path.exists(html_file_path):
            logger.error(f"HTML 파일을 찾을 수 없습니다: {html_file_path}")
            return False

        try:
            logger.info(f"HTML 파일 PDF 변환 시작: {html_file_path} -> {output_path}")

            # HTML 파일 읽기
            with open(html_file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # PDF 변환
            return self.convert_html_to_pdf(html_content, output_path)

        except Exception as e:
            logger.error(f"HTML 파일 PDF 변환 실패: {e}")
            return False

    def add_watermark(self, pdf_path: str, watermark_text: str, output_path: Optional[str] = None) -> bool:
        """
        PDF에 워터마크 추가

        Args:
            pdf_path: 입력 PDF 파일 경로
            watermark_text: 워터마크 텍스트
            output_path: 출력 PDF 파일 경로 (None인 경우 원본 파일 덮어쓰기)

        Returns:
            성공 여부
        """
        if not self._weasyprint_available:
            logger.error("WeasyPrint를 사용할 수 없어 워터마크 추가를 수행할 수 없습니다.")
            return False

        if not os.path.exists(pdf_path):
            logger.error(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
            return False

        try:
            logger.info(f"워터마크 추가 시작: {pdf_path}")

            # 출력 경로 설정
            if output_path is None:
                output_path = pdf_path

            # WeasyPrint를 사용한 워터마크 추가
            from weasyprint import HTML, CSS

            # 워터마크 HTML 생성
            watermark_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    @page {{
                        size: A4;
                        @top-center {{
                            content: "{watermark_text}";
                            font-size: 12px;
                            color: rgba(0, 0, 0, 0.3);
                            font-family: Arial, sans-serif;
                        }}
                    }}
                    body {{
                        margin: 0;
                        padding: 0;
                    }}
                </style>
            </head>
            <body>
                <object data="file://{pdf_path}" type="application/pdf" width="100%" height="100%"></object>
            </body>
            </html>
            """

            # 임시 파일로 변환 후 복사
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
                f.write(watermark_html)
                temp_html = f.name

            try:
                HTML(temp_html).write_pdf(output_path)
                logger.info(f"워터마크 추가 완료: {output_path}")
                return True
            finally:
                if os.path.exists(temp_html):
                    os.remove(temp_html)

        except Exception as e:
            logger.error(f"워터마크 추가 실패: {e}")
            return False

    def merge_pdfs(self, pdf_paths: List[str], output_path: str) -> bool:
        """
        여러 PDF 파일 병합

        Args:
            pdf_paths: 병합할 PDF 파일 경로 목록
            output_path: 출력 PDF 파일 경로

        Returns:
            성공 여부
        """
        if not pdf_paths:
            logger.error("병합할 PDF 파일이 없습니다.")
            return False

        try:
            logger.info(f"PDF 병합 시작: {len(pdf_paths)}개 파일")

            # 모든 파일 존재 확인
            for pdf_path in pdf_paths:
                if not os.path.exists(pdf_path):
                    logger.error(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
                    return False

            # PyPDF2를 사용한 병합
            try:
                from PyPDF2 import PdfMerger

                merger = PdfMerger()

                for pdf_path in pdf_paths:
                    merger.append(pdf_path)

                merger.write(output_path)
                merger.close()

                logger.info(f"PDF 병합 완료: {output_path}")
                return True

            except ImportError:
                logger.warning("PyPDF2를 사용할 수 없습니다. 설치를 확인해주세요.")
                logger.warning("설치 명령어: pip install PyPDF2")
                return False

        except Exception as e:
            logger.error(f"PDF 병합 실패: {e}")
            return False

    def get_pdf_info(self, pdf_path: str) -> dict:
        """
        PDF 파일 정보 가져오기

        Args:
            pdf_path: PDF 파일 경로

        Returns:
            PDF 정보 딕셔너리
        """
        if not os.path.exists(pdf_path):
            logger.error(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
            return {}

        try:
            info = {
                'path': pdf_path,
                'size_bytes': os.path.getsize(pdf_path),
                'size_mb': os.path.getsize(pdf_path) / (1024 * 1024),
                'created_at': datetime.fromtimestamp(os.path.getctime(pdf_path)).isoformat(),
                'modified_at': datetime.fromtimestamp(os.path.getmtime(pdf_path)).isoformat(),
                'pages': 0
            }

            # 페이지 수 가져오기
            try:
                from PyPDF2 import PdfReader

                with open(pdf_path, 'rb') as f:
                    reader = PdfReader(f)
                    info['pages'] = len(reader.pages)

            except ImportError:
                logger.warning("PyPDF2를 사용할 수 없어 페이지 수를 가져올 수 없습니다.")

            return info

        except Exception as e:
            logger.error(f"PDF 정보 가져오기 실패: {e}")
            return {}

    def optimize_pdf(self, input_path: str, output_path: str) -> bool:
        """
        PDF 파일 최적화 (압축)

        Args:
            input_path: 입력 PDF 파일 경로
            output_path: 출력 PDF 파일 경로

        Returns:
            성공 여부
        """
        if not os.path.exists(input_path):
            logger.error(f"PDF 파일을 찾을 수 없습니다: {input_path}")
            return False

        try:
            logger.info(f"PDF 최적화 시작: {input_path}")

            # WeasyPrint를 사용한 재변환 (압축)
            from weasyprint import HTML

            # HTML 파일로 변환했다가 다시 PDF로 변환
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
                f.write(f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        @page {{
                            size: A4;
                            margin: 20mm;
                        }}
                        body {{
                            font-family: Arial, sans-serif;
                            margin: 0;
                            padding: 0;
                        }}
                    </style>
                </head>
                <body>
                    <object data="file://{input_path}" type="application/pdf" width="100%" height="100%"></object>
                </body>
                </html>
                """)
                temp_html = f.name

            try:
                HTML(temp_html).write_pdf(output_path)
                logger.info(f"PDF 최적화 완료: {output_path}")
                return True
            finally:
                if os.path.exists(temp_html):
                    os.remove(temp_html)

        except Exception as e:
            logger.error(f"PDF 최적화 실패: {e}")
            return False

    def _get_default_stylesheets(self):
        """기본 스타일시트 반환"""
        from weasyprint import CSS

        styles = []

        # 기본 CSS 스타일
        base_css = """
        @page {
            size: A4;
            margin: 20mm;
        }

        @font-face {
            font-family: 'Noto Sans KR';
            src: local('Noto Sans KR');
        }

        body {
            font-family: 'Noto Sans KR', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }

        .page-break {
            page-break-after: always;
        }

        .no-break {
            page-break-inside: avoid;
        }
        """

        try:
            styles.append(CSS(string=base_css))
        except Exception as e:
            logger.warning(f"기본 스타일시트 적용 실패: {e}")

        return styles

    def create_pdf_from_template(self, template_name: str, context: dict, output_path: str) -> bool:
        """
        템플릿에서 PDF 생성

        Args:
            template_name: 템플릿 이름
            context: 템플릿 변수 딕셔너리
            output_path: 출력 PDF 파일 경로

        Returns:
            성공 여부
        """
        try:
            from .html_report_template import HTMLReportTemplate

            template_renderer = HTMLReportTemplate()

            # 템플릿 렌더링
            if template_name == "daily":
                html_content = template_renderer.render_daily_summary(context)
            elif template_name == "weekly":
                html_content = template_renderer.render_weekly_analysis(context)
            elif template_name == "monthly":
                html_content = template_renderer.render_monthly_overview(context)
            else:
                html_content = template_renderer.render_custom_report(template_name, context)

            # PDF 변환
            return self.convert_html_to_pdf(html_content, output_path)

        except Exception as e:
            logger.error(f"템플릿 PDF 생성 실패: {e}")
            return False

    def batch_convert_html_to_pdf(self, html_files: List[tuple], output_dir: str) -> dict:
        """
        여러 HTML 파일을 일괄 PDF로 변환

        Args:
            html_files: (html_content, output_filename) 튜플 목록
            output_dir: 출력 디렉토리

        Returns:
            변환 결과 딕셔너리
        """
        results = {
            'success': [],
            'failed': [],
            'total': len(html_files)
        }

        os.makedirs(output_dir, exist_ok=True)

        for html_content, output_filename in html_files:
            output_path = os.path.join(output_dir, output_filename)

            if self.convert_html_to_pdf(html_content, output_path):
                results['success'].append(output_filename)
                logger.info(f"일괄 변환 성공: {output_filename}")
            else:
                results['failed'].append(output_filename)
                logger.error(f"일괄 변환 실패: {output_filename}")

        logger.info(f"일괄 변환 완료: {len(results['success'])}/{len(html_files)} 성공")

        return results


class PDFGenerationError(Exception):
    """PDF 생성 예외"""
    pass


class PDFConfigError(Exception):
    """PDF 설정 예외"""
    pass


def validate_pdf_path(pdf_path: str) -> bool:
    """
    PDF 파일 경로 유효성 검사

    Args:
        pdf_path: PDF 파일 경로

    Returns:
        유효성 여부
    """
    if not pdf_path:
        return False

    if not pdf_path.endswith('.pdf'):
        logger.warning("PDF 파일 경로가 .pdf로 끝나지 않습니다.")
        return False

    # 경로에 사용할 수 없는 문자 확인
    invalid_chars = '<>:"|?*'
    for char in invalid_chars:
        if char in pdf_path:
            logger.warning(f"PDF 파일 경로에 사용할 수 없는 문자가 포함되어 있습니다: {char}")
            return False

    return True


def get_pdf_filename(report_type: str, date: datetime = None, prefix: str = "report") -> str:
    """
    PDF 파일명 생성

    Args:
        report_type: 리포트 타입 (daily, weekly, monthly)
        date: 날짜 (None인 경우 현재 날짜 사용)
        prefix: 파일명 접두사

    Returns:
        PDF 파일명
    """
    if date is None:
        date = datetime.now()

    date_str = date.strftime('%Y%m%d')
    return f"{prefix}_{report_type}_{date_str}.pdf"