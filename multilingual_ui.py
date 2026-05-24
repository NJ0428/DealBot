#!/usr/bin/env python3
"""
다국어 UI 번역 시스템
웹 인터페이스의 다국어 지원을 제공합니다.
"""

import json
from pathlib import Path
from typing import Dict, Optional, List
from flask import request, g
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class LanguageCode:
    """언어 코드 상수"""
    KOREAN = "ko"
    ENGLISH = "en"
    JAPANESE = "ja"
    CHINESE = "zh"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    RUSSIAN = "ru"
    ARABIC = "ar"
    PORTUGUESE = "pt"
    ITALIAN = "it"


class LanguageInfo:
    """언어 정보"""

    SUPPORTED_LANGUAGES = {
        LanguageCode.KOREAN: {
            "name": "한국어",
            "native_name": "한국어",
            "flag": "🇰🇷",
            "direction": "ltr",
            "locale": "ko_KR"
        },
        LanguageCode.ENGLISH: {
            "name": "English",
            "native_name": "English",
            "flag": "🇺🇸",
            "direction": "ltr",
            "locale": "en_US"
        },
        LanguageCode.JAPANESE: {
            "name": "Japanese",
            "native_name": "日本語",
            "flag": "🇯🇵",
            "direction": "ltr",
            "locale": "ja_JP"
        },
        LanguageCode.CHINESE: {
            "name": "Chinese",
            "native_name": "中文",
            "flag": "🇨🇳",
            "direction": "ltr",
            "locale": "zh_CN"
        },
        LanguageCode.SPANISH: {
            "name": "Spanish",
            "native_name": "Español",
            "flag": "🇪🇸",
            "direction": "ltr",
            "locale": "es_ES"
        },
        LanguageCode.FRENCH: {
            "name": "French",
            "native_name": "Français",
            "flag": "🇫🇷",
            "direction": "ltr",
            "locale": "fr_FR"
        },
        LanguageCode.GERMAN: {
            "name": "German",
            "native_name": "Deutsch",
            "flag": "🇩🇪",
            "direction": "ltr",
            "locale": "de_DE"
        },
        LanguageCode.RUSSIAN: {
            "name": "Russian",
            "native_name": "Русский",
            "flag": "🇷🇺",
            "direction": "ltr",
            "locale": "ru_RU"
        },
        LanguageCode.ARABIC: {
            "name": "Arabic",
            "native_name": "العربية",
            "flag": "🇸🇦",
            "direction": "rtl",
            "locale": "ar_SA"
        },
        LanguageCode.PORTUGUESE: {
            "name": "Portuguese",
            "native_name": "Português",
            "flag": "🇧🇷",
            "direction": "ltr",
            "locale": "pt_BR"
        },
        LanguageCode.ITALIAN: {
            "name": "Italian",
            "native_name": "Italiano",
            "flag": "🇮🇹",
            "direction": "ltr",
            "locale": "it_IT"
        }
    }

    @classmethod
    def get_language_info(cls, lang_code: str) -> Optional[Dict]:
        """언어 정보 반환"""
        return cls.SUPPORTED_LANGUAGES.get(lang_code)

    @classmethod
    def get_all_languages(cls) -> Dict[str, Dict]:
        """모든 지원 언어 반환"""
        return cls.SUPPORTED_LANGUAGES.copy()

    @classmethod
    def is_supported(cls, lang_code: str) -> bool:
        """언어 지원 여부 확인"""
        return lang_code in cls.SUPPORTED_LANGUAGES

    @classmethod
    def get_default_language(cls) -> str:
        """기본 언어 반환"""
        return LanguageCode.KOREAN


