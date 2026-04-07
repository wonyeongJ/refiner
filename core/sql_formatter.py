"""
SQL Formatter - Custom Convention
"""
import re

TAB = "\t"

def _ki(depth: int) -> str:
    return TAB * depth

def _ci(depth: int) -> str:
    return TAB * (depth + 1)

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

def render_clause(name: str, content: str, depth: int, lines: list) -> None:
    ki = _ki(depth)
    ci = _ci(depth)

    if name == "SELECT":
        lines.append(f"{ki}SELECT")
        cols = split_by_comma(content)
        for idx, col in enumerate(cols):
            col = col.strip()
            comma = "," if idx < len(cols) - 1 else ""
            
            # DISTINCT 예외 처리
            col_up = col.upper()
            if col_up.startswith("DISTINCT "):
                fmt = "distinct " + format_expr(col[9:].strip(), depth)
            else:
                fmt = format_expr(col, depth)
                
            lines.append(f"{ci}{fmt}{comma}")

    elif name == "FROM":
        lines.append(f"{ki}FROM")
        tables = split_by_comma(content)
        for tbl in tables:
            lines.append(f"{ci}{format_expr(tbl.strip(), depth)}")

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
        for idx, item in enumerate(items):
            comma = "," if idx < len(items) - 1 else ""
            lines.append(f"{ci}{format_expr(item.strip(), depth)}{comma}")

    elif name in ("UNION", "UNION ALL", "INTERSECT", "EXCEPT"):
        lines.append(f"{ki}{name}")
        lines.append(format_sql(content, depth))

    elif "JOIN" in name:
        on_pos = find_kw_top(content, "ON")
        if on_pos >= 0:
            tbl_part = content[:on_pos].strip()
            tbl_formatted = format_expr(tbl_part, depth)
            cond_part = content[on_pos+2:].strip()
            cond_formatted = format_expr(cond_part, depth)
            lines.append(f"{ci}{name} {tbl_formatted}")
            lines.append(f"{ci}\t{upper_kw('ON')} {cond_formatted}")
        else:
            lines.append(f"{ci}{name} {format_expr(content, depth)}")

    else:
        lines.append(f"{ki}{name}")
        if content:
            lines.append(f"{ci}{format_expr(content, depth)}")

def format_operators(text: str) -> str:
    # =, !=, <=, >=, <> 연산자 주변에 항상 1칸 공백 보장 (예: a=b -> a = b)
    return re.sub(r'\s*(<>|!=|<=|>=|=)\s*', r' \1 ', text)

def format_expr(expr: str, depth: int) -> str:
    paren_pos = find_subquery_paren(expr)
    if paren_pos is None:
        return format_operators(upper_kw(expr))

    paren_end = find_matching_paren(expr, paren_pos)
    if paren_end is None:
        return format_operators(upper_kw(expr))

    before = format_operators(upper_kw(expr[:paren_pos]).strip())
    inner = expr[paren_pos + 1: paren_end].strip()
    after = format_operators(upper_kw(expr[paren_end + 1:]).strip())

    sub_depth = depth + 1

    sub_formatted = format_sql(inner, depth=sub_depth)
    
    result = ""
    if before:
        result += f"{before} (\n"
    else:
        result += "(\n"
        
    result += f"{sub_formatted}\n{_ki(sub_depth)})"
    
    if after:
        result += f" {after}"
        
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
    su = sql.upper()
    n = len(sql)
    positions: list[tuple[int, str]] = []

    depth = 0
    in_str = False
    str_char = ""
    i = 0

    while i < n:
        ch = sql[i]
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

        if depth == 0:
            matched_clause = ""
            for clause in _CLAUSES:
                cl = len(clause)
                if su[i: i + cl] == clause:
                    if i > 0 and (sql[i - 1].isalnum() or sql[i - 1] == "_"):
                        continue
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

    result: list[tuple[str, str]] = []
    for idx, (pos, name) in enumerate(positions):
        content_start = pos + len(name)
        content_end = positions[idx + 1][0] if idx + 1 < len(positions) else n
        content = sql[content_start:content_end].strip()
        result.append((name, content))
    return result

def split_conditions(text: str) -> list[tuple[str, str]]:
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
                    while i < n and text[i] in (" ", "\t", "\n", "\r"):
                        i += 1
                    continue

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

def find_subquery_paren(expr: str) -> int | None:
    n = len(expr)
    i = 0
    while i < n:
        if expr[i] == "(":
            end = find_matching_paren(expr, i)
            if end is not None:
                inner = expr[i + 1: end].strip()
                if re.match(r"^SELECT\b", inner, re.IGNORECASE):
                    return i
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
            # Check boundaries
            if i > 0 and (text[i-1].isalnum() or text[i-1] == "_"):
                i += 1
                continue
            end = i + len(kw)
            if end < n and (text[end].isalnum() or text[end] == "_"):
                i += 1
                continue
            return i
        i += 1
    return -1
