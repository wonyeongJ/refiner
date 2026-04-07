"""
Java VO Generator Module
Parses CREATE TABLE SQL and generates Java @Data VO class.
Oracle/SQL -> Java type mapping based on official JDBC type mapping.
"""

import re
from typing import Optional


# ──────────────────────────────────────────────
# Oracle / SQL Standard → Java Type Mapping
# Based on Oracle JDBC Developer's Guide
# ──────────────────────────────────────────────
ORACLE_TO_JAVA: dict[str, str] = {
    # 문자열 타입
    "VARCHAR2": "String",
    "VARCHAR": "String",
    "CHAR": "String",
    "NCHAR": "String",
    "NVARCHAR2": "String",
    "NVARCHAR": "String",
    "LONG": "String",
    "CLOB": "String",
    "NCLOB": "String",
    "XMLTYPE": "String",

    # 숫자 타입
    "NUMBER": "int",
    "NUMERIC": "int",
    "DECIMAL": "int",
    "FLOAT": "Double",
    "BINARY_FLOAT": "Float",
    "BINARY_DOUBLE": "Double",
    "REAL": "Double",
    "INTEGER": "int",
    "INT": "int",
    "SMALLINT": "int",
    "TINYINT": "int",
    "BIGINT": "int",
    "DOUBLE": "Double",

    # 날짜/시간 타입 (String 지정)
    "DATE": "String",
    "TIMESTAMP": "String",
    "TIMESTAMP WITH TIME ZONE": "String",
    "TIMESTAMP WITH LOCAL TIME ZONE": "String",
    "INTERVAL YEAR TO MONTH": "String",
    "INTERVAL DAY TO SECOND": "String",

    # 이진 타입 (RAW는 String 처리)
    "BLOB": "byte[]",
    "RAW": "String",
    "LONG RAW": "byte[]",

    # 기타
    "BOOLEAN": "Boolean",
    "ROWID": "String",
    "UROWID": "String",
}

def _get_java_type(oracle_type: str, precision: Optional[int] = None, scale: Optional[int] = None, is_not_null: bool = False) -> str:
    """
    Oracle 타입 문자열을 Java 타입 문자열로 변환.
    """
    upper_type = oracle_type.strip().upper()

    # TIMESTAMP 계열의 접두사 매칭
    if upper_type.startswith("TIMESTAMP"):
        return "String"

    # 정수/숫자 타입 처리
    if upper_type in ("NUMBER", "NUMERIC", "DECIMAL", "INTEGER", "INT", "SMALLINT", "TINYINT", "BIGINT"):
        return "int" if is_not_null else "Integer"

    # 기본 매핑 테이블에서 가져오고, 없으면 Object 반환
    return ORACLE_TO_JAVA.get(upper_type, "Object")


def _get_required_imports(java_types: list[str]) -> list[str]:
    """사용된 Java 타입에 맞는 import 문 생성."""
    imports = set()
    for t in java_types:
        if t == "BigDecimal":
            imports.add("import java.math.BigDecimal;")
        elif t in ("LocalDateTime", "LocalDate", "LocalTime"):
            imports.add("import java.time.LocalDateTime;")
            imports.add("import java.time.LocalDate;")
        elif t == "OffsetDateTime":
            imports.add("import java.time.OffsetDateTime;")
        elif t == "Date":
            imports.add("import java.util.Date;")
    return sorted(imports)


def _snake_to_camel(snake_str: str, capitalize_first: bool = False) -> str:
    """
    snake_case → camelCase (or PascalCase)
    예: user_name → userName, USER_NAME → userName
    """
    parts = snake_str.lower().split("_")
    if not parts:
        return snake_str

    if capitalize_first:
        return "".join(p.capitalize() for p in parts if p)
    else:
        result = parts[0] + "".join(p.capitalize() for p in parts[1:] if p)
        return result


