"""
Refiner - Developer Utility Tool
Main GUI Application using PyQt6
Dark mode, SQL Formatter + Java VO Generator
"""

import sys
import os
import re

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTextEdit, QPlainTextEdit, QPushButton, QLabel,
    QStatusBar, QFrame, QSizePolicy, QToolBar, QMessageBox,
    QComboBox, QSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QSyntaxHighlighter, QTextCharFormat,
    QIcon, QTextDocument, QClipboard, QKeySequence, QShortcut,
    QAction, QLinearGradient, QBrush, QPainter
)
import pyperclip

from core.sql_formatter import format_multiple_statements
from core.java_vo_generator import generate_java_vo
from core.json_formatter import format_json


from ui.theme import COLORS, STYLESHEET, BUTTON_SQL_STYLE, BUTTON_JAVA_STYLE, BUTTON_JSON_STYLE, BUTTON_CLEAR_STYLE, BUTTON_COPY_STYLE
from ui.highlighters import SqlHighlighter, JavaHighlighter, JsonHighlighter

# ──────────────────────────────────────────────
# 메인 위젯: 입력 패널
# ──────────────────────────────────────────────
class InputPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)  # 상단 여백 추가 (OutputPanel과 수평 맞춤)
        layout.setSpacing(8)

        # 헤더
        header = QHBoxLayout()
        title_label = QLabel("  📝  SQL INPUT")
        title_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 2px;
            background: {COLORS['bg_dark']};
            padding: 8px 12px;
            border-radius: 6px 6px 0 0;
        """)
        line_count_label = QLabel("줄 수: 0")
        line_count_label.setObjectName("line_count")
        line_count_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent; margin-right: 16px;")
        header.addWidget(title_label)
        header.addStretch()
        header.addWidget(line_count_label)
        layout.addLayout(header)

        # 텍스트 에디터
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(
            "여기에 SQL이나 JSON을 입력하세요...\n\n"
            "예시 1) SELECT 정렬:\n"
            "  select u.id, u.name, u.email from users u where u.active = 1 order by u.created_at desc;\n\n"
            "예시 2) Java VO 생성:\n"
            "  CREATE TABLE TB_USER (USER_ID NUMBER(10,0), USER_NM VARCHAR2(100), EMAIL VARCHAR2(200), REG_DT DATE);\n\n"
            "예시 3) JSON 정렬:\n"
            "  {\"name\":\"Refiner\",\"version\":\"0.1.0\",\"features\":[\"SQL\",\"Java VO\",\"JSON\"]}"
        )
        self.editor.setMinimumHeight(200)
        
        # 탭 간격을 스페이스 4칸 기준으로 설정해 보기 좋게 맞춤
        font_metrics = self.editor.fontMetrics()
        tab_width = font_metrics.horizontalAdvance(' ') * 4
        self.editor.setTabStopDistance(float(tab_width))
        
        self.editor.textChanged.connect(self._on_text_changed)

        # SQL 하이라이터 적용
        self.highlighter = SqlHighlighter(self.editor.document())

        layout.addWidget(self.editor)
        self.line_count_label = line_count_label

    def _on_text_changed(self):
        lines = len(self.editor.toPlainText().splitlines())
        self.line_count_label.setText(f"줄 수: {lines}")

    def get_text(self) -> str:
        return self.editor.toPlainText()

    def clear(self):
        self.editor.clear()


# ──────────────────────────────────────────────
# 메인 위젯: 출력 패널
# ──────────────────────────────────────────────
class OutputPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_mode = "sql"  # "sql" or "java"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)  # 상단 여백 추가
        layout.setSpacing(8)

        # 헤더
        header = QHBoxLayout()
        self.title_label = QLabel("  💡  OUTPUT")
        self.title_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 2px;
            background: {COLORS['bg_dark']};
            padding: 8px 12px;
            border-radius: 6px 6px 0 0;
        """)

        self.copy_btn = QPushButton("📋 복사")
        self.copy_btn.setStyleSheet(BUTTON_COPY_STYLE)
        self.copy_btn.setFixedHeight(32)
        self.copy_btn.setToolTip("결과를 클립보드에 복사 (Ctrl+Shift+C)")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)

        self.copy_status = QLabel("")
        self.copy_status.setStyleSheet(f"color: {COLORS['accent_green']}; font-size: 11px; background: transparent;")

        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.copy_status)
        header.addWidget(self.copy_btn)
        layout.addLayout(header)

        # 출력 텍스트
        self.viewer = QPlainTextEdit()
        self.viewer.setReadOnly(True)
        self.viewer.setPlaceholderText("결과가 여기에 표시됩니다.")
        
        # 탭 간격을 스페이스 4칸 기준으로 설정
        font_metrics = self.viewer.fontMetrics()
        tab_width = font_metrics.horizontalAdvance(' ') * 4
        self.viewer.setTabStopDistance(float(tab_width))

        self.sql_highlighter = SqlHighlighter(self.viewer.document())
        self.java_highlighter = None  # 상황에 따라 교체

        layout.addWidget(self.viewer)

    def set_output(self, text: str, mode: str = "sql"):
        """결과 텍스트 설정 및 하이라이터 교체."""
        self._current_mode = mode
        self.viewer.setPlainText(text)

        # 하이라이터 교체
        self.sql_highlighter = None
        self.java_highlighter = None
        if hasattr(self, 'json_highlighter'):
            self.json_highlighter = None
            
        base_style = f"""
            color: {COLORS['text_primary']};
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 2px;
            padding: 8px 12px;
            border-radius: 6px 6px 0 0;
        """

        if mode == "java":
            self.java_highlighter = JavaHighlighter(self.viewer.document())
            self.title_label.setText("  ☕  JAVA VO OUTPUT")
            self.title_label.setStyleSheet(base_style + "background: #1C1028;")
        elif mode == "json":
            self.json_highlighter = JsonHighlighter(self.viewer.document())
            self.title_label.setText("  🔧  JSON OUTPUT")
            self.title_label.setStyleSheet(base_style + "background: #0B1D19;")
        else:
            self.sql_highlighter = SqlHighlighter(self.viewer.document())
            self.title_label.setText("  ✨  SQL OUTPUT")
            self.title_label.setStyleSheet(base_style + f"background: {COLORS['bg_dark']};")

    def copy_to_clipboard(self):
        text = self.viewer.toPlainText()
        if not text:
            return
        try:
            pyperclip.copy(text)
            self._flash_copy_status()
        except Exception:
            # pyperclip 실패 시 Qt 클립보드 사용
            QApplication.clipboard().setText(text)
            self._flash_copy_status()

    def _flash_copy_status(self):
        self.copy_status.setText("✓ 복사됨!")
        QTimer.singleShot(2000, lambda: self.copy_status.setText(""))

    def get_text(self) -> str:
        return self.viewer.toPlainText()


