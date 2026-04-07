"""
SQL Formatter - Custom Convention

원하는 출력 형태:
SELECT
\tCOL1,
\tCOL2
FROM
\tTABLE
WHERE
\tCONDITION
\tAND CONDITION2
ORDER BY
\tCOL DESC
;
"""

import re

TAB = "\t"


def _ki(depth: int) -> str:
    return TAB * (depth * 3)


def _ci(depth: int) -> str:
    return TAB * (depth * 3 + 1)


# ─────────────────────────────────────────────────────────────
# 메인 진입점
# ─────────────────────────────────────────────────────────────
def format_multiple_statements(raw_sql: str) -> str:
    if not raw_sql.strip():
        return ""
    stmts = split_by_semicolon(raw_sql)
    results = []
    for s in stmts:
        s = s.strip()
        if s:
            results.append(format_sql(s, depth=0))
    return "\n\n-- ─────────────────────────────────────\n\n".join(results)


def format_sql(raw_sql: str, depth: int = 0) -> str:
    sql = raw_sql.strip()
    if sql.endswith(";"):
        sql = sql[:-1].strip()
    if not sql:
        return ""

    clauses = extract_clauses(sql)
    if not clauses:
        return sql

    lines: list[str] = []
    for name, content in clauses:
        render_clause(name, content.strip(), depth, lines)

    result = "\n".join(lines)
    if depth == 0:
        result += "\n;"
    return result


# ─────────────────────────────────────────────────────────────
# 절 렌더링
# ─────────────────────────────────────────────────────────────
def render_clause(name: str, content: str, depth: int, lines: list) -> None:
    ki = _ki(depth)
    ci = _ci(depth)

    if name == "SELECT":
        lines.append(f"{ki}SELECT")
        cols = split_by_comma(content)
        for idx, col in enumerate(cols):
            col = col.strip()
            comma = "," if idx < len(cols) - 1 else ""
            lines.append(f"{ci}{upper_kw(col)}{comma}")

    elif name == "FROM":
        lines.append(f"{ki}FROM")
        tables = split_by_comma(content)
        for tbl in tables:
            lines.append(f"{ci}{tbl.strip()}")

    elif name in ("WHERE", "HAVING"):
        lines.append(f"{ki}{name}")
        conds = split_conditions(content)
        for connector, cond in conds:
            cond = cond.strip()
            prefix = f"{connector} " if connector else ""
            formatted = format_expr(cond, depth)
            lines.append(f"{ci}{prefix}{formatted}")

    elif name in ("ORDER BY", "GROUP BY"):
        lines.append(f"{ki}{name}")
        items = split_by_comma(content)
        for item in items:
            lines.append(f"{ci}{item.strip()}")

    elif name in ("UNION", "UNION ALL", "INTERSECT", "EXCEPT"):
        lines.append(f"{ki}{name}")
        lines.append(format_sql(content, depth))

    elif "JOIN" in name:
        # "LEFT JOIN t ON cond" → JOIN keyword / table / ON / condition
        on_pos = find_kw_top(content, "ON")
        lines.append(f"{ki}{name}")
        if on_pos >= 0:
            lines.append(f"{ci}{content[:on_pos].strip()}")
            lines.append(f"{ki}ON")
            lines.append(f"{ci}{content[on_pos+2:].strip()}")
        else:
            lines.append(f"{ci}{content}")

    else:
        lines.append(f"{ki}{name}")
        if content:
            lines.append(f"{ci}{content}")


# ─────────────────────────────────────────────────────────────
# 표현식 포매팅 (서브쿼리 재귀)
# ─────────────────────────────────────────────────────────────
def format_expr(expr: str, depth: int) -> str:
    paren_pos = find_subquery_paren(expr)
    if paren_pos is None:
        return upper_kw(expr)

    paren_end = find_matching_paren(expr, paren_pos)
    if paren_end is None:
        return upper_kw(expr)

    before = upper_kw(expr[:paren_pos])
    inner = expr[paren_pos + 1: paren_end].strip()
    after = expr[paren_end + 1:]

    sub_depth = depth + 1
    sub_ki = _ki(sub_depth)

    sub_formatted = format_sql(inner, depth=sub_depth)
    result = f"{before}(\n{sub_formatted}\n{sub_ki})"

    if after.strip():
        result += upper_kw(after)
    return result


