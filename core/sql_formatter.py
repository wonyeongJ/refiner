"""
SQL Formatter - Custom Convention
"""
import re

TAB = "\t"

def _ki(depth: int) -> str:
    return TAB * depth

def _ci(depth: int) -> str:
    return TAB * (depth + 1)

def _append_expr_with_prefix(lines: list[str], indent: str, prefix: str, expr: str) -> None:
    expr_lines = expr.splitlines() or [expr]
    lines.append(f"{indent}{prefix}{expr_lines[0]}")
    if len(expr_lines) > 1:
        lines.extend(expr_lines[1:])

def _append_block(lines: list[str], indent: str, expr: str, suffix: str = "") -> None:
    expr_lines = expr.splitlines() or [expr]
    if suffix:
        expr_lines[-1] = f"{expr_lines[-1]}{suffix}"
    lines.append(f"{indent}{expr_lines[0]}")
    if len(expr_lines) > 1:
        lines.extend(expr_lines[1:])

def _mask_sql_comments(text: str) -> str:
    chars = list(text)
    n = len(chars)
    i = 0
    in_str = False
    str_char = ""
    while i < n:
        ch = chars[i]
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
        if ch == "-" and i + 1 < n and chars[i + 1] == "-":
            chars[i] = " "
            chars[i + 1] = " "
            i += 2
            while i < n and chars[i] not in ("\n", "\r"):
                chars[i] = " "
                i += 1
            continue
        if ch == "/" and i + 1 < n and chars[i + 1] == "*":
            chars[i] = " "
            chars[i + 1] = " "
            i += 2
            while i + 1 < n and not (chars[i] == "*" and chars[i + 1] == "/"):
                if chars[i] not in ("\n", "\r"):
                    chars[i] = " "
                i += 1
            if i + 1 < n:
                chars[i] = " "
                chars[i + 1] = " "
                i += 2
            continue
        i += 1
    return "".join(chars)

def format_multiple_statements(raw_sql: str) -> str:
    if not raw_sql.strip():
        return ""
    stmts = split_by_semicolon(raw_sql)
    results = []
    for s in stmts:
        s = s.strip()
        if s and not is_comment_only_sql(s):
            results.append(format_sql(s, depth=0))
    return "\n\n".join(results)

def format_sql(raw_sql: str, depth: int = 0) -> str:
    sql = raw_sql.strip()
    if sql.endswith(";"):
        sql = sql[:-1].strip()
    if not sql:
        return ""

    leading = sql.lstrip().upper()
    if leading.startswith("INSERT"):
        result = format_insert_sql(sql, depth)
        if depth == 0:
            result += "\n;"
        return result
    if leading.startswith("UPDATE"):
        result = format_update_sql(sql, depth)
        if depth == 0:
            result += "\n;"
        return result
    if leading.startswith("DELETE"):
        result = format_delete_sql(sql, depth)
        if depth == 0:
            result += "\n;"
        return result

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
            
            # DISTINCT 컬럼은 DISTINCT 키워드를 유지한 채 표현식만 재정렬
            col_up = col.upper()
            if col_up.startswith("DISTINCT "):
                fmt = "DISTINCT " + format_expr(col[9:].strip(), depth)
            else:
                fmt = format_expr(col, depth)

            prefix = "" if idx == 0 else ", "
            _append_expr_with_prefix(lines, ci, prefix, fmt)

    elif name == "FROM":
        lines.append(f"{ki}FROM")
        tables = split_by_comma(content)
        for idx, tbl in enumerate(tables):
            prefix = "" if idx == 0 else ", "
            _append_expr_with_prefix(lines, ci, prefix, format_expr(tbl.strip(), depth))

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
            prefix = "" if idx == 0 else ", "
            _append_expr_with_prefix(lines, ci, prefix, format_expr(item.strip(), depth))

    elif name in ("UNION", "UNION ALL", "INTERSECT", "EXCEPT"):
        if lines and lines[-1] != "":
            lines.append("")
        lines.append(f"{ki}{name}")
        lines.append("")
        if content:
            lines.append(format_sql(content, depth))

    elif "JOIN" in name:
        on_pos = find_kw_top(content, "ON")
        ji = _ki(depth + 2)
        oi = _ki(depth + 3)
        if on_pos >= 0:
            tbl_part = content[:on_pos].strip()
            tbl_formatted = format_expr(tbl_part, depth + 1)
            cond_part = content[on_pos+2:].strip()
            cond_formatted = format_expr(cond_part, depth + 1)
            
            if tbl_formatted.startswith("(\n"):
                lines.append(f"{ji}{name}")
                tbl_lines = tbl_formatted.splitlines()
                lines.append(f"{ji}(")
                lines.extend(tbl_lines[1:])
            else:
                _append_expr_with_prefix(lines, ji, f"{name} ", tbl_formatted)
                
            _append_expr_with_prefix(lines, oi, f"{upper_kw('ON')} ", cond_formatted)
        else:
            tbl_formatted = format_expr(content, depth + 1)
            if tbl_formatted.startswith("(\n"):
                lines.append(f"{ji}{name}")
                tbl_lines = tbl_formatted.splitlines()
                lines.append(f"{ji}(")
                lines.extend(tbl_lines[1:])
            else:
                _append_expr_with_prefix(lines, ji, f"{name} ", tbl_formatted)

    else:
        lines.append(f"{ki}{name}")
        if content:
            lines.append(f"{ci}{format_expr(content, depth)}")