# ──────────────────────────────────────────────
# 액션 버튼 패널
# ──────────────────────────────────────────────
class ActionPanel(QWidget):
    sql_format_requested = pyqtSignal()
    java_vo_requested = pyqtSignal()
    json_format_requested = pyqtSignal()
    clear_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(10)

        # SQL 정렬 버튼
        self.btn_sql = QPushButton("⚡  SQL 정렬 실행")
        self.btn_sql.setStyleSheet(BUTTON_SQL_STYLE)
        self.btn_sql.setMinimumHeight(44)
        self.btn_sql.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 포커스 테두리 제거

        # Java VO 변환 버튼
        self.btn_java = QPushButton("☕  Java VO 변환 실행")
        self.btn_java.setStyleSheet(BUTTON_JAVA_STYLE)
        self.btn_java.setMinimumHeight(44)
        self.btn_java.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # JSON 정렬 버튼
        self.btn_json = QPushButton("🔧  JSON 정렬 실행")
        self.btn_json.setStyleSheet(BUTTON_JSON_STYLE)
        self.btn_json.setMinimumHeight(44)
        self.btn_json.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # 클리어 버튼
        self.btn_clear = QPushButton("🗑  초기화")
        self.btn_clear.setStyleSheet(BUTTON_CLEAR_STYLE)
        self.btn_clear.setMinimumHeight(44)
        self.btn_clear.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.btn_sql.clicked.connect(self.sql_format_requested.emit)
        self.btn_java.clicked.connect(self.java_vo_requested.emit)
        self.btn_json.clicked.connect(self.json_format_requested.emit)
        self.btn_clear.clicked.connect(self.clear_requested.emit)

        layout.addWidget(self.btn_sql, 2)
        layout.addWidget(self.btn_java, 2)
        layout.addWidget(self.btn_json, 2)
        layout.addWidget(self.btn_clear, 1)