def upper_kw(text: str) -> str:
    keywords = [
        "SELECT", "FROM", "WHERE", "AND", "OR", "NOT", "IN", "EXISTS",
        "LIKE", "BETWEEN", "IS", "NULL", "AS", "ON", "CASE", "WHEN",
        "THEN", "ELSE", "END", "DISTINCT", "ASC", "DESC", "SET",
        "VALUES", "INNER", "LEFT", "RIGHT", "FULL", "OUTER", "CROSS",
        "GROUP", "ORDER", "BY", "HAVING", "LIMIT", "UNION", "ALL",
        "INTERSECT", "EXCEPT", "COUNT", "SUM", "AVG", "MAX", "MIN",
        "COALESCE", "NVL", "DECODE", "ROWNUM", "DUAL", "SYSDATE",
    ]
    pattern = r"\b(" + "|".join(keywords) + r")\b"
    return re.sub(pattern, lambda m: m.group(0).upper(), text, flags=re.IGNORECASE)


# ─────────────────────────────────────────────────────────────
# 절 분리 (clause extraction)
# ─────────────────────────────────────────────────────────────
# 긴 키워드 우선 (ORDER BY > ORDER)
_CLAUSES = [
    "ORDER BY", "GROUP BY",
    "UNION ALL", "INTERSECT ALL", "EXCEPT ALL",
    "LEFT OUTER JOIN", "RIGHT OUTER JOIN", "FULL OUTER JOIN",
    "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "CROSS JOIN", "FULL JOIN",
    "JOIN",
    "SELECT", "FROM", "WHERE", "HAVING",
    "UNION", "INTERSECT", "EXCEPT",
    "LIMIT", "OFFSET",
]


def extract_clauses(sql: str) -> list[tuple[str, str]]:
    """
    최상위(괄호 밖) SQL 키워드 경계를 찾아 (절이름, 내용) 리스트 반환.
    """
    su = sql.upper()
    n = len(sql)
    positions: list[tuple[int, str]] = []

    depth = 0
    in_str = False
    str_char = ""
    i = 0

    while i < n:
        ch = sql[i]

        # ── 문자열 내부
        if in_str:
            if ch == str_char:
                in_str = False
            i += 1
            continue

        # ── 문자열 시작
        if ch in ("'", '"'):
            in_str = True
            str_char = ch
            i += 1
            continue

        # ── 괄호 깊이 추적
        if ch == "(":
            depth += 1
            i += 1
            continue
        if ch == ")":
            if depth > 0:
                depth -= 1
            i += 1
            continue

        # ── 최상위에서만 절 키워드 탐색
        if depth == 0:
            matched_clause = ""
            for clause in _CLAUSES:
                cl = len(clause)
                if su[i: i + cl] == clause:
                    # 앞 경계: 시작이거나 단어 문자 아님
                    if i > 0 and (sql[i - 1].isalnum() or sql[i - 1] == "_"):
                        continue
                    # 뒤 경계: 끝이거나 단어 문자 아님
                    end_pos = i + cl
                    if end_pos < n and (sql[end_pos].isalnum() or sql[end_pos] == "_"):
                        continue
                    matched_clause = clause
                    break

            if matched_clause:
                positions.append((i, matched_clause))
                i += len(matched_clause)
                continue

        i += 1

    # 각 절의 내용 추출
    result: list[tuple[str, str]] = []
    for idx, (pos, name) in enumerate(positions):
        content_start = pos + len(name)
        content_end = positions[idx + 1][0] if idx + 1 < len(positions) else n
        content = sql[content_start:content_end].strip()
        result.append((name, content))
    return result