def format_operators(text: str) -> str:
    # =, !=, <=, >=, <> 연산자 주변 공백을 1칸으로 정규화 (예: a=b -> a = b)
    return re.sub(r'\s*(<>|!=|<=|>=|=)\s*', r' \1 ', text)

def _split_head_parenthesized(text: str) -> tuple[str, str] | None:
    stripped = text.strip()
    p0 = stripped.find("(")
    if p0 < 0:
        return None
    p1 = find_matching_paren(stripped, p0)
    if p1 is None:
        return None
    head = stripped[:p0].strip()
    inner = stripped[p0 + 1:p1].strip()
    tail = stripped[p1 + 1:].strip()
    if tail:
        return None
    return head, inner

def _fmt_plain_expr(text: str) -> str:
    txt = text.strip()
    if not txt:
        return ""
    if txt.startswith("<") and txt.endswith(">"):
        return txt
    return format_operators(upper_kw(txt))

def _split_assignment_top(text: str) -> tuple[str, str] | None:
    s = text.strip()
    depth = 0
    in_str = False
    str_char = ""
    n = len(s)
    i = 0
    while i < n:
        ch = s[i]
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
        if ch == "=" and depth == 0:
            prev = s[i - 1] if i > 0 else ""
            nxt = s[i + 1] if i + 1 < n else ""
            if prev in ("<", ">", "!", "=") or nxt == "=":
                i += 1
                continue
            left = s[:i].strip()
            right = s[i + 1:].strip()
            if left and right:
                return left, right
        i += 1
    return None

def _format_set_item(item: str, depth: int) -> str:
    txt = item.strip()
    if txt.startswith("<") and txt.endswith(">"):
        return txt
    pair = _split_assignment_top(txt)
    if pair is None:
        return _fmt_plain_expr(txt)
    left, right = pair
    rhs = format_expr(right, depth)
    rhs_lines = rhs.splitlines() or [rhs]
    result = f"{_fmt_plain_expr(left)} = {rhs_lines[0]}"
    if len(rhs_lines) > 1:
        result += "\n" + "\n".join(rhs_lines[1:])
    return result

def format_insert_sql(sql: str, depth: int) -> str:
    ki = _ki(depth)
    ci = _ci(depth)

    into_pos = find_kw_top(sql, "INTO")
    values_pos = find_kw_top(sql, "VALUES")
    if into_pos < 0 or values_pos < 0 or values_pos <= into_pos:
        return _fmt_plain_expr(sql)

    table_and_cols = sql[into_pos + len("INTO"):values_pos].strip()
    values_part = sql[values_pos + len("VALUES"):].strip()

    tc = _split_head_parenthesized(table_and_cols)
    vv = _split_head_parenthesized(values_part)
    if tc is None or vv is None:
        return _fmt_plain_expr(sql)

    table_name, cols_raw = tc
    _, vals_raw = vv

    cols = split_by_comma(cols_raw)
    vals = split_by_comma(vals_raw)

    lines: list[str] = []
    lines.append(f"{ki}INSERT INTO {_fmt_plain_expr(table_name)}")
    lines.append(f"{ci}(")
    for idx, col in enumerate(cols):
        suffix = "," if idx < len(cols) - 1 else ""
        lines.append(f"{ci}{_fmt_plain_expr(col)}{suffix}")
    lines.append(f"{ci})")
    lines.append(f"{ki}VALUES")
    lines.append(f"{ci}(")
    for idx, val in enumerate(vals):
        suffix = "," if idx < len(vals) - 1 else ""
        _append_block(lines, ci, format_expr(val.strip(), depth), suffix)
    lines.append(f"{ci})")
    return "\n".join(lines)