# ──────────────────────────────────────────────
# 메인 윈도우
# ──────────────────────────────────────────────
class RefinerMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Refiner  —  Developer Utility")
        self.setWindowIcon(QIcon(resource_path("assets/images/icon.ico")))
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        self._setup_ui()
        self._setup_shortcuts()
        self._apply_styles()

    def _setup_ui(self):
        # 중앙 위젯
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(0)

        # 헤더 배너
        banner = self._create_banner()
        main_layout.addWidget(banner)

        # 스플리터: 입력 | 출력
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(6)

        self.input_panel = InputPanel()
        self.output_panel = OutputPanel()

        self.splitter.addWidget(self.input_panel)
        self.splitter.addWidget(self.output_panel)
        self.splitter.setSizes([550, 550])

        main_layout.addWidget(self.splitter, 1)

        # 액션 버튼 패널
        self.action_panel = ActionPanel()
        self.action_panel.sql_format_requested.connect(self._run_sql_format)
        self.action_panel.java_vo_requested.connect(self._run_java_vo)
        self.action_panel.json_format_requested.connect(self._run_json_format)
        self.action_panel.clear_requested.connect(self._clear_all)
        main_layout.addWidget(self.action_panel)

        # 상태바
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("준비  |  Ctrl+Enter: SQL 정렬  |  Ctrl+Shift+Enter: Java VO  |  Alt+J: JSON 정렬  |  Ctrl+Shift+C: 복사")

    def _create_banner(self) -> QWidget:
        frame = QFrame()
        frame.setFixedHeight(72)  # 높이를 72로 확장해 여유공간 확보
        frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0D1117,
                    stop:0.3 #131C2E,
                    stop:0.7 #1A1030,
                    stop:1 #0D1117);
                border-bottom: 2px solid {COLORS['border']};
                border-radius: 0;
                margin: 0;
            }}
        """)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(24, 12, 24, 12)  # 내부 패딩을 줘서 답답함 해소

        # 로고 아이콘 (이미지 파일 사용)
        logo_icon = QLabel()
        pixmap = QIcon(resource_path("assets/images/icon.ico")).pixmap(32, 32)
        logo_icon.setPixmap(pixmap)
        logo_icon.setStyleSheet("background: transparent;")

        # 로고 텍스트
        logo_text = QLabel("<b>REFINER</b>")
        logo_text.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 22px;
            font-weight: 800;
            letter-spacing: 5px;
            background: transparent;
            margin-left: 8px;
        """)

        # 태그라인
        tagline = QLabel("Developer Utility  ·  SQL / Java / JSON Formatter")
        tagline.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 12px;
            letter-spacing: 0.5px;
            background: transparent;
            margin-left: 20px;
        """)

        # 버전 배지
        version_badge = QLabel("v1.0.0-stable")
        version_badge.setFixedHeight(24)
        version_badge.setStyleSheet(f"""
            background: {COLORS['bg_light']};
            color: {COLORS['accent_blue']};
            border: 1px solid {COLORS['accent_blue']}50;
            border-radius: 12px;
            padding: 0 14px;
            font-size: 10px;
            font-weight: 700;
        """)

        layout.addWidget(logo_icon)
        layout.addWidget(logo_text)
        layout.addSpacing(16)
        layout.addWidget(tagline)
        layout.addStretch()
        layout.addWidget(version_badge)

        return frame

    def _setup_shortcuts(self):
        # Ctrl+Enter → SQL 정렬
        sc_sql = QShortcut(QKeySequence("Ctrl+Return"), self)
        sc_sql.activated.connect(self._run_sql_format)

        # Ctrl+Shift+Enter → Java VO
        sc_java = QShortcut(QKeySequence("Ctrl+Shift+Return"), self)
        sc_java.activated.connect(self._run_java_vo)

        # Alt+J → JSON 정렬
        sc_json = QShortcut(QKeySequence("Alt+J"), self)
        sc_json.activated.connect(self._run_json_format)

        # Ctrl+Shift+C → 결과 복사
        sc_copy = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        sc_copy.activated.connect(self.output_panel.copy_to_clipboard)

        # Ctrl+Delete → 초기화
        sc_clear = QShortcut(QKeySequence("Ctrl+Delete"), self)
        sc_clear.activated.connect(self._clear_all)

    def _apply_styles(self):
        self.setStyleSheet(STYLESHEET)

    # ── 핵심 로직 ────────────────────────────────

    def _run_sql_format(self):
        raw = self.input_panel.get_text().strip()
        if not raw:
            self.status_bar.showMessage("⚠  입력된 SQL이 없습니다.")
            return

        try:
            result = format_multiple_statements(raw)
            if not result:
                self.status_bar.showMessage("⚠  포맷 결과가 비어 있습니다.")
                return

            self.output_panel.set_output(result, mode="sql")

            # 자동 클립보드 복사
            try:
                pyperclip.copy(result)
            except Exception:
                QApplication.clipboard().setText(result)

            char_count = len(result)
            line_count = len(result.splitlines())
            self.status_bar.showMessage(
                f"✅  SQL 정렬 완료  |  {line_count}줄  {char_count}자  |  클립보드에 자동 복사됨"
            )

        except Exception as e:
            self.status_bar.showMessage(f"❌  오류: {str(e)}")
            self.output_panel.set_output(f"// Error during SQL formatting:\n// {str(e)}", mode="sql")

    def _run_java_vo(self):
        raw = self.input_panel.get_text().strip()
        if not raw:
            self.status_bar.showMessage("⚠  입력된 SQL이 없습니다.")
            return

        try:
            result = generate_java_vo(raw)
            self.output_panel.set_output(result, mode="java")

            # 자동 클립보드 복사
            try:
                pyperclip.copy(result)
            except Exception:
                QApplication.clipboard().setText(result)

            if result.startswith("//"):
                self.status_bar.showMessage("⚠  CREATE TABLE 문을 찾을 수 없습니다.")
            else:
                line_count = len(result.splitlines())
                self.status_bar.showMessage(
                    f"✅  Java VO 변환 완료  |  {line_count}줄  |  클립보드에 자동 복사됨"
                )

        except Exception as e:
            self.status_bar.showMessage(f"❌  오류: {str(e)}")
            self.output_panel.set_output(f"// Error during Java VO generation:\n// {str(e)}", mode="java")

    def _run_json_format(self):
        raw = self.input_panel.get_text().strip()
        if not raw:
            self.status_bar.showMessage("⚠  입력된 JSON이 없습니다.")
            return

        try:
            result = format_json(raw)
            if not result:
                self.status_bar.showMessage("⚠  포맷 결과가 비어 있습니다.")
                return

            self.output_panel.set_output(result, mode="json")

            # 자동 클립보드 복사
            try:
                pyperclip.copy(result)
            except Exception:
                QApplication.clipboard().setText(result)

            line_count = len(result.splitlines())
            self.status_bar.showMessage(
                f"✅  JSON 정렬 완료  |  {line_count}줄  |  클립보드에 자동 복사됨"
            )

        except Exception as e:
            self.status_bar.showMessage(f"❌  JSON 분석 오류")
            self.output_panel.set_output(f"// Error during JSON formatting:\n{str(e)}", mode="json")

    def _clear_all(self):
        self.input_panel.clear()
        self.output_panel.viewer.clear()
        self.output_panel.title_label.setText("  💡  OUTPUT")
        self.status_bar.showMessage("초기화 완료")


# ──────────────────────────────────────────────
# 엔트리 포인트
# ──────────────────────────────────────────────
def main():
    # 고DPI 지원 (QApplication 생성 전에 설정해야 함)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Refiner")
    app.setApplicationVersion("0.1.0")

    window = RefinerMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