# ─────────────────────────────────────────────────────────────
# 조건 분리 (AND / OR at top level)
# ─────────────────────────────────────────────────────────────
def split_conditions(text: str) -> list[tuple[str, str]]:
    """
    depth=0의 AND/OR로 분리.
    반환: [(connector, condition), ...] connector = '' | 'AND' | 'OR'
    """
    results: list[tuple[str, str]] = []
    buf: list[str] = []
    connector = ""

    depth = 0
    in_str = False
    str_char = ""
    tu = text.upper()
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        if in_str:
            buf.append(ch)
            if ch == str_char:
                in_str = False
            i += 1
            continue

        if ch in ("'", '"'):
            in_str = True
            str_char = ch
            buf.append(ch)
            i += 1
            continue

        if ch == "(":
            depth += 1
            buf.append(ch)
            i += 1
            continue

        if ch == ")":
            if depth > 0:
                depth -= 1
            buf.append(ch)
            i += 1
            continue

        if depth == 0:
            # AND 감지
            if tu[i: i + 3] == "AND":
                pre_ok = (i == 0) or not (text[i - 1].isalnum() or text[i - 1] == "_")
                suf_idx = i + 3
                suf_ok = (suf_idx >= n) or not (text[suf_idx].isalnum() or text[suf_idx] == "_")
                if pre_ok and suf_ok:
                    part = "".join(buf).strip()
                    if part:
                        results.append((connector, part))
                    buf = []
                    connector = "AND"
                    i = suf_idx
                    # 공백 스킵
                    while i < n and text[i] in (" ", "\t", "\n", "\r"):
                        i += 1
                    continue

            # OR 감지
            if tu[i: i + 2] == "OR":
                pre_ok = (i == 0) or not (text[i - 1].isalnum() or text[i - 1] == "_")
                suf_idx = i + 2
                suf_ok = (suf_idx >= n) or not (text[suf_idx].isalnum() or text[suf_idx] == "_")
                if pre_ok and suf_ok:
                    part = "".join(buf).strip()
                    if part:
                        results.append((connector, part))
                    buf = []
                    connector = "OR"
                    i = suf_idx
                    while i < n and text[i] in (" ", "\t", "\n", "\r"):
                        i += 1
                    continue

        buf.append(ch)
        i += 1

    part = "".join(buf).strip()
    if part:
        results.append((connector, part))
    return results


# ─────────────────────────────────────────────────────────────
# 콤마 분리
# ─────────────────────────────────────────────────────────────
def split_by_comma(text: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    in_str = False
    str_char = ""

    for ch in text:
        if in_str:
            buf.append(ch)
            if ch == str_char:
                in_str = False
            continue
        if ch in ("'", '"'):
            in_str = True
            str_char = ch
            buf.append(ch)
            continue
        if ch == "(":
            depth += 1
            buf.append(ch)
            continue
        if ch == ")":
            if depth > 0:
                depth -= 1
            buf.append(ch)
            continue
        if ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)

    if buf:
        parts.append("".join(buf))
    return [p for p in parts if p.strip()]


# ─────────────────────────────────────────────────────────────
# 세미콜론 분리
# ─────────────────────────────────────────────────────────────
def split_by_semicolon(sql: str) -> list[str]:
    stmts: list[str] = []
    buf: list[str] = []
    depth = 0
    in_str = False
    str_char = ""

    for ch in sql:
        if in_str:
            buf.append(ch)
            if ch == str_char:
                in_str = False
            continue
        if ch in ("'", '"'):
            in_str = True
            str_char = ch
            buf.append(ch)
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            if depth > 0:
                depth -= 1
        if ch == ";" and depth == 0:
            s = "".join(buf).strip()
            if s:
                stmts.append(s)
            buf = []
        else:
            buf.append(ch)

    s = "".join(buf).strip()
    if s:
        stmts.append(s)
    return stmts


# ─────────────────────────────────────────────────────────────
# 서브쿼리 괄호 탐색
# ─────────────────────────────────────────────────────────────
def find_subquery_paren(expr: str) -> int | None:
    """SELECT 서브쿼리를 감싸는 최초 '(' 위치 반환."""
    n = len(expr)
    i = 0
    while i < n:
        if expr[i] == "(":
            end = find_matching_paren(expr, i)
            if end is not None:
                inner = expr[i + 1: end].strip()
                if re.match(r"^SELECT\b", inner, re.IGNORECASE):
                    return i
            # '('를 찾았지만 SELECT 서브쿼리가 아니면 다음으로
            i += 1
        else:
            i += 1
    return None


def find_matching_paren(s: str, start: int) -> int | None:
    if start >= len(s) or s[start] != "(":
        return None
    depth = 0
    in_str = False
    str_char = ""
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if ch == str_char:
                in_str = False
            continue
        if ch in ("'", '"'):
            in_str = True
            str_char = ch
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i
    return None


def find_kw_top(text: str, keyword: str) -> int:
    """depth=0에서 키워드의 시작 위치 반환. 없으면 -1."""
    kw = keyword.upper()
    tu = text.upper()
    n = len(text)
    depth = 0
    in_str = False
    str_char = ""
    i = 0
    while i < n:
        ch = text[i]
        if in_str:
            if ch == str_char:
                in_str = False
            i += 1
            continue
        if ch in ("'", '"'):
            in_str = True
            str_char = ch
            i += 1
            continue
        if ch == "(":
            depth += 1
            i += 1
            continue
        if ch == ")":
            if depth > 0:
                depth -= 1
            i += 1
            continue
        if depth == 0 and tu[i: i + len(kw)] == kw:
            return i
        i += 1
    return -1