def format_update_sql(sql: str, depth: int) -> str:
    ki = _ki(depth)
    ci = _ci(depth)

    set_pos = find_kw_top(sql, "SET")
    if set_pos < 0:
        return _fmt_plain_expr(sql)
    where_pos = find_kw_top(sql, "WHERE")

    table_part = sql[len("UPDATE"):set_pos].strip()
    if where_pos >= 0:
        set_part = sql[set_pos + len("SET"):where_pos].strip()
        where_part = sql[where_pos + len("WHERE"):].strip()
    else:
        set_part = sql[set_pos + len("SET"):].strip()
        where_part = ""

    sets = split_by_comma(set_part)

    lines: list[str] = []
    lines.append(f"{ki}UPDATE")
    lines.append(f"{ci}{_fmt_plain_expr(table_part)}")
    lines.append(f"{ki}SET")
    for idx, item in enumerate(sets):
        suffix = "," if idx < len(sets) - 1 else ""
        _append_block(lines, ci, _format_set_item(item, depth), suffix)

    if where_part:
        lines.append(f"{ki}WHERE")
        conds = split_conditions(where_part)
        for connector, cond in conds:
            prefix = f"{connector} " if connector else ""
            lines.append(f"{ci}{prefix}{format_expr(cond.strip(), depth)}")

    return "\n".join(lines)

def format_delete_sql(sql: str, depth: int) -> str:
    ki = _ki(depth)
    ci = _ci(depth)

    from_pos = find_kw_top(sql, "FROM")
    if from_pos < 0:
        return _fmt_plain_expr(sql)
    where_pos = find_kw_top(sql, "WHERE")

    if where_pos >= 0:
        table_part = sql[from_pos + len("FROM"):where_pos].strip()
        where_part = sql[where_pos + len("WHERE"):].strip()
    else:
        table_part = sql[from_pos + len("FROM"):].strip()
        where_part = ""

    lines: list[str] = []
    lines.append(f"{ki}DELETE FROM")
    lines.append(f"{ci}{_fmt_plain_expr(table_part)}")

    if where_part:
        lines.append(f"{ki}WHERE")
        conds = split_conditions(where_part)
        for connector, cond in conds:
            prefix = f"{connector} " if connector else ""
            lines.append(f"{ci}{prefix}{format_expr(cond.strip(), depth)}")

    return "\n".join(lines)

def normalize_whitespace(text: str) -> str:
    n = len(text)
    in_str = False
    str_char = ""
    result = []
    i = 0
    while i < n:
        ch = text[i]
        if in_str:
            result.append(ch)
            if ch == "\\" and i + 1 < n:
                result.append(text[i + 1])
                i += 2
                continue
            if ch == str_char:
                in_str = False
            i += 1
            continue
        if ch in ("'", '"'):
            in_str = True
            str_char = ch
            result.append(ch)
            i += 1
            continue
        if ch.isspace():
            if result and not result[-1].isspace():
                result.append(" ")
            i += 1
            continue
        result.append(ch)
        i += 1
    return "".join(result).strip()

def find_case_blocks(text: str) -> list[tuple[int, int]]:
    n = len(text)
    masked = _mask_sql_comments(text)
    tu = masked.upper()
    
    positions = []
    in_str = False
    str_char = ""
    paren_depth = 0
    case_depth = 0
    case_starts = []
    
    i = 0
    while i < n:
        ch = masked[i]
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
            paren_depth += 1
            i += 1
            continue
        if ch == ")":
            if paren_depth > 0:
                paren_depth -= 1
            i += 1
            continue
            
        def is_kw(kw: str, index: int) -> bool:
            if tu[index: index + len(kw)] != kw:
                return False
            if index > 0 and (masked[index - 1].isalnum() or masked[index - 1] == "_"):
                return False
            end = index + len(kw)
            if end < n and (masked[end].isalnum() or masked[end] == "_"):
                return False
            return True
            
        if paren_depth == 0:
            if is_kw("CASE", i):
                if case_depth == 0:
                    case_starts.append(i)
                case_depth += 1
                i += 4
                continue
            elif is_kw("END", i):
                if case_depth > 0:
                    case_depth -= 1
                    if case_depth == 0:
                        start = case_starts.pop()
                        positions.append((start, i + 3))
                i += 3
                continue
        i += 1
    return positions