class UITranslations:
    """UI 번역 데이터"""

    TRANSLATIONS = {
        # 공통
        "common": {
            LanguageCode.KOREAN: {
                "app_name": "DealBot",
                "app_subtitle": "웹 주제 크롤러 및 Excel 저장 프로그램",
                "home": "홈",
                "search_history": "검색 이력",
                "language": "언어",
                "settings": "설정",
                "logout": "로그아웃",
                "loading": "로딩 중...",
                "error": "오류",
                "success": "성공",
                "warning": "경고",
                "info": "정보",
                "cancel": "취소",
                "confirm": "확인",
                "save": "저장",
                "delete": "삭제",
                "edit": "편집",
                "back": "뒤로",
                "next": "다음",
                "previous": "이전",
                "close": "닫기",
                "search": "검색",
                "download": "다운로드",
                "upload": "업로드",
                "submit": "제출",
                "reset": "초기화",
                "refresh": "새로고침",
                "export": "내보내기",
                "import": "가져오기",
                "total": "전체",
                "filter": "필터",
                "sort": "정렬",
                "view": "보기",
                "add": "추가",
                "remove": "제거",
                "yes": "예",
                "no": "아니오",
                "or": "또는",
                "and": "그리고",
                "all": "전체",
                "none": "없음",
                "search_placeholder": "검색어를 입력하세요...",
                "no_results": "결과가 없습니다",
                "please_wait": "잠시 기다려주세요",
                "operation_complete": "작업 완료",
                "operation_failed": "작업 실패"
            },
            LanguageCode.ENGLISH: {
                "app_name": "DealBot",
                "app_subtitle": "Web Topic Crawler and Excel Storage Program",
                "home": "Home",
                "search_history": "Search History",
                "language": "Language",
                "settings": "Settings",
                "logout": "Logout",
                "loading": "Loading...",
                "error": "Error",
                "success": "Success",
                "warning": "Warning",
                "info": "Info",
                "cancel": "Cancel",
                "confirm": "Confirm",
                "save": "Save",
                "delete": "Delete",
                "edit": "Edit",
                "back": "Back",
                "next": "Next",
                "previous": "Previous",
                "close": "Close",
                "search": "Search",
                "download": "Download",
                "upload": "Upload",
                "submit": "Submit",
                "reset": "Reset",
                "refresh": "Refresh",
                "export": "Export",
                "import": "Import",
                "total": "Total",
                "filter": "Filter",
                "sort": "Sort",
                "view": "View",
                "add": "Add",
                "remove": "Remove",
                "yes": "Yes",
                "no": "No",
                "or": "Or",
                "and": "And",
                "all": "All",
                "none": "None",
                "search_placeholder": "Enter search keyword...",
                "no_results": "No results found",
                "please_wait": "Please wait",
                "operation_complete": "Operation completed",
                "operation_failed": "Operation failed"
            },
            LanguageCode.JAPANESE: {
                "app_name": "DealBot",
                "app_subtitle": "WebトピッククローラーとExcel保存プログラム",
                "home": "ホーム",
                "search_history": "検索履歴",
                "language": "言語",
                "settings": "設定",
                "logout": "ログアウト",
                "loading": "読み込み中...",
                "error": "エラー",
                "success": "成功",
                "warning": "警告",
                "info": "情報",
                "cancel": "キャンセル",
                "confirm": "確認",
                "save": "保存",
                "delete": "削除",
                "edit": "編集",
                "back": "戻る",
                "next": "次へ",
                "previous": "前へ",
                "close": "閉じる",
                "search": "検索",
                "download": "ダウンロード",
                "upload": "アップロード",
                "submit": "送信",
                "reset": "リセット",
                "refresh": "更新",
                "export": "エクスポート",
                "import": "インポート",
                "total": "合計",
                "filter": "フィルター",
                "sort": "ソート",
                "view": "表示",
                "add": "追加",
                "remove": "削除",
                "yes": "はい",
                "no": "いいえ",
                "or": "または",
                "and": "そして",
                "all": "すべて",
                "none": "なし",
                "search_placeholder": "検索キーワードを入力...",
                "no_results": "結果が見つかりません",
                "please_wait": "お待ちください",
                "operation_complete": "操作完了",
                "operation_failed": "操作失敗"
            },
            LanguageCode.CHINESE: {
                "app_name": "DealBot",
                "app_subtitle": "网络主题爬虫和Excel存储程序",
                "home": "首页",
                "search_history": "搜索历史",
                "language": "语言",
                "settings": "设置",
                "logout": "登出",
                "loading": "加载中...",
                "error": "错误",
                "success": "成功",
                "warning": "警告",
                "info": "信息",
                "cancel": "取消",
                "confirm": "确认",
                "save": "保存",
                "delete": "删除",
                "edit": "编辑",
                "back": "返回",
                "next": "下一步",
                "previous": "上一步",
                "close": "关闭",
                "search": "搜索",
                "download": "下载",
                "upload": "上传",
                "submit": "提交",
                "reset": "重置",
                "refresh": "刷新",
                "export": "导出",
                "import": "导入",
                "total": "总计",
                "filter": "筛选",
                "sort": "排序",
                "view": "查看",
                "add": "添加",
                "remove": "移除",
                "yes": "是",
                "no": "否",
                "or": "或",
                "and": "和",
                "all": "全部",
                "none": "无",
                "search_placeholder": "请输入搜索关键词...",
                "no_results": "未找到结果",
                "please_wait": "请稍候",
                "operation_complete": "操作完成",
                "operation_failed": "操作失败"
            }
        },

        # 네비게이션
        "nav": {
            LanguageCode.KOREAN: {
                "search": "검색",
                "results": "결과",
                "analysis": "분석",
                "settings": "설정",
                "about": "정보",
                "help": "도움말"
            },
            LanguageCode.ENGLISH: {
                "search": "Search",
                "results": "Results",
                "analysis": "Analysis",
                "settings": "Settings",
                "about": "About",
                "help": "Help"
            },
            LanguageCode.JAPANESE: {
                "search": "検索",
                "results": "結果",
                "analysis": "分析",
                "settings": "設定",
                "about": "について",
                "help": "ヘルプ"
            },
            LanguageCode.CHINESE: {
                "search": "搜索",
                "results": "结果",
                "analysis": "分析",
                "settings": "设置",
                "about": "关于",
                "help": "帮助"
            }
        },

        # 검색 페이지
        "search_page": {
            LanguageCode.KOREAN: {
                "title": "웹 검색",
                "subtitle": "다양한 소스에서 정보를 수집합니다",
                "keyword_label": "검색어",
                "keyword_placeholder": "검색어를 입력하세요...",
                "max_results_label": "최대 결과 수",
                "search_type_label": "검색 유형",
                "naver_blog": "네이버 블로그",
                "google_news": "구글 뉴스",
                "multiple_search": "다중 검색",
                "enable_sentiment": "감정 분석 활성화",
                "start_search": "검색 시작",
                "searching": "검색 중...",
                "features_title": "기능",
                "fast_search": "빠른 검색",
                "fast_search_desc": "최적화된 크롤링으로 빠른 결과 제공",
                "excel_save": "Excel 저장",
                "excel_save_desc": "검색 결과를 엑셀 파일로 다운로드",
                "rss_feed": "RSS 피드",
                "rss_feed_desc": "RSS 피드 구독 및 알림 기능",
                "multilingual": "다국어 지원",
                "multilingual_desc": "다국어 검색 및 번역 기능",
                "sentiment_analysis": "감정 분석",
                "sentiment_analysis_desc": "AI 기반 감정 분석 및 통계"
            },
            LanguageCode.ENGLISH: {
                "title": "Web Search",
                "subtitle": "Collect information from various sources",
                "keyword_label": "Keyword",
                "keyword_placeholder": "Enter search keyword...",
                "max_results_label": "Max Results",
                "search_type_label": "Search Type",
                "naver_blog": "Naver Blog",
                "google_news": "Google News",
                "multiple_search": "Multiple Search",
                "enable_sentiment": "Enable Sentiment Analysis",
                "start_search": "Start Search",
                "searching": "Searching...",
                "features_title": "Features",
                "fast_search": "Fast Search",
                "fast_search_desc": "Optimized crawling for quick results",
                "excel_save": "Excel Save",
                "excel_save_desc": "Download search results as Excel files",
                "rss_feed": "RSS Feed",
                "rss_feed_desc": "RSS feed subscription and notifications",
                "multilingual": "Multilingual Support",
                "multilingual_desc": "Multilingual search and translation features",
                "sentiment_analysis": "Sentiment Analysis",
                "sentiment_analysis_desc": "AI-powered sentiment analysis and statistics"
            },
            LanguageCode.JAPANESE: {
                "title": "Web検索",
                "subtitle": "様々なソースから情報を収集",
                "keyword_label": "検索キーワード",
                "keyword_placeholder": "検索キーワードを入力...",
                "max_results_label": "最大結果数",
                "search_type_label": "検索タイプ",
                "naver_blog": "NAVERブログ",
                "google_news": "Googleニュース",
                "multiple_search": "複数検索",
                "enable_sentiment": "感情分析を有効化",
                "start_search": "検索開始",
                "searching": "検索中...",
                "features_title": "機能",
                "fast_search": "高速検索",
                "fast_search_desc": "最適化されたクローリングで迅速な結果",
                "excel_save": "Excel保存",
                "excel_save_desc": "検索結果をExcelファイルでダウンロード",
                "rss_feed": "RSSフィード",
                "rss_feed_desc": "RSSフィード購読と通知機能",
                "multilingual": "多言語対応",
                "multilingual_desc": "多言語検索と翻訳機能",
                "sentiment_analysis": "感情分析",
                "sentiment_analysis_desc": "AIによる感情分析と統計"
            },
            LanguageCode.CHINESE: {
                "title": "网络搜索",
                "subtitle": "从各种来源收集信息",
                "keyword_label": "搜索关键词",
                "keyword_placeholder": "请输入搜索关键词...",
                "max_results_label": "最大结果数",
                "search_type_label": "搜索类型",
                "naver_blog": "Naver博客",
                "google_news": "Google新闻",
                "multiple_search": "多重搜索",
                "enable_sentiment": "启用情感分析",
                "start_search": "开始搜索",
                "searching": "搜索中...",
                "features_title": "功能",
                "fast_search": "快速搜索",
                "fast_search_desc": "优化的爬虫提供快速结果",
                "excel_save": "Excel保存",
                "excel_save_desc": "将搜索结果下载为Excel文件",
                "rss_feed": "RSS订阅",
                "rss_feed_desc": "RSS订阅和通知功能",
                "multilingual": "多语言支持",
                "multilingual_desc": "多语言搜索和翻译功能",
                "sentiment_analysis": "情感分析",
                "sentiment_analysis_desc": "AI驱动的情感分析和统计"
            }
        },

        # 결과 페이지
        "results_page": {
            LanguageCode.KOREAN: {
                "title": "검색 결과",
                "back_to_search": "다시 검색",
                "results_list": "결과 목록",
                "first_n_items": "처음 50개",
                "download_excel": "Excel 다운로드",
                "download_csv": "CSV 다운로드",
                "export_results": "결과 내보내기",
                "stats_title": "통계",
                "total_results": "총 결과 수",
                "successful": "성공",
                "failed": "실패",
                "search_time": "검색 시간",
                "table_headers": {
                    "index": "순번",
                    "title": "제목",
                    "url": "URL",
                    "blog_name": "블로그명",
                    "date": "날짜",
                    "status": "상태",
                    "sentiment": "감정",
                    "language": "언어",
                    "score": "점수"
                },
                "sentiment_stats": {
                    "positive": "긍정",
                    "negative": "부정",
                    "neutral": "중립",
                    "avg_score": "평균 점수",
                    "positive_ratio": "긍정 비율",
                    "negative_ratio": "부정 비율",
                    "neutral_ratio": "중립 비율"
                },
                "filter_by_sentiment": "감정별 필터링",
                "all_sentiments": "전체 감정",
                "show_positive": "긍정만 보기",
                "show_negative": "부정만 보기",
                "show_neutral": "중립만 보기",
                "no_matching_results": "일치하는 결과가 없습니다"
            },
            LanguageCode.ENGLISH: {
                "title": "Search Results",
                "back_to_search": "Search Again",
                "results_list": "Results List",
                "first_n_items": "First 50",
                "download_excel": "Download Excel",
                "download_csv": "Download CSV",
                "export_results": "Export Results",
                "stats_title": "Statistics",
                "total_results": "Total Results",
                "successful": "Successful",
                "failed": "Failed",
                "search_time": "Search Time",
                "table_headers": {
                    "index": "Index",
                    "title": "Title",
                    "url": "URL",
                    "blog_name": "Blog Name",
                    "date": "Date",
                    "status": "Status",
                    "sentiment": "Sentiment",
                    "language": "Language",
                    "score": "Score"
                },
                "sentiment_stats": {
                    "positive": "Positive",
                    "negative": "Negative",
                    "neutral": "Neutral",
                    "avg_score": "Average Score",
                    "positive_ratio": "Positive Ratio",
                    "negative_ratio": "Negative Ratio",
                    "neutral_ratio": "Neutral Ratio"
                },
                "filter_by_sentiment": "Filter by Sentiment",
                "all_sentiments": "All Sentiments",
                "show_positive": "Show Positive Only",
                "show_negative": "Show Negative Only",
                "show_neutral": "Show Neutral Only",
                "no_matching_results": "No matching results found"
            },
            LanguageCode.JAPANESE: {
                "title": "検索結果",
                "back_to_search": "再検索",
                "results_list": "結果一覧",
                "first_n_items": "最初の50件",
                "download_excel": "Excelダウンロード",
                "download_csv": "CSVダウンロード",
                "export_results": "結果をエクスポート",
                "stats_title": "統計",
                "total_results": "総結果数",
                "successful": "成功",
                "failed": "失敗",
                "search_time": "検索時間",
                "table_headers": {
                    "index": "番号",
                    "title": "タイトル",
                    "url": "URL",
                    "blog_name": "ブログ名",
                    "date": "日付",
                    "status": "ステータス",
                    "sentiment": "感情",
                    "language": "言語",
                    "score": "スコア"
                },
                "sentiment_stats": {
                    "positive": "肯定的",
                    "negative": "否定的",
                    "neutral": "中立的",
                    "avg_score": "平均スコア",
                    "positive_ratio": "肯定的比率",
                    "negative_ratio": "否定的比率",
                    "neutral_ratio": "中立的比率"
                },
                "filter_by_sentiment": "感情でフィルタリング",
                "all_sentiments": "全感情",
                "show_positive": "肯定的のみ表示",
                "show_negative": "否定的のみ表示",
                "show_neutral": "中立的のみ表示",
                "no_matching_results": "一致する結果が見つかりません"
            },
            LanguageCode.CHINESE: {
                "title": "搜索结果",
                "back_to_search": "再次搜索",
                "results_list": "结果列表",
                "first_n_items": "前50个",
                "download_excel": "下载Excel",
                "download_csv": "下载CSV",
                "export_results": "导出结果",
                "stats_title": "统计",
                "total_results": "总结果数",
                "successful": "成功",
                "failed": "失败",
                "search_time": "搜索时间",
                "table_headers": {
                    "index": "序号",
                    "title": "标题",
                    "url": "URL",
                    "blog_name": "博客名称",
                    "date": "日期",
                    "status": "状态",
                    "sentiment": "情感",
                    "language": "语言",
                    "score": "得分"
                },
                "sentiment_stats": {
                    "positive": "积极",
                    "negative": "消极",
                    "neutral": "中性",
                    "avg_score": "平均得分",
                    "positive_ratio": "积极比例",
                    "negative_ratio": "消极比例",
                    "neutral_ratio": "中性比例"
                },
                "filter_by_sentiment": "按情感筛选",
                "all_sentiments": "所有情感",
                "show_positive": "仅显示积极",
                "show_negative": "仅显示消极",
                "show_neutral": "仅显示中性",
                "no_matching_results": "未找到匹配结果"
            }
        },

        # 감정 분석
        "sentiment": {
            LanguageCode.KOREAN: {
                "title": "감정 분석",
                "analyze": "감정 분석하기",
                "analyzing": "감정 분석 중...",
                "sentiment_score": "감정 점수",
                "confidence": "신뢰도",
                "positive_words": "긍정 단어",
                "negative_words": "부정 단어",
                "word_count": "단어 수",
                "detected_language": "감지 언어",
                "translation_used": "번역 사용",
                "sentiment_distribution": "감정 분포",
                "language_distribution": "언어별 분포",
                "analyze_text": "텍스트 분석",
                "text_placeholder": "분석할 텍스트를 입력하세요...",
                "sentiment_labels": {
                    "positive": "긍정",
                    "negative": "부정",
                    "neutral": "중립"
                },
                "analysis_options": "분석 옵션",
                "auto_translate": "자동 번역",
                "show_details": "상세 정보 표시",
                "export_analysis": "분석 결과 내보내기",
                "positive_score": "긍정 점수",
                "negative_score": "부정 점수",
                "overall_sentiment": "전체 감정",
                "sentiment_trend": "감정 추이",
                "keywords": "주요 단어",
                "emotional_intensity": "감정 강도"
            },
            LanguageCode.ENGLISH: {
                "title": "Sentiment Analysis",
                "analyze": "Analyze Sentiment",
                "analyzing": "Analyzing sentiment...",
                "sentiment_score": "Sentiment Score",
                "confidence": "Confidence",
                "positive_words": "Positive Words",
                "negative_words": "Negative Words",
                "word_count": "Word Count",
                "detected_language": "Detected Language",
                "translation_used": "Translation Used",
                "sentiment_distribution": "Sentiment Distribution",
                "language_distribution": "Language Distribution",
                "analyze_text": "Analyze Text",
                "text_placeholder": "Enter text to analyze...",
                "sentiment_labels": {
                    "positive": "Positive",
                    "negative": "Negative",
                    "neutral": "Neutral"
                },
                "analysis_options": "Analysis Options",
                "auto_translate": "Auto Translate",
                "show_details": "Show Details",
                "export_analysis": "Export Analysis",
                "positive_score": "Positive Score",
                "negative_score": "Negative Score",
                "overall_sentiment": "Overall Sentiment",
                "sentiment_trend": "Sentiment Trend",
                "keywords": "Keywords",
                "emotional_intensity": "Emotional Intensity"
            },
            LanguageCode.JAPANESE: {
                "title": "感情分析",
                "analyze": "感情を分析",
                "analyzing": "感情分析中...",
                "sentiment_score": "感情スコア",
                "confidence": "信頼度",
                "positive_words": "肯定的単語",
                "negative_words": "否定的単語",
                "word_count": "単語数",
                "detected_language": "検出された言語",
                "translation_used": "翻訳使用",
                "sentiment_distribution": "感情分布",
                "language_distribution": "言語分布",
                "analyze_text": "テキスト分析",
                "text_placeholder": "分析するテキストを入力...",
                "sentiment_labels": {
                    "positive": "肯定的",
                    "negative": "否定的",
                    "neutral": "中立的"
                },
                "analysis_options": "分析オプション",
                "auto_translate": "自動翻訳",
                "show_details": "詳細を表示",
                "export_analysis": "分析結果をエクスポート",
                "positive_score": "肯定的スコア",
                "negative_score": "否定的スコア",
                "overall_sentiment": "全体的感情",
                "sentiment_trend": "感情傾向",
                "keywords": "キーワード",
                "emotional_intensity": "感情強度"
            },
            LanguageCode.CHINESE: {
                "title": "情感分析",
                "analyze": "分析情感",
                "analyzing": "情感分析中...",
                "sentiment_score": "情感得分",
                "confidence": "置信度",
                "positive_words": "积极词汇",
                "negative_words": "消极词汇",
                "word_count": "词数",
                "detected_language": "检测到的语言",
                "translation_used": "使用翻译",
                "sentiment_distribution": "情感分布",
                "language_distribution": "语言分布",
                "analyze_text": "分析文本",
                "text_placeholder": "请输入要分析的文本...",
                "sentiment_labels": {
                    "positive": "积极",
                    "negative": "消极",
                    "neutral": "中性"
                },
                "analysis_options": "分析选项",
                "auto_translate": "自动翻译",
                "show_details": "显示详情",
                "export_analysis": "导出分析结果",
                "positive_score": "积极得分",
                "negative_score": "消极得分",
                "overall_sentiment": "整体情感",
                "sentiment_trend": "情感趋势",
                "keywords": "关键词",
                "emotional_intensity": "情感强度"
            }
        },

        # 에러 메시지
        "errors": {
            LanguageCode.KOREAN: {
                "keyword_required": "검색어를 입력해주세요.",
                "invalid_keyword": "유효하지 않은 검색어입니다.",
                "search_failed": "검색 중 오류가 발생했습니다.",
                "network_error": "네트워크 오류가 발생했습니다.",
                "server_error": "서버 오류가 발생했습니다.",
                "file_not_found": "파일을 찾을 수 없습니다.",
                "invalid_file_type": "유효하지 않은 파일 형식입니다.",
                "file_too_large": "파일이 너무 큽니다.",
                "upload_failed": "파일 업로드에 실패했습니다.",
                "analysis_failed": "분석에 실패했습니다.",
                "translation_failed": "번역에 실패했습니다.",
                "permission_denied": "권한이 거부되었습니다.",
                "session_expired": "세션이 만료되었습니다.",
                "invalid_request": "유효하지 않은 요청입니다.",
                "rate_limit_exceeded": "요청 제한을 초과했습니다.",
                "service_unavailable": "서비스를 사용할 수 없습니다."
            },
            LanguageCode.ENGLISH: {
                "keyword_required": "Please enter a keyword.",
                "invalid_keyword": "Invalid keyword.",
                "search_failed": "An error occurred during search.",
                "network_error": "A network error occurred.",
                "server_error": "A server error occurred.",
                "file_not_found": "File not found.",
                "invalid_file_type": "Invalid file type.",
                "file_too_large": "File is too large.",
                "upload_failed": "File upload failed.",
                "analysis_failed": "Analysis failed.",
                "translation_failed": "Translation failed.",
                "permission_denied": "Permission denied.",
                "session_expired": "Session expired.",
                "invalid_request": "Invalid request.",
                "rate_limit_exceeded": "Rate limit exceeded.",
                "service_unavailable": "Service unavailable."
            },
            LanguageCode.JAPANESE: {
                "keyword_required": "検索キーワードを入力してください。",
                "invalid_keyword": "無効な検索キーワードです。",
                "search_failed": "検索中にエラーが発生しました。",
                "network_error": "ネットワークエラーが発生しました。",
                "server_error": "サーバーエラーが発生しました。",
                "file_not_found": "ファイルが見つかりません。",
                "invalid_file_type": "無効なファイルタイプです。",
                "file_too_large": "ファイルが大きすぎます。",
                "upload_failed": "ファイルのアップロードに失敗しました。",
                "analysis_failed": "分析に失敗しました。",
                "translation_failed": "翻訳に失敗しました。",
                "permission_denied": "アクセス権が拒否されました。",
                "session_expired": "セッションが期限切れです。",
                "invalid_request": "無効なリクエストです。",
                "rate_limit_exceeded": "リクエスト制限を超えました。",
                "service_unavailable": "サービスをご利用いただけません。"
            },
            LanguageCode.CHINESE: {
                "keyword_required": "请输入搜索关键词。",
                "invalid_keyword": "无效的搜索关键词。",
                "search_failed": "搜索过程中发生错误。",
                "network_error": "发生网络错误。",
                "server_error": "发生服务器错误。",
                "file_not_found": "文件未找到。",
                "invalid_file_type": "无效的文件类型。",
                "file_too_large": "文件太大。",
                "upload_failed": "文件上传失败。",
                "analysis_failed": "分析失败。",
                "translation_failed": "翻译失败。",
                "permission_denied": "权限被拒绝。",
                "session_expired": "会话已过期。",
                "invalid_request": "无效的请求。",
                "rate_limit_exceeded": "超过请求限制。",
                "service_unavailable": "服务不可用。"
            }
        },

        # 설정 페이지
        "settings": {
            LanguageCode.KOREAN: {
                "title": "설정",
                "language_settings": "언어 설정",
                "interface_language": "인터페이스 언어",
                "content_language": "콘텐츠 언어",
                "search_settings": "검색 설정",
                "default_max_results": "기본 최대 결과 수",
                "search_sources": "검색 소스",
                "enable_sentiment": "감정 분석 활성화",
                "enable_translation": "번역 기능 활성화",
                "translation_language": "번역 언어",
                "auto_translate_results": "결과 자동 번역",
                "data_settings": "데이터 설정",
                "export_format": "내보내기 형식",
                "data_retention": "데이터 보관 기간",
                "clear_data": "데이터 정리",
                "clear_history": "검색 이력 정리",
                "clear_cache": "캐시 정리",
                "save_settings": "설정 저장",
                "reset_to_default": "기본값으로 초기화",
                "settings_saved": "설정이 저장되었습니다.",
                "settings_reset": "설정이 초기화되었습니다."
            },
            LanguageCode.ENGLISH: {
                "title": "Settings",
                "language_settings": "Language Settings",
                "interface_language": "Interface Language",
                "content_language": "Content Language",
                "search_settings": "Search Settings",
                "default_max_results": "Default Max Results",
                "search_sources": "Search Sources",
                "enable_sentiment": "Enable Sentiment Analysis",
                "enable_translation": "Enable Translation",
                "translation_language": "Translation Language",
                "auto_translate_results": "Auto Translate Results",
                "data_settings": "Data Settings",
                "export_format": "Export Format",
                "data_retention": "Data Retention",
                "clear_data": "Clear Data",
                "clear_history": "Clear Search History",
                "clear_cache": "Clear Cache",
                "save_settings": "Save Settings",
                "reset_to_default": "Reset to Default",
                "settings_saved": "Settings saved successfully.",
                "settings_reset": "Settings reset to default."
            },
            LanguageCode.JAPANESE: {
                "title": "設定",
                "language_settings": "言語設定",
                "interface_language": "インターフェース言語",
                "content_language": "コンテンツ言語",
                "search_settings": "検索設定",
                "default_max_results": "デフォルト最大結果数",
                "search_sources": "検索ソース",
                "enable_sentiment": "感情分析を有効化",
                "enable_translation": "翻訳機能を有効化",
                "translation_language": "翻訳言語",
                "auto_translate_results": "結果の自動翻訳",
                "data_settings": "データ設定",
                "export_format": "エクスポート形式",
                "data_retention": "データ保持期間",
                "clear_data": "データをクリア",
                "clear_history": "検索履歴をクリア",
                "clear_cache": "キャッシュをクリア",
                "save_settings": "設定を保存",
                "reset_to_default": "デフォルトにリセット",
                "settings_saved": "設定が正常に保存されました。",
                "settings_reset": "設定がデフォルトにリセットされました。"
            },
            LanguageCode.CHINESE: {
                "title": "设置",
                "language_settings": "语言设置",
                "interface_language": "界面语言",
                "content_language": "内容语言",
                "search_settings": "搜索设置",
                "default_max_results": "默认最大结果数",
                "search_sources": "搜索来源",
                "enable_sentiment": "启用情感分析",
                "enable_translation": "启用翻译功能",
                "translation_language": "翻译语言",
                "auto_translate_results": "自动翻译结果",
                "data_settings": "数据设置",
                "export_format": "导出格式",
                "data_retention": "数据保留",
                "clear_data": "清除数据",
                "clear_history": "清除搜索历史",
                "clear_cache": "清除缓存",
                "save_settings": "保存设置",
                "reset_to_default": "重置为默认",
                "settings_saved": "设置保存成功。",
                "settings_reset": "设置已重置为默认。"
            }
        }
    }

    @classmethod
    def get_translation(cls, category: str, key: str, language: str = None) -> str:
        """
        번역 텍스트 가져오기

        Args:
            category: 카테고리 (예: 'common', 'nav', 'search_page')
            key: 키 (예: 'app_name', 'search')
            language: 언어 코드 (None인 경우 기본 언어 사용)

        Returns:
            번역된 텍스트
        """
        if language is None:
            language = LanguageInfo.get_default_language()

        # 언어 지원 여부 확인
        if not LanguageInfo.is_supported(language):
            language = LanguageInfo.get_default_language()

        try:
            return cls.TRANSLATIONS[category][language][key]
        except KeyError:
            # 키를 찾을 수 없으면 기본 언어로 시도
            try:
                return cls.TRANSLATIONS[category][LanguageInfo.get_default_language()][key]
            except KeyError:
                # 카테고리를 찾을 수 없으면 기본값 반환
                return key

    @classmethod
    def get_translations_for_language(cls, language: str) -> Dict[str, Dict]:
        """
        특정 언어의 모든 번역 가져오기

        Args:
            language: 언어 코드

        Returns:
            {카테고리: {키: 번역}} 딕셔너리
        """
        if not LanguageInfo.is_supported(language):
            language = LanguageInfo.get_default_language()

        translations = {}
        for category, lang_translations in cls.TRANSLATIONS.items():
            if language in lang_translations:
                translations[category] = lang_translations[language]

        return translations

    @classmethod
    def get_all_categories(cls) -> List[str]:
        """모든 카테고리 목록"""
        return list(cls.TRANSLATIONS.keys())

    @classmethod
    def export_translations(cls, language: str) -> Dict:
        """
        특정 언어의 번역 내보내기

        Args:
            language: 언어 코드

        Returns:
            번역 데이터
        """
        return {
            "language": language,
            "language_info": LanguageInfo.get_language_info(language),
            "translations": cls.get_translations_for_language(language)
        }

    @classmethod
    def add_custom_translation(cls, category: str, key: str, translations: Dict[str, str]) -> None:
        """
        사용자 정의 번역 추가

        Args:
            category: 카테고리
            key: 키
            translations: {언어코드: 번역텍스트} 딕셔너리
        """
        if category not in cls.TRANSLATIONS:
            cls.TRANSLATIONS[category] = {}

        cls.TRANSLATIONS[category][key] = translations


