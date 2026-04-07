"""
Refiner GUI Theme and Stylesheets
"""

COLORS = {
    "bg_darkest":   "#0D1117",   # 최상위 배경
    "bg_dark":      "#161B22",   # 패널 배경
    "bg_medium":    "#21262D",   # 입력창 배경
    "bg_light":     "#30363D",   # 호버/선택 배경
    "border":       "#30363D",   # 테두리
    "border_accent":"#388BFD",   # 강조 테두리
    "text_primary": "#E6EDF3",   # 기본 텍스트
    "text_muted":   "#8B949E",   # 보조 텍스트
    "accent_blue":  "#388BFD",   # 주요 강조색 (파랑)
    "accent_green": "#3FB950",   # 성공 (초록)
    "accent_orange":"#D29922",   # 경고 (주황)
    "accent_purple":"#BC8CFF",   # Java 강조 (보라)
    "accent_red":   "#F85149",   # 에러 (빨강)
    "btn_sql_from": "#1C3A5C",
    "btn_sql_to":   "#1F4A85",
    "btn_java_from":"#2D1A4A",
    "btn_java_to":  "#3D2260",
    "btn_json_from":"#1A3D36",
    "btn_json_to":  "#24594E",
    "btn_clear_from":"#2A1A1A",
    "btn_clear_to": "#3D2222",
}

STYLESHEET = f"""
/* ── 전체 앱 배경 ────────────────── */
QMainWindow, QWidget {{
    background-color: {COLORS['bg_darkest']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
    font-size: 13px;
}}

/* ── 텍스트 에디터 ────────────────── */
QPlainTextEdit, QTextEdit {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px;
    font-family: 'JetBrains Mono', 'Consolas', 'D2Coding', monospace;
    font-size: 13px;
    line-height: 1.5;
    selection-background-color: {COLORS['accent_blue']};
    selection-color: white;
}}
QPlainTextEdit:focus, QTextEdit:focus {{
    border: 1px solid {COLORS['border_accent']};
}}

/* ── 스크롤바 ─────────────────── */
QScrollBar:vertical {{
    background: {COLORS['bg_dark']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['bg_light']};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS['accent_blue']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: {COLORS['bg_dark']};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['bg_light']};
    border-radius: 4px;
}}

/* ── 구분선 ─────────────────── */
QFrame[frameShape="5"] {{
    color: {COLORS['border']};
}}
QSplitter::handle {{
    background: {COLORS['border']};
    width: 2px;
    border-radius: 1px;
}}
QSplitter::handle:hover {{
    background: {COLORS['accent_blue']};
}}

/* ── 상태바 ─────────────────── */
QStatusBar {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_muted']};
    border-top: 1px solid {COLORS['border']};
    padding: 2px 8px;
    font-size: 11px;
}}

/* ── 라벨 ─────────────────── */
QLabel {{
    color: {COLORS['text_muted']};
    background: transparent;
}}

/* ── 콤보박스 ─────────────────── */
QComboBox {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 4px 10px;
    min-width: 150px;
}}
QComboBox:hover {{
    border-color: {COLORS['accent_blue']};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['accent_blue']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}

/* ── 툴바 ─────────────────── */
QToolBar {{
    background-color: {COLORS['bg_dark']};
    border-bottom: 1px solid {COLORS['border']};
    spacing: 6px;
    padding: 4px 8px;
}}
"""

BUTTON_SQL_STYLE = f"""
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['btn_sql_from']}, stop:1 {COLORS['btn_sql_to']});
    color: #79C0FF;
    border: 1px solid #388BFD40;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 13px;
    letter-spacing: 0.3px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1F4A85, stop:1 #2255A0);
    border-color: {COLORS['accent_blue']};
    color: white;
}}
QPushButton:pressed {{
    background: {COLORS['btn_sql_from']};
    padding-top: 12px;
    padding-bottom: 8px;
}}
"""

BUTTON_JAVA_STYLE = f"""
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['btn_java_from']}, stop:1 {COLORS['btn_java_to']});
    color: #D2A8FF;
    border: 1px solid {COLORS['border']};  /* 중립적인 테두리 색으로 변경하여 혼동 방지 */
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 13px;
    letter-spacing: 0.3px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3D2260, stop:1 #522D80);
    border-color: {COLORS['accent_purple']};
    color: white;
}}
QPushButton:pressed {{
    background: {COLORS['btn_java_from']};
    padding-top: 12px;
    padding-bottom: 8px;
}}
"""

BUTTON_JSON_STYLE = f"""
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS['btn_json_from']}, stop:1 {COLORS['btn_json_to']});
    color: #56D364;
    border: 1px solid #3FB95040;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 13px;
    letter-spacing: 0.3px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #24594E, stop:1 #2B7062);
    border-color: {COLORS['accent_green']};
    color: white;
}}
QPushButton:pressed {{
    background: {COLORS['btn_json_from']};
    padding-top: 12px;
    padding-bottom: 8px;
}}
"""

BUTTON_CLEAR_STYLE = f"""
QPushButton {{
    background: transparent;
    color: {COLORS['text_muted']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 13px;
}}
QPushButton:hover {{
    background: {COLORS['btn_clear_from']};
    color: {COLORS['accent_red']};
    border-color: {COLORS['accent_red']}60;
}}
QPushButton:pressed {{
    background: {COLORS['btn_clear_to']};
}}
"""

BUTTON_COPY_STYLE = f"""
QPushButton {{
    background: transparent;
    color: {COLORS['text_muted']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px 16px;
    font-size: 12px;
}}
QPushButton:hover {{
    background: {COLORS['bg_light']};
    color: {COLORS['accent_green']};
    border-color: {COLORS['accent_green']}60;
}}
"""