def split_case_parts(case_text: str) -> dict:
    masked = _mask_sql_comments(case_text)
    tu = masked.upper()
    n = len(case_text)
    
    in_str = False
    str_char = ""
    paren_depth = 0
    case_depth = 0
    keywords = []
    
    i = 4 # Skip "CASE"
    while i < n - 3:
        ch = masked[i]
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
            paren_depth += 1
            i += 1
            continue
        if ch == ")":
            if paren_depth > 0:
                paren_depth -= 1
            i += 1
            continue
            
        def is_kw(kw: str, index: int) -> bool:
            if tu[index: index + len(kw)] != kw:
                return False
            if index > 0 and (masked[index - 1].isalnum() or masked[index - 1] == "_"):
                return False
            end = index + len(kw)
            if end < n and (masked[end].isalnum() or masked[end] == "_"):
                return False
            return True

        if paren_depth == 0:
            if is_kw("CASE", i):
                case_depth += 1
                i += 4
                continue
            elif is_kw("END", i):
                if case_depth > 0:
                    case_depth -= 1
                i += 3
                continue
                
            if case_depth == 0:
                if is_kw("WHEN", i):
                    keywords.append(("WHEN", i))
                    i += 4
                    continue
                elif is_kw("THEN", i):
                    keywords.append(("THEN", i))
                    i += 4
                    continue
                elif is_kw("ELSE", i):
                    keywords.append(("ELSE", i))
                    i += 4
                    continue
        i += 1
        
    parts = {
        "base": "",
        "whens": [],
        "else": ""
    }
    
    if not keywords:
        return parts
        
    first_kw, first_idx = keywords[0]
    if first_kw == "WHEN":
        parts["base"] = case_text[4:first_idx].strip()
        
    current_when = None
    for idx, (kw, pos) in enumerate(keywords):
        next_pos = keywords[idx + 1][1] if idx + 1 < len(keywords) else n - 3
        content = case_text[pos + len(kw): next_pos].strip()
        
        if kw == "WHEN":
            current_when = {"when": content, "then": ""}
        elif kw == "THEN":
            if current_when is not None:
                current_when["then"] = content
                parts["whens"].append(current_when)
                current_when = None
        elif kw == "ELSE":
            parts["else"] = content
            
    return parts

def format_single_case(case_text: str, depth: int) -> str:
    parts = split_case_parts(case_text)
    d = depth + 1
    base_indent = _ki(d)
    
    # CASE starts at base_indent + ", " which is exactly 2 characters.
    # To align END perfectly under the 'C' in 'CASE', we use exactly 2 spaces after base_indent.
    end_indent = base_indent + "  "
    # To indent WHEN/ELSE by exactly 4 spaces (1 full tab level) relative to CASE/END, we use exactly 2 + 4 = 6 spaces.
    when_indent = base_indent + "      "
    
    lines = []
    if parts["base"]:
        base_fmt = format_expr(parts["base"], d)
        lines.append(f"CASE {base_fmt}")
    else:
        lines.append("CASE")
        
    for w in parts["whens"]:
        when_cond = format_expr(w["when"], d)
        then_expr = format_expr(w["then"], d)
        lines.append(f"{when_indent}WHEN {when_cond} THEN {then_expr}")
        
    if parts["else"]:
        else_expr = format_expr(parts["else"], d)
        lines.append(f"{when_indent}ELSE {else_expr}")
        
    lines.append(f"{end_indent}END")
    return "\n".join(lines)

def format_all_cases_in_expr(expr: str, depth: int) -> str:
    blocks = find_case_blocks(expr)
    if not blocks:
        return expr
    result = expr
    for start, end in reversed(blocks):
        case_text = expr[start:end]
        formatted = format_single_case(case_text, depth)
        result = result[:start] + formatted + result[end:]
    return result