def _parse_column_def(col_def: str) -> Optional[dict]:
    """
    컬럼 정의 문자열 파싱.
    예: COLUMN_NAME VARCHAR2(100) NOT NULL
        AMOUNT NUMBER(15, 2) DEFAULT 0
    """
    col_def = col_def.strip()

    # 주석, 제약조건 제외
    skip_patterns = [
        r"^\s*--",
        r"^\s*CONSTRAINT\b",
        r"^\s*PRIMARY\s+KEY\b",
        r"^\s*FOREIGN\s+KEY\b",
        r"^\s*UNIQUE\b",
        r"^\s*CHECK\b",
        r"^\s*INDEX\b",
    ]
    for pat in skip_patterns:
        if re.match(pat, col_def, re.IGNORECASE):
            return None

    # 컬럼명 추출 (첫 토큰, 따옴표 제거)
    col_name_match = re.match(r'^\s*["`]?(\w+)["`]?\s+', col_def)
    if not col_name_match:
        return None
    col_name = col_name_match.group(1)

    # 나머지 부분에서 타입 추출
    rest = col_def[col_name_match.end():]

    # TIMESTAMP WITH TIME ZONE 같은 복합 타입 처리
    timestamp_tz_match = re.match(
        r"(TIMESTAMP\s+WITH\s+(?:LOCAL\s+)?TIME\s+ZONE)(?:\s*\(\s*\d+\s*\))?",
        rest, re.IGNORECASE
    )
    if timestamp_tz_match:
        oracle_type = timestamp_tz_match.group(1).upper()
        is_not_null = bool(re.search(r"NOT\s+NULL", rest, re.IGNORECASE))
        return {
            "col_name": col_name,
            "oracle_type": oracle_type,
            "precision": None,
            "scale": None,
            "is_not_null": is_not_null,
            "java_type": _get_java_type(oracle_type, is_not_null=is_not_null),
        }

    # 일반 타입(정밀도 포함) 추출
    type_match = re.match(
        r"(\w+)\s*(?:\(\s*(\d+)(?:\s*,\s*(\d+))?\s*\))?",
        rest, re.IGNORECASE
    )
    if not type_match:
        return None

    oracle_type = type_match.group(1).upper()
    precision = int(type_match.group(2)) if type_match.group(2) else None
    scale = int(type_match.group(3)) if type_match.group(3) else None
    is_not_null = bool(re.search(r"NOT\s+NULL", rest, re.IGNORECASE))

    java_type = _get_java_type(oracle_type, precision, scale, is_not_null)

    return {
        "col_name": col_name,
        "oracle_type": oracle_type,
        "precision": precision,
        "scale": scale,
        "is_not_null": is_not_null,
        "java_type": java_type,
    }


def parse_comments(sql: str) -> dict[str, str]:
    """
    COMMENT ON COLUMN table.column IS 'comment'; 구문에서 주석 파싱
    """
    comments = {}
    pattern = r"COMMENT\s+ON\s+COLUMN\s+(?:[\w\"`]+\.)*[\"`]?(\w+)[\"`]?\s+IS\s+'(.*?)'"
    for match in re.finditer(pattern, sql, re.IGNORECASE):
        col_name = match.group(1).upper()
        comment = match.group(2)
        comments[col_name] = comment
    return comments


def parse_create_table(sql: str) -> Optional[dict]:
    """
    CREATE TABLE 문에서 테이블명과 컬럼 정보를 파싱.
    여러 CREATE TABLE 이 있으면 첫 번째만 처리.
    """
    # 테이블명 추출 (스키마명에 쌍따옴표 포함된 경우 대응)
    create_match = re.search(
        r"CREATE\s+(?:OR\s+REPLACE\s+)?TABLE\s+(?:[\"`]?\w+[\"`]?\.)?[\"`]?(\w+)[\"`]?\s*\(",
        sql,
        re.IGNORECASE
    )
    if not create_match:
        return None

    table_name = create_match.group(1)

    # 괄호 쌍을 추적하여 정확한 컬럼 정의 블록만 추출
    start_pos = create_match.end() - 1  # '(' 위치
    depth = 0
    in_str = False
    str_char = ""
    end_pos = -1

    for i in range(start_pos, len(sql)):
        ch = sql[i]
        if in_str:
            if ch == str_char:
                in_str = False
            continue
        if ch in ("'", '"', '`'):
            in_str = True
            str_char = ch
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                end_pos = i
                break

    if end_pos == -1:
        return None

    columns_block = sql[start_pos + 1:end_pos]

    # 컬럼 정의 분리 (괄호 레벨 고려)
    col_defs = _split_column_defs(columns_block)

    columns = []
    for col_def in col_defs:
        parsed = _parse_column_def(col_def.strip())
        if parsed:
            columns.append(parsed)

    if not columns:
        return None

    return {
        "table_name": table_name,
        "columns": columns,
    }


