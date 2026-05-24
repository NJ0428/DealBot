#!/usr/bin/env python3
"""
다국어 감정 분석 시스템
여러 언어의 감정을 분석하고 통합 결과를 제공합니다.
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter
from enum import Enum

# 기존 한국어 감정 분석기 import
from sentiment_analyzer import (
    SentimentAnalyzer, SentimentConfig, SentimentResult, SentimentFilter,
    KOREAN_SENTIMENT_DICT, KONLPY_AVAILABLE
)

# 번역 서비스 import
from translation_service import TranslationService, TranslationConfig

from web_crawler import setup_logging

logger = setup_logging()


# ============================================================================
# 언어 열거형 및 지원 언어
# ============================================================================

class Language(Enum):
    """지원하는 언어 코드"""
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
    VIETNAMESE = "vi"
    THAI = "th"
    HINDI = "hi"

    @classmethod
    def get_language_name(cls, code: str) -> str:
        """언어 코드로 언어 이름 반환"""
        language_names = {
            "ko": "Korean", "en": "English", "ja": "Japanese", "zh": "Chinese",
            "es": "Spanish", "fr": "French", "de": "German", "ru": "Russian",
            "ar": "Arabic", "pt": "Portuguese", "it": "Italian", "vi": "Vietnamese",
            "th": "Thai", "hi": "Hindi"
        }
        return language_names.get(code, code)

    @classmethod
    def get_all_supported(cls) -> Dict[str, str]:
        """모든 지원 언어 반환 {코드: 이름}"""
        return {lang.value: cls.get_language_name(lang.value) for lang in cls}


# ============================================================================
# 언어별 감정 사전
# ============================================================================

ENGLISH_SENTIMENT_DICT = {
    'positive': {
        # Strong positive
        'excellent', 'outstanding', 'amazing', 'wonderful', 'fantastic', 'superb',
        'brilliant', 'incredible', 'extraordinary', 'phenomenal', 'magnificent',
        'spectacular', 'remarkable', 'impressive', 'exceptional', 'perfect',
        'success', 'successful', 'achieve', 'achievement', 'accomplish', 'accomplishment',
        'breakthrough', 'innovation', 'innovative', 'revolutionary', 'pioneering',
        'growth', 'grow', 'growing', 'increase', 'increasing', 'rise', 'rising',
        'improve', 'improvement', 'improving', 'enhance', 'enhancement', 'better',
        'strong', 'strength', 'powerful', 'robust', 'solid', 'stable', 'stability',
        # Medium positive
        'good', 'great', 'nice', 'positive', 'beneficial', 'advantageous',
        'effective', 'efficient', 'productive', 'useful', 'helpful', 'supportive',
        'reliable', 'trustworthy', 'confident', 'optimistic', 'hopeful', 'promising',
        'satisfactory', 'adequate', 'acceptable', 'reasonable', 'appropriate',
        # Weak positive
        'okay', 'fine', 'decent', 'fair', 'not bad', 'alright', 'passable'
    },
    'negative': {
        # Strong negative
        'terrible', 'horrible', 'awful', 'disastrous', 'catastrophic', 'devastating',
        'failure', 'fail', 'failed', 'failing', 'unsuccessful', 'disappointment',
        'crisis', 'emergency', 'disaster', 'catastrophe', 'collapse', 'crash',
        'worst', 'poor', 'bad', 'horrible', 'terrible', 'awful', 'dreadful',
        'danger', 'dangerous', 'threat', 'threatening', 'harmful', 'damaging',
        'loss', 'lose', 'losing', 'lost', 'damage', 'damaged', 'destroy', 'destroyed',
        'problem', 'problematic', 'issue', 'trouble', 'difficult', 'difficulty',
        # Medium negative
        'concern', 'concerning', 'worry', 'worrying', 'worried', 'anxiety',
        'negative', 'unfavorable', 'adverse', 'harmful', 'detrimental',
        'disappointing', 'unsatisfactory', 'inadequate', 'insufficient',
        'complaint', 'complain', 'criticism', 'criticize', 'negative feedback',
        'reject', 'rejection', 'refuse', 'refusal', 'deny', 'denial',
        # Weak negative
        'concern', 'worry', 'regret', 'unfortunate', 'disappointing', 'poor',
        'weak', 'weakness', 'flaw', 'flawed', 'defect', 'defective', 'error', 'mistake'
    },
    'intensifiers': {
        'very', 'extremely', 'incredibly', 'absolutely', 'completely', 'totally',
        'fully', 'entirely', 'thoroughly', 'really', 'truly', 'genuinely',
        'highly', 'remarkably', 'exceptionally', 'extraordinarily', 'particularly',
        'especially', 'significantly', 'substantially', 'considerably', 'notably',
        'most', 'more', 'much', 'far', 'way', 'so', 'such', 'too'
    },
    'negations': {
        'not', 'no', 'never', 'neither', 'nor', 'none', 'nobody', 'nothing',
        'nowhere', 'hardly', 'barely', 'scarcely', 'rarely', 'seldom',
        'don\'t', 'doesn\'t', 'didn\'t', 'won\'t', 'wouldn\'t', 'couldn\'t', 'shouldn\'t',
        'can\'t', 'cannot', 'couldn\'t', 'isn\'t', 'aren\'t', 'wasn\'t', 'weren\'t',
        'haven\'t', 'hasn\'t', 'hadn\'t', 'without', 'lacking', 'missing'
    }
}

JAPANESE_SENTIMENT_DICT = {
    'positive': {
        # 強い肯定的 (Strong positive)
        '最高', '素晴らしい', '素晴らしく', '優秀', '優秀な', '素晴らしい',
        '成功', '成功する', '達成', '達成する', '実現', '実現する',
        '革新', '革新的', '画期的', '飛躍的', '急成長', '急成長する',
        '向上', '向上する', '改善', '改善する', '進歩', '進歩する',
        '成長', '成長する', '拡大', '拡大する', '増加', '増加する',
        '良い', '素晴らしい', '優れた', '優秀な', '秀逸', '傑出',
        '満足', '満足する', '喜び', '喜ぶ', '嬉しい', '楽しい',
        # 中程度肯定的 (Medium positive)
        '良い', 'いい', 'まとも', '適切', '適切な', '合理的',
        '安定', '安定する', '安定した', '順調', '順調な',
        '有効', '有効な', '効果的', '効率的', '生産的',
        '支持', '支持する', '後援', '協力', '協力する',
        '信頼', '信頼する', '信頼性', '確信', '期待',
        # 弱い肯定的 (Weak positive)
        'まあまあ', '普通', '悪くない', '及第', '合格', 'そこそこ'
    },
    'negative': {
        # 強い否定的 (Strong negative)
        '最悪', '最悪の', '悲惨', '悲惨な', 'ひどい', '酷い',
        '失敗', '失敗する', '挫折', '挫折する', '崩壊', '崩壊する',
        '危機', '危機的', '緊急', '緊急の', '災害', '災害',
        '悪い', '悪い', '劣悪', '劣悪な', '劣る', '劣っている',
        '危険', '危険な', '脅威', '脅威となる', '有害', '有害な',
        '損失', '損失する', '損なう', '損害', '損害を与える',
        '問題', '問題のある', '困難', '困難な', '難しい',
        # 中程度否定的 (Medium negative)
        '懸念', '懸念される', '懸念', '不安', '不安な',
        '否定的', '不利益', '有害', '害を与える',
        '失望', '失望する', '不満', '不満な', '不満を抱く',
        '苦情', '苦情を言う', '批判', '批判する', '非難',
        '拒否', '拒否する', '否定', '否定する', '反対', '反対する',
        # 弱い否定的 (Weak negative)
        '心配', '心配する', '悩み', '残念', '残念な',
        '不十分', '不足', '不足する', '弱い', '弱い'
    },
    'intensifiers': {
        '非常に', '大変', 'とても', 'たいへん', '極めて', '極めて',
        '完全に', '全く', '本当に', '実に', '誠に', '確かに',
        '著しく', '著しい', '格別', '格別に', '特に', 'とりわけ',
        '相当', '相当に', 'ずいぶん', '随分', '大いに', '大幅に',
        '最も', 'より', 'ずっと', 'はるかに', 'ますます', 'ますます'
    },
    'negations': {
        'ない', 'ません', 'ぬ', 'ず', 'ん', 'うかがう', 'まい',
        '否', '否定', '否定的', '無', 'なし', 'ぬ',
        '難い', 'かたい', '得ない', 'かねる', 'がたい', '兼ねる',
        'まい', 'ぬ', 'ん', 'ず', 'その他', 'ほか'
    }
}

CHINESE_SENTIMENT_DICT = {
    'positive': {
        # 强烈积极 (Strong positive)
        '优秀', '卓越', '杰出', '精彩', '完美', '理想', '最佳', '最好',
        '成功', '成就', '达成', '实现', '完成', '圆满', '成功',
        '创新', '革新', '突破', '跨越', '飞跃', '突飞猛进',
        '发展', '进步', '提高', '改善', '改进', '优化', '升级',
        '增长', '上升', '增加', '扩大', '扩展', '扩展', '提升',
        '良好', '优秀', '优良', '优质', '出色', '精彩', '出色',
        '满意', '满足', '喜悦', '高兴', '快乐', '愉快', '兴奋',
        # 中等积极 (Medium positive)
        '好', '不错', '很好', '挺好', '适当', '合适',
        '稳定', '稳固', '平稳', '顺利', '流畅',
        '有效', '高效', '有用', '实用', '有益', '帮助',
        '支持', '协助', '合作', '配合', '支援', '支援',
        '信任', '信赖', '信心', '相信', '期待', '希望',
        # 弱积极 (Weak positive)
        '还行', '一般', '不错', '及格', '说得过去', '马马虎虎'
    },
    'negative': {
        # 强烈消极 (Strong negative)
        '糟糕', '恶劣', '差劲', '极差', '最差', '失败', '失败',
        '危机', '紧急', '灾难', '灾难性', '崩溃', '瓦解',
        '糟糕', '恶劣', '差', '差劲', '拙劣', '低劣',
        '危险', '危急', '威胁', '有害', '损害', '伤害',
        '损失', '失去', '损坏', '破坏', '毁坏', '摧毁',
        '问题', '困难', '艰难', '困苦', '困苦', '困难',
        # 中等消极 (Medium negative)
        '担忧', '焦虑', '忧虑', '不安', '担心', '担心',
        '消极', '负面', '不利', '有害', '有害的',
        '失望', '不满', '抱怨', '不满', '投诉',
        '批评', '指责', '谴责', '抨击', '攻击',
        '拒绝', '否认', '否定', '反对', '抵制',
        # 弱消极 (Weak negative)
        '担心', '忧虑', '遗憾', '可惜', '可惜', '遗憾',
        '不足', '缺乏', '不够', '弱', '软弱'
    },
    'intensifiers': {
        '非常', '极其', '十分', '特别', '格外', '格外',
        '完全', '彻底', '充分', '充分', '确实', '的确',
        '显著', '明显', '突出', '杰出', '格外', '特别',
        '相当', '相当', '很', '挺', '特别', '格外',
        '最', '更', '越', '愈发', '更加', '越来越'
    },
    'negations': {
        '不', '没', '没有', '无', '非', '未',
        '别', '不要', '不必', '不用', '无须',
        '难以', '无法', '不能', '不可能', '未必',
        '从不', '永不', '绝不', '毫不', '毫无', '毫无'
    }
}

SPANISH_SENTIMENT_DICT = {
    'positive': {
        # Fuerte positivo (Strong positive)
        'excelente', 'extraordinario', 'maravilloso', 'fantástico', 'increíble',
        'espectacular', 'excepcional', 'perfecto', 'ideal', 'óptimo',
        'éxito', 'exitoso', 'lograr', 'logro', 'conseguir', 'conseguido',
        'innovación', 'innovador', 'revolucionario', 'pionero', 'avance',
        'crecimiento', 'crecer', 'aumento', 'aumentar', 'expansión', 'expandir',
        'mejora', 'mejorar', 'mejor', 'mejorar', 'progreso', 'progresar',
        'bueno', 'excelente', 'maravilloso', 'fantástico', 'genial',
        'satisfacción', 'satisfacer', 'alegría', 'alegre', 'feliz', 'contento',
        # Positivo medio (Medium positive)
        'bueno', 'bien', 'positivo', 'beneficioso', 'ventajoso',
        'adecuado', 'apropiado', 'razonable', 'aceptable', 'satisfactorio',
        'estable', 'estabilidad', 'favorable', 'prometedor', 'esperanzador',
        'efectivo', 'eficiente', 'útil', 'productivo', 'provechoso',
        'apoyo', 'apoyar', 'ayuda', 'ayudar', 'colaboración', 'cooperar',
        # Positivo débil (Weak positive)
        'aceptable', 'bien', 'regular', 'decente', 'no mal', 'pasable'
    },
    'negative': {
        # Fuerte negativo (Strong negative)
        'terrible', 'horrible', 'pésimo', 'desastroso', 'catastrófico',
        'fracaso', 'fallar', 'fracasar', 'fracasado', 'fracasado',
        'crisis', 'emergencia', 'desastre', 'colapso', 'caída',
        'malo', 'pésimo', 'terrible', 'horrible', 'espantoso',
        'peligro', 'peligroso', 'amenaza', 'dañino', 'perjudicial',
        'pérdida', 'perder', 'daño', 'dañar', 'destruir', 'destruido',
        'problema', 'problemático', 'dificultad', 'difícil', 'complejo',
        # Negativo medio (Medium negative)
        'preocupación', 'preocupar', 'preocupado', 'ansiedad', 'inquietud',
        'negativo', 'desfavorable', 'adverso', 'perjudicial',
        'decepción', 'decepcionado', 'insatisfacción', 'insatisfactorio',
        'queja', 'quejarse', 'crítica', 'criticar', 'condena',
        'rechazo', 'rechazar', 'negativa', 'negar', 'oposición', 'oponer',
        # Negativo débil (Weak negative)
        'preocupación', 'inquietud', 'arrepentimiento', 'lamentable', 'poco',
        'insuficiente', 'falta', 'débil', 'flaco', 'malo'
    },
    'intensifiers': {
        'muy', 'extremadamente', 'increíblemente', 'absolutamente', 'completamente',
        'totalmente', 'realmente', 'verdaderamente', 'genuinamente',
        'altamente', 'notablemente', 'excepcionalmente', 'particularmente',
        'especialmente', 'significativamente', 'considerablemente', 'sustancialmente',
        'más', 'muy', 'tan', 'demasiado', 'casi'
    },
    'negations': {
        'no', 'nunca', 'jamás', 'tampoco', 'nada', 'nadie',
        'ningún', 'ninguna', 'ningunos', 'ningunas', 'ni', 'ni siquiera',
        'sin', 'falta de', 'carencia de', 'privación de',
        'difícilmente', 'apenas', 'rara vez', 'pocas veces', 'casi nunca'
    }
}

FRENCH_SENTIMENT_DICT = {
    'positive': {
        # Fort positif (Strong positive)
        'excellent', 'extraordinaire', 'merveilleux', 'fantastique', 'incroyable',
        'spectaculaire', 'exceptionnel', 'parfait', 'idéal', 'optimal',
        'succès', 'réussir', 'réussite', 'accomplir', 'accomplissement', 'réalisation',
        'innovation', 'innovateur', 'révolutionnaire', 'pionnier', 'avancée',
        'croissance', 'croître', 'augmentation', 'augmenter', 'expansion', 'étendre',
        'amélioration', 'améliorer', 'mieux', 'amélioré', 'progrès', 'progresser',
        'bon', 'excellent', 'merveilleux', 'fantastique', 'génial',
        'satisfaction', 'satisfaire', 'joie', 'heureux', 'content', 'plaisir',
        # Positif moyen (Medium positive)
        'bon', 'bien', 'positif', 'bénéfique', 'avantageux',
        'approprié', 'adéquat', 'raisonnable', 'acceptable', 'satisfaisant',
        'stable', 'stabilité', 'favorable', 'prometteur', 'espérance',
        'efficace', 'efficace', 'utile', 'productif', 'avantageux',
        'soutien', 'soutenir', 'aide', 'aider', 'collaboration', 'coopérer',
        # Positif faible (Weak positive)
        'acceptable', 'bien', 'régulier', 'décent', 'pas mal', 'passable'
    },
    'negative': {
        # Fort négatif (Strong negative)
        'terrible', 'horrible', 'épouvantable', 'désastreux', 'catastrophique',
        'échec', 'échouer', 'raté', 'échoué', 'désastre',
        'crise', 'urgence', 'désastre', 'catastrophe', 'effondrement', 'chute',
        'mauvais', 'épouvantable', 'horrible', 'terrible', 'affreux',
        'danger', 'dangereux', 'menace', 'menaçant', 'nuisible', 'préjudiciable',
        'perte', 'perdre', 'dommage', 'endommager', 'détruire', 'détruit',
        'problème', 'problématique', 'difficulté', 'difficile', 'complexe',
        # Négatif moyen (Medium negative)
        'inquiétude', 'inquiéter', 'inquiet', 'anxiété', 'souci',
        'négatif', 'défavorable', 'adverse', 'nuisible', 'préjudiciable',
        'déception', 'déçu', 'insatisfaction', 'insatisfaisant',
        'plainte', 'se plaindre', 'critique', 'critiquer', 'condamnation',
        'refus', 'refuser', 'négation', 'nier', 'opposition', 's\'opposer',
        # Négatif faible (Weak negative)
        'inquiétude', 'souci', 'regret', 'regrettable', 'peu',
        'insuffisant', 'manque', 'faible', 'maigre', 'mauvais'
    },
    'intensifiers': {
        'très', 'extrêmement', 'incroyablement', 'absolument', 'complètement',
        'totalement', 'réellement', 'véritablement', 'généreusement',
        'hautement', 'notablement', 'exceptionnellement', 'particulièrement',
        'spécialement', 'significativement', 'considérablement', 'substantiellement',
        'plus', 'très', 'tellement', 'trop', 'presque'
    },
    'negations': {
        'non', 'ne', 'pas', 'jamais', 'rien', 'personne',
        'aucun', 'aucune', 'aucuns', 'aucunes', 'ni', 'ni même',
        'sans', 'manque de', 'carence de', 'privation de',
        'difficilement', 'à peine', 'rarement', 'peu', 'presque jamais'
    }
}

GERMAN_SENTIMENT_DICT = {
    'positive': {
        # Stark positiv (Strong positive)
        'ausgezeichnet', 'hervorragend', 'wunderbar', 'fantastisch', 'unglaublich',
        'spektakulär', 'außergewöhnlich', 'perfekt', 'ideal', 'optimal',
        'erfolg', 'erfolgreich', 'erzielen', 'erfolg', 'erreichen', 'erreichung',
        'innovation', 'innovativ', 'revolutionär', 'pionier', 'fortschritt',
        'wachstum', 'wachsen', 'zunahme', 'zunehmen', 'expansion', 'erweitern',
        'verbesserung', 'verbessern', 'besser', 'verbessert', 'fortschritt', 'fortschreiten',
        'gut', 'ausgezeichnet', 'wunderbar', 'fantastisch', 'genial',
        'zufriedenheit', 'zufrieden', 'freude', 'froh', 'glücklich', 'zufrieden',
        # Mittel positiv (Medium positive)
        'gut', 'positiv', 'vorteilhaft', 'günstig',
        'angemessen', 'geeignet', 'vernünftig', 'akzeptabel', 'zufriedenstellend',
        'stabil', 'stabilität', 'günstig', 'vielversprechend', 'hoffnungsvoll',
        'effektiv', 'effizient', 'nützlich', 'produktiv', 'vorteilhaft',
        'unterstützung', 'unterstützen', 'hilfe', 'helfen', 'zusammenarbeit', 'kooperieren',
        # Schwach positiv (Weak positive)
        'akzeptabel', 'gut', 'ordentlich', 'anständig', 'nicht schlecht', 'passabel'
    },
    'negative': {
        # Stark negativ (Strong negative)
        'schrecklich', 'furchtbar', 'entsetzlich', 'katastrophal', 'desaströs',
        'misserfolg', 'scheitern', 'fehlgeschlagen', 'desaster', 'katastrophe',
        'krise', 'notfall', 'desaster', 'katastrophe', 'zusammenbruch', 'sturz',
        'schlecht', 'furchtbar', 'entsetzlich', 'schrecklich', 'grausam',
        'gefahr', 'gefährlich', 'bedrohung', 'bedrohlich', 'schädlich', 'nachteilig',
        'verlust', 'verlieren', 'schaden', 'beschädigen', 'zerstören', 'zerstört',
        'problem', 'problematisch', 'schwierigkeit', 'schwierig', 'komplex',
        # Mittel negativ (Medium negative)
        'sorge', 'besorgnis', 'ängstlich', 'besorgt', 'unruhe',
        'negativ', 'ungünstig', 'nachteilig', 'schädlich', 'beeinträchtigend',
        'enttäuschung', 'enttäuscht', 'unzufriedenheit', 'unzufrieden',
        'beschwerde', 'beschweren', 'kritik', 'kritisieren', 'verurteilung',
        'ablehnung', 'ablehnen', 'verneinung', 'leugnen', 'widerspruch', 'widersprechen',
        # Schwach negativ (Weak negative)
        'sorge', 'unruhe', 'bedauern', 'bedauerlich', 'wenig',
        'unzureichend', 'mangel', 'schwach', 'mager', 'schlecht'
    },
    'intensifiers': {
        'sehr', 'äußerst', 'unglaublich', 'absolut', 'vollständig',
        'ganz', 'wirklich', 'tatsächlich', 'echt', 'wahrhaftig',
        'hoch', 'bemerkenswert', 'außergewöhnlich', 'besonders',
        'insbesondere', 'signifikant', 'erheblich', 'beträchtlich', 'substantiell',
        'mehr', 'sehr', 'so', 'zu', 'fast'
    },
    'negations': {
        'nicht', 'nie', 'nimmer', 'nichts', 'niemand', 'kein', 'keine',
        'keiner', 'keines', 'keinem', 'keinen', 'weder', 'noch',
        'ohne', 'mangel an', 'ermangelung', 'entbehrung',
        'kaum', 'kaum', 'selten', 'beinahe', 'fast nie'
    }
}

RUSSIAN_SENTIMENT_DICT = {
    'positive': {
        # Сильный позитив (Strong positive)
        'отличный', 'превосходный', 'замечательный', 'фантастический', 'невероятный',
        'спектакулярный', 'исключительный', 'идеальный', 'оптимальный',
        'успех', 'успешный', 'добиться', 'достижение', 'выполнение', 'реализация',
        'инновация', 'инновационный', 'революционный', 'пионер', 'прогресс',
        'рост', 'расти', 'увеличение', 'увеличить', 'расширение', 'расширить',
        'улучшение', 'улучшить', 'лучше', 'улучшенный', 'прогресс', 'продвигаться',
        'хороший', 'отличный', 'замечательный', 'фантастический', 'гениальный',
        'удовлетворение', 'удовлетворить', 'радость', 'счастливый', 'довольный',
        # Средний позитив (Medium positive)
        'хороший', 'хорошо', 'позитивный', 'выгодный', 'благоприятный',
        'подходящий', 'адекватный', 'разумный', 'приемлемый', 'удовлетворительный',
        'стабильный', 'стабильность', 'благоприятный', 'перспективный', 'обнадеживающий',
        'эффективный', 'эффективность', 'полезный', 'продуктивный', 'выгодный',
        'поддержка', 'поддерживать', 'помощь', 'помогать', 'сотрудничество', 'кооперация',
        # Слабый позитив (Weak positive)
        'приемлемый', 'хорошо', 'нормально', 'достойный', 'неплохой', 'приличный'
    },
    'negative': {
        # Сильный негатив (Strong negative)
        'ужасный', 'ужасный', 'катастрофический', 'разрушительный', 'провальный',
        'неудача', 'провалиться', 'неудачный', 'катастрофа', 'крах',
        'кризис', 'аварийный', 'катастрофа', 'коллапс', 'падение',
        'плохой', 'ужасный', 'страшный', 'ужасный', 'жестокий',
        'опасность', 'опасный', 'угроза', 'угрожающий', 'вредный', 'повреждающий',
        'потеря', 'терять', 'ущерб', 'повреждать', 'уничтожать', 'разрушенный',
        'проблема', 'проблематичный', 'трудность', 'трудный', 'сложный',
        # Средний негатив (Medium negative)
        'беспокойство', 'тревожный', 'забота', 'волнение', 'тревога',
        'негативный', 'неблагоприятный', 'вредный', 'повреждающий',
        'разочарование', 'разочарованный', 'неудовлетворение', 'неудовлетворительный',
        'жалоба', 'жаловаться', 'критика', 'критиковать', 'осуждение',
        'отказ', 'отказывать', 'отрицание', 'отрицать', 'противопоставление', 'противостоять',
        # Слабый негатив (Weak negative)
        'беспокойство', 'забота', 'сожаление', 'сожалительный', 'мало',
        'недостаточный', 'нехватка', 'слабый', 'плохой'
    },
    'intensifiers': {
        'очень', 'чрезвычайно', 'невероятно', 'абсолютно', 'полностью',
        'совершенно', 'действительно', 'действительно', 'искренне',
        'высоко', 'заметно', 'исключительно', 'особенно',
        'в частности', 'значительно', 'существенно', 'заметно',
        'более', 'очень', 'так', 'слишком', 'почти'
    },
    'negations': {
        'не', 'никогда', 'никак', 'ничего', 'никто', 'нет',
        'ни', 'ни', 'без', 'отсутствие', 'нехватка',
        'с трудом', 'едва', 'редко', 'мало', 'почти никогда'
    }
}

# 언어별 감정 사전 통합
LANGUAGE_SENTIMENT_DICTS = {
    Language.KOREAN.value: KOREAN_SENTIMENT_DICT,
    Language.ENGLISH.value: ENGLISH_SENTIMENT_DICT,
    Language.JAPANESE.value: JAPANESE_SENTIMENT_DICT,
    Language.CHINESE.value: CHINESE_SENTIMENT_DICT,
    Language.SPANISH.value: SPANISH_SENTIMENT_DICT,
    Language.FRENCH.value: FRENCH_SENTIMENT_DICT,
    Language.GERMAN.value: GERMAN_SENTIMENT_DICT,
    Language.RUSSIAN.value: RUSSIAN_SENTIMENT_DICT
}


# ============================================================================
# 다국어 감정 분석 설정
# ============================================================================

@dataclass
class MultilingualSentimentConfig:
    """다국어 감정 분석 설정"""
    # 기본 감정 분석 설정
    base_config: SentimentConfig = field(default_factory=SentimentConfig)

    # 다국어 설정
    enabled_languages: List[str] = field(default_factory=lambda: [Language.KOREAN.value, Language.ENGLISH.value])
    default_language: str = Language.ENGLISH.value

    # 번역 설정
    use_translation: bool = True
    translation_config_file: str = "translation_config.json"

    # 언어 감지 설정
    auto_detect_language: bool = True

    # 결과 통합 설정
    combine_results: bool = True
    prefer_original_language: bool = True


# ============================================================================
# 다국어 감정 분석 결과
# ============================================================================

@dataclass
class MultilingualSentimentResult:
    """다국어 감정 분석 결과"""
    # 기본 정보
    text: str
    detected_language: str
    label: str
    confidence: float

    # 점수
    sentiment_score: float
    positive_score: float
    negative_score: float

    # 언어별 결과
    language_results: Dict[str, SentimentResult] = field(default_factory=dict)

    # 번역 정보
    translated_text: Optional[str] = None
    translation_used: bool = False

    # 상세 정보
    positive_words: List[str] = field(default_factory=list)
    negative_words: List[str] = field(default_factory=list)
    word_count: int = 0

    # 메타데이터
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    analyzer_type: str = 'multilingual'

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        result = {
            'text': self.text[:200],
            'detected_language': self.detected_language,
            'sentiment_label': self.label,
            'sentiment_score': round(self.sentiment_score, 4),
            'positive_score': round(self.positive_score, 4),
            'negative_score': round(self.negative_score, 4),
            'confidence': round(self.confidence, 4),
            'positive_words': ', '.join(self.positive_words[:10]),
            'negative_words': ', '.join(self.negative_words[:10]),
            'word_count': self.word_count,
            'analyzed_at': self.analyzed_at,
            'analyzer_type': self.analyzer_type,
            'translation_used': self.translation_used
        }

        if self.translated_text:
            result['translated_text'] = self.translated_text[:200]

        # 언어별 결과
        for lang, lang_result in self.language_results.items():
            result[f'{lang}_sentiment_score'] = round(lang_result.sentiment_score, 4)
            result[f'{lang}_sentiment_label'] = lang_result.label

        return result


# ============================================================================
# 다국어 감정 분석기
# ============================================================================

class MultilingualSentimentAnalyzer:
    """다국어 감정 분석 메인 클래스"""

    def __init__(self, config: Optional[MultilingualSentimentConfig] = None):
        self.config = config or MultilingualSentimentConfig()
        self.korean_analyzer = None
        self.translation_service = None
        self.language_analyzers: Dict[str, SentimentAnalyzer] = {}

        # 한국어 분석기 초기화
        if KONLPY_AVAILABLE:
            self.korean_analyzer = SentimentAnalyzer(self.config.base_config)

        # 번역 서비스 초기화
        if self.config.use_translation:
            self._init_translation_service()

        # 언어별 분석기 초기화
        self._init_language_analyzers()

        logger.info(f"다국어 감정 분석기 초기화 완료 (지원 언어: {len(self.config.enabled_languages)})")

    def _init_translation_service(self) -> None:
        """번역 서비스 초기화"""
        try:
            translation_config = TranslationConfig(self.config.translation_config_file)
            self.translation_service = TranslationService(
                credentials_path=translation_config.get_credentials_path(),
                api_key=translation_config.get_api_key()
            )

            if self.translation_service.is_available():
                logger.info("번역 서비스 초기화 성공")
            else:
                logger.warning("번역 서비스를 사용할 수 없습니다.")
                self.translation_service = None
        except Exception as e:
            logger.warning(f"번역 서비스 초기화 오류: {e}")
            self.translation_service = None

    def _init_language_analyzers(self) -> None:
        """언어별 감정 분석기 초기화"""
        for lang in self.config.enabled_languages:
            if lang == Language.KOREAN.value and self.korean_analyzer:
                self.language_analyzers[lang] = self.korean_analyzer
            elif lang in LANGUAGE_SENTIMENT_DICTS:
                # 기본 설정 사용 (각 언어 사전 로드)
                try:
                    self.language_analyzers[lang] = self._create_basic_analyzer(lang)
                    logger.debug(f"{lang} 언어 분석기 초기화 성공")
                except Exception as e:
                    logger.warning(f"{lang} 언어 분석기 초기화 실패: {e}")

    def _create_basic_analyzer(self, language: str) -> SentimentAnalyzer:
        """기본 언어 분석기 생성"""
        config = SentimentConfig(tokenizer_type='basic')

        # 언어별 감정 사전 설정
        if language in LANGUAGE_SENTIMENT_DICTS:
            # 이 부분은 SentimentAnalyzer가 사전을 받을 수 있도록 수정 필요
            # 현재는 기본 분석기 반환
            pass

        return SentimentAnalyzer(config)

    def detect_language(self, text: str) -> str:
        """텍스트 언어 감지"""
        if not self.translation_service or not self.config.auto_detect_language:
            return self.config.default_language

        detected = self.translation_service.detect_language(text)
        return detected if detected else self.config.default_language

    def analyze_basic(self, text: str, language: str) -> float:
        """기본 감정 분석 (형태소 분석 없이 단어 매칭만)"""
        if not text or not text.strip():
            return 0.0

        if language not in LANGUAGE_SENTIMENT_DICTS:
            return 0.0

        sentiment_dict = LANGUAGE_SENTIMENT_DICTS[language]

        # 텍스트를 단어로 분리 (간단한 방식)
        words = self._tokenize_basic(text, language)

        positive_count = 0
        negative_count = 0
        intensifier_count = 0
        negation_count = 0

        for word in words:
            word_lower = word.lower()
            if word_lower in sentiment_dict['positive']:
                positive_count += 1
            elif word_lower in sentiment_dict['negative']:
                negative_count += 1
            elif word_lower in sentiment_dict['intensifiers']:
                intensifier_count += 1
            elif word_lower in sentiment_dict['negations']:
                negation_count += 1

        # 감정 점수 계산
        pos_score = positive_count
        neg_score = negative_count

        # 강조어 보정
        if intensifier_count > 0:
            factor = 1.5 ** intensifier_count
            pos_score *= factor
            neg_score *= factor

        # 부정어 보정
        if negation_count > 0:
            factor = -1.3 ** negation_count
            total_score = (pos_score + neg_score) * factor
        else:
            total_score = pos_score - neg_score

        # 정규화
        max_score = max(abs(pos_score), abs(neg_score), 1)
        normalized_score = total_score / max_score

        return max(-1.0, min(1.0, normalized_score))

    def _tokenize_basic(self, text: str, language: str) -> List[str]:
        """기본 토크나이징 (언어별)"""
        if not text:
            return []

        # 전처리
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # 언어별 토크나이징
        if language in [Language.KOREAN.value, Language.JAPANESE.value, Language.CHINESE.value]:
            # 한자/한글 문자 분리
            if language == Language.KOREAN.value:
                tokens = re.findall(r'[가-힣]{2,}', text)
            elif language == Language.JAPANESE.value:
                tokens = re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]{2,}', text)
            else:  # Chinese
                tokens = re.findall(r'[\u4E00-\u9FAF]{2,}', text)
        else:
            # 알파벳 기반 언어
            tokens = text.split()

        return [token.lower() for token in tokens if len(token) > 1]

    def analyze(self, text: str, target_language: Optional[str] = None) -> MultilingualSentimentResult:
        """텍스트 감정 분석 (다국어)"""
        if not text or not text.strip():
            return self._create_neutral_result(text or "")

        # 언어 감지
        detected_language = self.detect_language(text)

        # 기본 분석
        basic_score = self.analyze_basic(text, detected_language)

        # 한국어의 경우 고급 분석기 사용
        if detected_language == Language.KOREAN.value and self.korean_analyzer:
            korean_result = self.korean_analyzer.analyze(text)
            basic_score = korean_result.sentiment_score

        # 번역 사용 및 추가 언어 분석
        language_results = {}
        translated_text = None
        translation_used = False

        if self.translation_service and self.translation_service.is_available():
            # 영어로 번역하여 분석
            if detected_language != Language.ENGLISH.value:
                try:
                    translated_text = self.translation_service.translate(text, Language.ENGLISH.value)
                    if translated_text:
                        translation_used = True
                        english_score = self.analyze_basic(translated_text, Language.ENGLISH.value)

                        # 영어 결과 생성
                        english_result = SentimentResult(
                            text=translated_text[:200],
                            label=self._get_label_from_score(english_score),
                            confidence=min(1.0, 0.6 + abs(english_score) * 0.4),
                            sentiment_score=english_score,
                            positive_score=max(0, english_score),
                            negative_score=max(0, -english_score)
                        )
                        language_results[Language.ENGLISH.value] = english_result
                except Exception as e:
                    logger.warning(f"번역 오류: {e}")

        # 원본 언어 결과 추가
        original_result = SentimentResult(
            text=text[:200],
            label=self._get_label_from_score(basic_score),
            confidence=min(1.0, 0.6 + abs(basic_score) * 0.4),
            sentiment_score=basic_score,
            positive_score=max(0, basic_score),
            negative_score=max(0, -basic_score)
        )
        language_results[detected_language] = original_result

        # 통합 점수 계산
        if self.config.combine_results and len(language_results) > 1:
            combined_score = self._combine_scores([r.sentiment_score for r in language_results.values()])
        else:
            combined_score = basic_score

        # 단어 추출 (간단)
        positive_words, negative_words = self._extract_sentiment_words(text, detected_language)

        return MultilingualSentimentResult(
            text=text[:200],
            detected_language=detected_language,
            label=self._get_label_from_score(combined_score),
            confidence=min(1.0, 0.7 + abs(combined_score) * 0.3),
            sentiment_score=combined_score,
            positive_score=max(0, combined_score),
            negative_score=max(0, -combined_score),
            language_results=language_results,
            translated_text=translated_text,
            translation_used=translation_used,
            positive_words=positive_words,
            negative_words=negative_words,
            word_count=len(self._tokenize_basic(text, detected_language))
        )

    def _get_label_from_score(self, score: float) -> str:
        """점수에서 라벨 생성"""
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        else:
            return 'neutral'

    def _combine_scores(self, scores: List[float]) -> float:
        """여러 점수 통합"""
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def _extract_sentiment_words(self, text: str, language: str) -> Tuple[List[str], List[str]]:
        """감정 단어 추출"""
        if language not in LANGUAGE_SENTIMENT_DICTS:
            return [], []

        sentiment_dict = LANGUAGE_SENTIMENT_DICTS[language]
        words = self._tokenize_basic(text, language)

        positive_words = []
        negative_words = []

        for word in words:
            word_lower = word.lower()
            if word_lower in sentiment_dict['positive']:
                positive_words.append(word)
            elif word_lower in sentiment_dict['negative']:
                negative_words.append(word)

        return positive_words[:10], negative_words[:10]

    def _create_neutral_result(self, text: str) -> MultilingualSentimentResult:
        """중립 결과 생성"""
        return MultilingualSentimentResult(
            text=text[:200] if text else "",
            detected_language=self.config.default_language,
            label='neutral',
            confidence=0.0,
            sentiment_score=0.0,
            positive_score=0.0,
            negative_score=0.0,
            word_count=0
        )

    def analyze_batch(self, texts: List[str]) -> List[MultilingualSentimentResult]:
        """여러 텍스트 일괄 분석"""
        results = []
        total = len(texts)

        for i, text in enumerate(texts):
            result = self.analyze(text)
            results.append(result)

            if (i + 1) % 10 == 0:
                logger.info(f"다국어 감정 분석 진행: {i + 1}/{total}")

        return results

    def analyze_data(self, data: List[Dict]) -> List[Dict]:
        """크롤링 데이터에 다국어 감정 분석 결과 추가"""
        for item in data:
            # 다양한 필드 확인
            text_fields = ['title', 'content', 'description', '요약', '제목', '본문']
            combined_text = ""

            for field in text_fields:
                if field in item and item[field]:
                    combined_text += f"{item[field]} "

            # 번역된 텍스트도 확인
            translated_fields = ['title_translated', 'content_translated', '요약_translated', '제목_translated']
            for field in translated_fields:
                if field in item and item[field]:
                    combined_text += f"{item[field]} "

            if combined_text.strip():
                # 감정 분석
                result = self.analyze(combined_text.strip())

                # 결과에 추가
                item.update(result.to_dict())

        return data

    def get_supported_languages(self) -> Dict[str, str]:
        """지원하는 언어 목록"""
        return Language.get_all_supported()


# ============================================================================
# 다국어 감정 필터
# ============================================================================

class MultilingualSentimentFilter:
    """다국어 감정 기반 데이터 필터링"""

    @staticmethod
    def filter_by_language(data: List[Dict], language: str) -> List[Dict]:
        """언어로 필터링"""
        return [
            item for item in data
            if item.get('detected_language') == language
        ]

    @staticmethod
    def filter_by_sentiment_and_language(
        data: List[Dict],
        sentiment: str = 'positive',
        language: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[Dict]:
        """감정과 언어로 필터링"""
        filtered = [
            item for item in data
            if item.get('sentiment_label') == sentiment
            and abs(item.get('sentiment_score', 0)) >= min_score
        ]

        if language:
            filtered = [item for item in filtered if item.get('detected_language') == language]

        return filtered

    @staticmethod
    def get_language_sentiment_distribution(data: List[Dict]) -> Dict[str, Dict[str, int]]:
        """언어별 감정 분포"""
        distribution = {}

        for item in data:
            lang = item.get('detected_language', 'unknown')
            sentiment = item.get('sentiment_label', 'neutral')

            if lang not in distribution:
                distribution[lang] = {'positive': 0, 'negative': 0, 'neutral': 0}

            distribution[lang][sentiment] += 1

        return distribution

    @staticmethod
    def get_multilingual_summary(data: List[Dict]) -> Dict:
        """다국어 감정 분석 요약"""
        if not data:
            return {}

        # 전체 통계
        total_count = len(data)
        positive_items = [d for d in data if d.get('sentiment_label') == 'positive']
        negative_items = [d for d in data if d.get('sentiment_label') == 'negative']
        neutral_items = [d for d in data if d.get('sentiment_label') == 'neutral']

        # 언어별 통계
        language_dist = MultilingualSentimentFilter.get_language_sentiment_distribution(data)
        translation_usage = sum(1 for d in data if d.get('translation_used', False))

        avg_scores = {
            'avg_sentiment_score': sum(d.get('sentiment_score', 0) for d in data) / total_count,
            'avg_positive_score': sum(d.get('positive_score', 0) for d in data) / total_count,
            'avg_negative_score': sum(d.get('negative_score', 0) for d in data) / total_count
        }

        return {
            'total_count': total_count,
            'positive_count': len(positive_items),
            'negative_count': len(negative_items),
            'neutral_count': len(neutral_items),
            'positive_ratio': len(positive_items) / total_count if total_count else 0,
            'negative_ratio': len(negative_items) / total_count if total_count else 0,
            'neutral_ratio': len(neutral_items) / total_count if total_count else 0,
            'language_distribution': language_dist,
            'translation_usage_count': translation_usage,
            'translation_usage_ratio': translation_usage / total_count if total_count else 0,
            **avg_scores
        }


# ============================================================================
# 메인 함수
# ============================================================================

def main():
    """메인 함수 - 테스트용"""
    print("=" * 80)
    print("🌍 다국어 감정 분석 시스템 테스트")
    print("=" * 80)

    # 다국어 분석기 초기화
    config = MultilingualSentimentConfig(
        use_translation=True,
        enabled_languages=['ko', 'en', 'ja', 'zh', 'es']
    )

    analyzer = MultilingualSentimentAnalyzer(config)

    print(f"\n📋 지원 언어:")
    for code, name in analyzer.get_supported_languages().items():
        if code in config.enabled_languages:
            print(f"  ✅ {code}: {name}")
        else:
            print(f"  ⭕ {code}: {name}")

    # 테스트 텍스트 (다국어)
    test_texts = [
        # 한국어
        ("이 제품은 정말 혁신적이고 기대가 됩니다. 성능이 매우 우수합니다.", "ko"),
        ("실망스럽습니다. 품질이 너무 나쁘고 문제가 많습니다.", "ko"),

        # 영어
        ("This product is truly innovative and promising. The performance is excellent.", "en"),
        ("Very disappointing. The quality is poor and there are many issues.", "en"),

        # 일본어
        ("この製品は本当に革新的で期待できます。性能が非常に優秀です。", "ja"),
        ("失望しました。品質が悪すぎて問題が多いです。", "ja"),

        # 중국어
        ("这个产品真的很有创新性，值得期待。性能非常优秀。", "zh"),
        ("很失望。质量太差了，问题很多。", "zh"),
    ]

    print("\n🧪 다국어 감정 분석 테스트:")
    print("=" * 80)

    for i, (text, expected_lang) in enumerate(test_texts, 1):
        print(f"\n[{i}] {text[:50]}...")
        print(f"   예상 언어: {expected_lang}")

        try:
            result = analyzer.analyze(text)

            print(f"   감지 언어: {result.detected_language}")
            print(f"   감정: {result.label}")
            print(f"   점수: {result.sentiment_score:.3f}")
            print(f"   신뢰도: {result.confidence:.3f}")

            if result.translation_used:
                print(f"   번역 사용: ✅ ({result.translated_text[:30]}...)")
            else:
                print(f"   번역 사용: ❌")

            # 언어별 결과
            if result.language_results:
                print(f"   언어별 분석:")
                for lang, lang_result in result.language_results.items():
                    print(f"     {lang}: {lang_result.label} ({lang_result.sentiment_score:.3f})")

        except Exception as e:
            print(f"   ❌ 오류: {e}")

    # 통계 요약
    print("\n" + "=" * 80)
    print("📊 통계 요약")
    print("=" * 80)

    # 더미 데이터 생성
    dummy_data = []
    for text, _ in test_texts:
        result = analyzer.analyze(text)
        dummy_data.append(result.to_dict())

    summary = MultilingualSentimentFilter.get_multilingual_summary(dummy_data)

    print(f"\n총 {summary['total_count']}개 분석:")
    print(f"  긍정: {summary['positive_count']}개 ({summary['positive_ratio']:.1%})")
    print(f"  부정: {summary['negative_count']}개 ({summary['negative_ratio']:.1%})")
    print(f"  중립: {summary['neutral_count']}개 ({summary['neutral_ratio']:.1%})")
    print(f"\n평균 감정 점수: {summary['avg_sentiment_score']:.3f}")
    print(f"번역 사용률: {summary['translation_usage_ratio']:.1%}")

    print(f"\n언어별 분포:")
    for lang, counts in summary['language_distribution'].items():
        lang_name = Language.get_language_name(lang)
        print(f"  {lang_name} ({lang}):")
        print(f"    긍정: {counts['positive']}, 부정: {counts['negative']}, 중립: {counts['neutral']}")

    print("\n✨ 테스트 완료!")


if __name__ == "__main__":
    main()