def format_expr(expr: str, depth: int) -> str:
    expr_strip = expr.strip()
    if expr_strip.startswith("<") and expr_strip.endswith(">"):
        return expr_strip

    paren_pos = find_subquery_paren(expr)
    if paren_pos is None:
        normalized = normalize_whitespace(expr_strip)
        expr_with_cases = format_all_cases_in_expr(normalized, depth)
        return format_operators(upper_kw(expr_with_cases))

    paren_end = find_matching_paren(expr, paren_pos)
    if paren_end is None:
        normalized = normalize_whitespace(expr_strip)
        expr_with_cases = format_all_cases_in_expr(normalized, depth)
        return format_operators(upper_kw(expr_with_cases))

    before_norm = normalize_whitespace(expr[:paren_pos])
    before = format_operators(upper_kw(format_all_cases_in_expr(before_norm, depth)))
    
    inner = expr[paren_pos + 1: paren_end].strip()
    
    after_norm = normalize_whitespace(expr[paren_end + 1:])
    after = format_operators(upper_kw(format_all_cases_in_expr(after_norm, depth)))

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

def _match_clause_at(text_upper: str, start: int, clause: str) -> int | None:
    """Match SQL clause allowing one-or-more spaces between words."""
    n = len(text_upper)
    words = clause.split(" ")
    i = start

    for idx, w in enumerate(words):
        wlen = len(w)
        if text_upper[i:i + wlen] != w:
            return None
        i += wlen

        if idx < len(words) - 1:
            if i >= n or text_upper[i] not in (" ", "\t", "\n", "\r"):
                return None
            while i < n and text_upper[i] in (" ", "\t", "\n", "\r"):
                i += 1

    return i

def extract_clauses(sql: str) -> list[tuple[str, str]]:
    masked = _mask_sql_comments(sql)
    su = masked.upper()
    n = len(sql)
    positions: list[tuple[int, str, int]] = []

    depth = 0
    in_str = False
    str_char = ""
    i = 0

    while i < n:
        ch = masked[i]
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
            matched_end = -1
            for clause in _CLAUSES:
                end_pos = _match_clause_at(su, i, clause)
                if end_pos is None:
                    continue
                if i > 0 and (masked[i - 1].isalnum() or masked[i - 1] == "_"):
                    continue
                if end_pos < n and (masked[end_pos].isalnum() or masked[end_pos] == "_"):
                    continue
                matched_clause = clause
                matched_end = end_pos
                break

            if matched_clause:
                positions.append((i, matched_clause, matched_end))
                i = matched_end
                continue

        i += 1

    result: list[tuple[str, str]] = []
    for idx, (pos, name, end_pos) in enumerate(positions):
        content_start = end_pos
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
    masked = _mask_sql_comments(text)
    tu = masked.upper()
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]
        mch = masked[i]
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
                pre_ok = (i == 0) or not (masked[i - 1].isalnum() or masked[i - 1] == "_")
                suf_idx = i + 3
                suf_ok = (suf_idx >= n) or not (masked[suf_idx].isalnum() or masked[suf_idx] == "_")
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
                pre_ok = (i == 0) or not (masked[i - 1].isalnum() or masked[i - 1] == "_")
                suf_idx = i + 2
                suf_ok = (suf_idx >= n) or not (masked[suf_idx].isalnum() or masked[suf_idx] == "_")
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

        buf.append(ch if mch != " " else text[i])
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

def is_comment_only_sql(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    without_block = re.sub(r"/\*.*?\*/", "", stripped, flags=re.DOTALL)
    without_line = re.sub(r"--[^\n\r]*", "", without_block)
    return not without_line.strip()

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
    masked = _mask_sql_comments(text)
    tu = masked.upper()
    n = len(text)
    depth = 0
    in_str = False
    str_char = ""
    i = 0
    while i < n:
        ch = masked[i]
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
            if i > 0 and (masked[i-1].isalnum() or masked[i-1] == "_"):
                i += 1
                continue
            end = i + len(kw)
            if end < n and (masked[end].isalnum() or masked[end] == "_"):
                i += 1
                continue
            return i
        i += 1
    return -1