class I18N:
    """국제화 지원 클래스"""

    def __init__(self, default_language: Optional[str] = None):
        """
        I18N 초기화

        Args:
            default_language: 기본 언어
        """
        self.default_language = default_language or LanguageInfo.get_default_language()
        self.current_language = self.default_language

    def set_language(self, language: str) -> None:
        """
        현재 언어 설정

        Args:
            language: 언어 코드
        """
        if LanguageInfo.is_supported(language):
            self.current_language = language
            logger.info(f"언어 변경: {self.current_language}")
        else:
            logger.warning(f"지원하지 않는 언어: {language}")

    def get_language(self) -> str:
        """현재 언어 반환"""
        return self.current_language

    def translate(self, category: str, key: str, **kwargs) -> str:
        """
        텍스트 번역

        Args:
            category: 카테고리
            key: 키
            **kwargs: 포맷팅 인자

        Returns:
            번역된 텍스트
        """
        text = UITranslations.get_translation(category, key, self.current_language)
        return text.format(**kwargs) if kwargs else text

    def t(self, category: str, key: str, **kwargs) -> str:
        """짧은 번역 메서드"""
        return self.translate(category, key, **kwargs)

    def get_language_info(self) -> Dict:
        """현재 언어 정보 반환"""
        return LanguageInfo.get_language_info(self.current_language)

    def get_supported_languages(self) -> Dict[str, Dict]:
        """지원하는 모든 언어 반환"""
        return LanguageInfo.get_all_languages()

    def get_current_translations(self) -> Dict[str, Dict]:
        """현재 언어의 모든 번역 반환"""
        return UITranslations.get_translations_for_language(self.current_language)