def _split_column_defs(columns_block: str) -> list[str]:
    """괄호 중첩을 고려하여 컬럼 정의를 분리."""
    defs = []
    depth = 0
    current = []

    for char in columns_block:
        if char == "(":
            depth += 1
            current.append(char)
        elif char == ")":
            depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            defs.append("".join(current))
            current = []
        else:
            current.append(char)

    if current:
        defs.append("".join(current))

    return defs


def generate_java_vo(sql: str, package_name: str = "com.example.vo") -> str:
    """
    CREATE TABLE SQL에서 Java @Data VO 클래스 생성.
    """
    parsed = parse_create_table(sql)
    if not parsed:
        return "// ❌ CREATE TABLE 문을 찾을 수 없습니다.\n// 입력 SQL에 CREATE TABLE ... ( ... ) 형식의 구문이 포함되어야 합니다."

    table_name = parsed["table_name"]
    columns = parsed["columns"]
    
    # COLUMN 주석 파싱
    comments = parse_comments(sql)

    # 클래스명: PascalCase + Vo 접미사
    class_name = _snake_to_camel(table_name, capitalize_first=True) + "Vo"

    # 필요한 import 수집
    java_types = [col["java_type"] for col in columns]
    imports = _get_required_imports(java_types)

    # 코드 생성
    lines = []

    # 패키지 선언
    lines.append(f"package {package_name};")
    lines.append("")

    # 타입별 import
    if imports:
        lines.extend(imports)
        lines.append("")

    # 클래스 선언
    lines.append("/**")
    lines.append(f" * {table_name} 테이블 VO")
    lines.append(f" * Auto-generated by Refiner")
    lines.append(" */")
    lines.append(f"public class {class_name} {{")
    lines.append("")

    # 필드 생성
    for col in columns:
        field_name = _snake_to_camel(col["col_name"])
        java_type = col["java_type"]
        oracle_type_comment = col["oracle_type"]
        if col["precision"] is not None:
            oracle_type_comment += f"({col['precision']}"
            if col["scale"] is not None:
                oracle_type_comment += f", {col['scale']}"
            oracle_type_comment += ")"

        col_name_upper = col["col_name"].upper()
        comment_str = comments.get(col_name_upper, "")
        comment_display = f" - {comment_str}" if comment_str else ""

        lines.append(f"    /** {col['col_name']} ({oracle_type_comment}){comment_display} */")
        lines.append(f"    private {java_type} {field_name};")
        lines.append("")

    # Getter / Setter 생성
    for col in columns:
        field_name = _snake_to_camel(col["col_name"])
        # getter/setter Name => 첫 글자 대문자
        method_suffix = field_name[0].upper() + field_name[1:] if field_name else ""
        java_type = col["java_type"]

        # Getter
        lines.append(f"    public {java_type} get{method_suffix}() {{")
        lines.append(f"        return {field_name};")
        lines.append("    }")
        lines.append("")

        # Setter
        lines.append(f"    public void set{method_suffix}({java_type} {field_name}) {{")
        lines.append(f"        this.{field_name} = {field_name};")
        lines.append("    }")
        lines.append("")

    # 마지막 빈 줄 제거 후 클래스 닫기
    if lines[-1] == "":
        lines.pop()
    lines.append("}")

    return "\n".join(lines)
