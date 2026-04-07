import re
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont

class SqlHighlighter(QSyntaxHighlighter):
    SQL_KEYWORDS = [
        "SELECT", "FROM", "WHERE", "AND", "OR", "NOT", "IN", "EXISTS",
        "LIKE", "BETWEEN", "IS", "NULL", "AS", "JOIN", "LEFT", "RIGHT",
        "INNER", "OUTER", "FULL", "ON", "GROUP", "BY", "HAVING", "ORDER",
        "LIMIT", "OFFSET", "UNION", "ALL", "DISTINCT", "CASE", "WHEN",
        "THEN", "ELSE", "END", "INSERT", "INTO", "VALUES", "UPDATE", "SET",
        "DELETE", "CREATE", "TABLE", "DROP", "ALTER", "ADD", "COLUMN",
        "PRIMARY", "KEY", "FOREIGN", "REFERENCES", "NOT", "NULL", "DEFAULT",
        "UNIQUE", "INDEX", "CONSTRAINT", "WITH", "RECURSIVE", "OVER",
        "PARTITION", "ROWNUM", "DUAL", "CONNECT", "START", "PRIOR",
        "NOCYCLE", "LEVEL", "MERGE", "USING", "MATCHED", "REPLACE",
        "VIEW", "SEQUENCE", "TRIGGER", "PROCEDURE", "FUNCTION", "DECLARE",
        "BEGIN", "EXCEPTION", "RAISE", "RETURN", "IF", "LOOP", "WHILE",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []
        self._build_rules()

    def _build_rules(self):
        # 키워드
        kw_fmt = QTextCharFormat()
        kw_fmt.setForeground(QColor("#79C0FF"))
        kw_fmt.setFontWeight(QFont.Weight.Bold)
        kw_pattern = r"\b(?:" + "|".join(self.SQL_KEYWORDS) + r")\b"
        self._rules.append((kw_pattern, kw_fmt, re.IGNORECASE))

        # 문자열 리터럴
        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor("#A5D6FF"))
        self._rules.append((r"'[^']*'", str_fmt, 0))

        # 숫자
        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor("#FFA657"))
        self._rules.append((r"\b\d+(?:\.\d+)?\b", num_fmt, 0))

        # 주석 (-- 한 줄)
        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#6A9955"))
        comment_fmt.setFontItalic(True)
        self._rules.append((r"--[^\n]*", comment_fmt, 0))

        # 주석 (/* */)
        block_comment_fmt = QTextCharFormat()
        block_comment_fmt.setForeground(QColor("#6A9955"))
        block_comment_fmt.setFontItalic(True)
        self._rules.append((r"/\*.*?\*/", block_comment_fmt, re.DOTALL))

        # 함수명
        func_fmt = QTextCharFormat()
        func_fmt.setForeground(QColor("#D2A8FF"))
        self._rules.append((r"\b\w+(?=\s*\()", func_fmt, 0))

        # 연산자
        op_fmt = QTextCharFormat()
        op_fmt.setForeground(QColor("#FF7B72"))
        self._rules.append((r"[=<>!+\-*/]", op_fmt, 0))

    def highlightBlock(self, text: str):
        for pattern, fmt, flags in self._rules:
            for m in re.finditer(pattern, text, flags):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


class JavaHighlighter(QSyntaxHighlighter):
    KEYWORDS = [
        "public", "private", "protected", "class", "interface", "extends",
        "implements", "import", "package", "static", "final", "void",
        "return", "if", "else", "for", "while", "new", "this", "super",
        "null", "true", "false", "instanceof", "throws", "throw", "try",
        "catch", "finally",
    ]
    TYPES = [
        "String", "Integer", "Long", "Double", "Float", "Boolean",
        "BigDecimal", "LocalDateTime", "LocalDate", "OffsetDateTime",
        "byte", "int", "long", "double", "float", "boolean", "Object",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []
        self._build_rules()

    def _build_rules(self):
        # 어노테이션
        ann_fmt = QTextCharFormat()
        ann_fmt.setForeground(QColor("#FFA657"))
        self._rules.append((r"@\w+", ann_fmt, 0))

        # 키워드
        kw_fmt = QTextCharFormat()
        kw_fmt.setForeground(QColor("#FF7B72"))
        kw_fmt.setFontWeight(QFont.Weight.Bold)
        kw_pattern = r"\b(?:" + "|".join(self.KEYWORDS) + r")\b"
        self._rules.append((kw_pattern, kw_fmt, 0))

        # 타입
        type_fmt = QTextCharFormat()
        type_fmt.setForeground(QColor("#79C0FF"))
        type_pattern = r"\b(?:" + "|".join(self.TYPES) + r")\b"
        self._rules.append((type_pattern, type_fmt, 0))

        # 문자열
        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor("#A5D6FF"))
        self._rules.append((r'"[^"]*"', str_fmt, 0))

        # 주석
        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#6A9955"))
        comment_fmt.setFontItalic(True)
        self._rules.append((r"//[^\n]*", comment_fmt, 0))
        self._rules.append((r"/\*.*?\*/", comment_fmt, re.DOTALL))

        # 클래스명 (대문자 시작)
        class_fmt = QTextCharFormat()
        class_fmt.setForeground(QColor("#D2A8FF"))
        self._rules.append((r"\b[A-Z]\w*\b", class_fmt, 0))

    def highlightBlock(self, text: str):
        for pattern, fmt, flags in self._rules:
            for m in re.finditer(pattern, text, flags):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


class JsonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []
        self._build_rules()

    def _build_rules(self):
        # 1. 문자열 값
        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor("#A5D6FF"))
        self._rules.append((r'"[^"\\]*(\\.[^"\\]*)*"', str_fmt, 0))

        # 2. 속성 키값 ("key":)
        key_fmt = QTextCharFormat()
        key_fmt.setForeground(QColor("#79C0FF"))
        self._rules.append((r'"[^"\\]*(\\.[^"\\]*)*"\s*(?=:)', key_fmt, 0))

        # 3. 숫자
        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor("#FFA657"))
        self._rules.append((r'\b-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b', num_fmt, 0))

        # 4. 불리언 및 Null
        bool_fmt = QTextCharFormat()
        bool_fmt.setForeground(QColor("#FF7B72"))
        bool_fmt.setFontWeight(QFont.Weight.Bold)
        self._rules.append((r'\b(?:true|false|null)\b', bool_fmt, 0))

    def highlightBlock(self, text: str):
        for pattern, fmt, flags in self._rules:
            for m in re.finditer(pattern, text, flags):
                self.setFormat(m.start(), m.end() - m.start(), fmt)