# Flask 통합 함수
def get_i18n() -> I18N:
    """Flask g 객체에서 I18N 인스턴스 가져오기"""
    if not hasattr(g, 'i18n'):
        g.i18n = I18N()
    return g.i18n


def set_language(language: str) -> None:
    """현재 언어 설정"""
    i18n = get_i18n()
    i18n.set_language(language)


def get_current_language() -> str:
    """현재 언어 반환"""
    return get_i18n().get_language()


def translate(category: str, key: str, **kwargs) -> str:
    """텍스트 번역"""
    return get_i18n().translate(category, key, **kwargs)


def t(category: str, key: str, **kwargs) -> str:
    """짧은 번역 메서드"""
    return translate(category, key, **kwargs)


# Flask 데코레이터
def with_i18n(f):
    """I18N 지원 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 언어 설정 (URL 파라미터, 헤더, 쿠키 등)
        language = request.args.get('lang') or \
                    request.headers.get('Accept-Language', '').split(',')[0][:2] or \
                    request.cookies.get('language') or \
                    LanguageInfo.get_default_language()

        # 언어 설정
        set_language(language)

        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# 번역 파일 관리
# ============================================================================

class TranslationFileManager:
    """번역 파일 관리 클래스"""

    @staticmethod
    def save_translations_to_file(language: str, file_path: str) -> None:
        """
        번역을 파일로 저장

        Args:
            language: 언어 코드
            file_path: 저장할 파일 경로
        """
        translations = UITranslations.export_translations(language)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)

        logger.info(f"번역 파일 저장 완료: {file_path}")

    @staticmethod
    def load_translations_from_file(file_path: str) -> Dict:
        """
        파일에서 번역 로드

        Args:
            file_path: 번역 파일 경로

        Returns:
            번역 데이터
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            translations = json.load(f)

        logger.info(f"번역 파일 로드 완료: {file_path}")
        return translations

    @staticmethod
    def export_all_languages(output_dir: str = "translations") -> None:
        """
        모든 언어의 번역 파일 내보내기

        Args:
            output_dir: 출력 디렉토리
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        for language in LanguageInfo.SUPPORTED_LANGUAGES.keys():
            file_path = output_path / f"{language}.json"
            TranslationFileManager.save_translations_to_file(language, str(file_path))

        logger.info(f"모든 언어 번역 파일 내보내기 완료: {output_dir}")


# ============================================================================
# 유틸리티 함수
# ============================================================================

def detect_browser_language() -> str:
    """
    브라우저 언어 감지 (Accept-Language 헤더 기반)

    Returns:
        감지된 언어 코드
    """
    accept_language = request.headers.get('Accept-Language', '')
    if accept_language:
        # 첫 번째 언어 코드 추출
        first_lang = accept_language.split(',')[0]
        lang_code = first_lang.split('-')[0][:2]

        if LanguageInfo.is_supported(lang_code):
            return lang_code

    return LanguageInfo.get_default_language()


def get_language_switcher_html(current_language: str) -> str:
    """
    언어 전환기 HTML 생성

    Args:
        current_language: 현재 언어 코드

    Returns:
        언어 전환기 HTML
    """
    languages = LanguageInfo.get_all_languages()
    html = '<div class="language-switcher">'

    for lang_code, lang_info in languages.items():
        flag = lang_info.get('flag', '')
        native_name = lang_info.get('native_name', lang_code)
        is_active = lang_code == current_language

        html += f'''
        <button class="lang-btn {'active' if is_active else ''}"
                onclick="changeLanguage('{lang_code}')"
                title="{native_name}">
            <span class="flag">{flag}</span>
            <span class="lang-name">{native_name}</span>
        </button>
        '''

    html += '</div>'
    return html


def get_language_select_html(current_language: str) -> str:
    """
    언어 선택 드롭다운 HTML 생성

    Args:
        current_language: 현재 언어 코드

    Returns:
        언어 선택 HTML
    """
    languages = LanguageInfo.get_all_languages()
    html = '<select id="language-selector" class="form-control" onchange="changeLanguage(this.value)">'

    for lang_code, lang_info in languages.items():
        native_name = lang_info.get('native_name', lang_code)
        selected = 'selected' if lang_code == current_language else ''

        html += f'<option value="{lang_code}" {selected}>{native_name}</option>'

    html += '</select>'
    return html


# ============================================================================
# 테스트
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🌐 다국어 UI 번역 시스템 테스트")
    print("=" * 60)

    # I18N 초기화
    i18n = I18N()

    # 지원 언어 확인
    print(f"\n📋 지원 언어:")
    for code, info in LanguageInfo.get_all_languages().items():
        print(f"   {code}: {info['flag']} {info['native_name']}")

    # 번역 테스트
    print(f"\n🧪 번역 테스트:")

    test_languages = [LanguageCode.KOREAN, LanguageCode.ENGLISH, LanguageCode.JAPANESE, LanguageCode.CHINESE]

    for lang in test_languages:
        i18n.set_language(lang)
        lang_info = i18n.get_language_info()

        print(f"\n{lang_info['flag']} {lang_info['native_name']}:")

        # 공통 텍스트
        print(f"   앱 이름: {i18n.t('common', 'app_name')}")
        print(f"   검색: {i18n.t('common', 'search')}")
        print(f"   다운로드: {i18n.t('common', 'download')}")

        # 페이지별 텍스트
        print(f"   검색 페이지 제목: {i18n.t('search_page', 'title')}")
        print(f"   결과 페이지 제목: {i18n.t('results_page', 'title')}")
        print(f"   감정 분석 제목: {i18n.t('sentiment', 'title')}")

        # 에러 메시지
        print(f"   검색어 필수 오류: {i18n.t('errors', 'keyword_required')}")

    # 파일 내보내기 테스트
    print(f"\n📁 번역 파일 내보내기 테스트:")
    try:
        TranslationFileManager.export_all_languages()
        print("   ✅ 모든 번역 파일 내보내기 완료")
    except Exception as e:
        print(f"   ❌ 오류: {e}")

    # 언어 전환기 HTML 테스트
    print(f"\n🎨 언어 전환기 HTML:")
    html = get_language_switcher_html(LanguageCode.KOREAN)
    print(f"   {html[:100]}...")

    print("\n✨ 테스트 완료!")