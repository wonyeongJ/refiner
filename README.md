# Refiner

> 개발자를 위한 SQL & JSON 정제 및 Java VO 자동 생성 유틸리티

**Refiner**는 반복되는 SQL 포맷팅, DDL 기반의 Java VO 작성, 가독성 낮은 JSON 데이터를 한눈에 보기 좋게 정리해주는 개발자 전용 도구입니다.

---

## ✨ 주요 기능 (User Features)

### 1. SQL 정제 (SQL Formatter)
- 한 줄로 늘어진 복잡한 쿼리를 표준 관례에 맞춰 탭 들여쓰기 기반으로 정렬합니다.
- `SELECT`, `FROM`, `WHERE` 등 주요 키워드 줄바꿈 및 서브쿼리 재귀적 들여쓰기를 지원합니다.
- SQL 구문 강조(Syntax Highlighting)를 통해 가독성을 극대화합니다.

### 2. Java VO 자동 생성 (Java VO Generator)
- `CREATE TABLE` 문을 분석하여 자동으로 Lombok `@Data` 기반의 Java 클래스를 생성합니다.
- **Oracle → Java 타입 자동 매핑**: NUMBER, VARCHAR2, DATE 등 주요 타입을 적절한 Java 타입으로 변환합니다.
- **Javadoc 연동**: `COMMENT ON COLUMN` 구문이 포함된 경우, 해당 주석을 Java 필드의 Javadoc으로 자동 삽입합니다.

### 3. JSON 포매터 (JSON Formatter)
- 압축된 JSON 데이터를 4칸 들여쓰기의 보기 좋은 구조로 변환합니다.
- JSON Key, String, Number, Boolean 등 요소별 전용 색상 테마를 적용합니다.

---

## 🛠 기술 스택 (Developer Details)

- **Language**: Python 3.12+
- **GUI Framework**: PyQt6
- **Libraries**:
    - `sqlparse`: SQL 토큰 분석 및 초기 파싱
    - `pyperclip`: 클립보드 연동
    - `re`: 정규표현식을 활용한 커스텀 파싱 및 구문 강조
- **Icons**: ⚙ (Gears) Custom Icon

---

## 📁 프로젝트 구조

```text
refiner/
├── main.py                 # 앱 초기화 및 GUI 배치 (PyQt6)
├── requirements.txt        # 의존성 패키지 목록
├── core/                   # 핵심 변환 로직 모듈
│   ├── sql_formatter.py    # SQL 정렬 및 인덴트 처리
│   ├── java_vo_generator.py# DDL 분석 및 VO 문자열 생성
│   └── json_formatter.py   # JSON 구조화 및 예외 처리
├── ui/                     # UI 스타일 및 하이라이팅
│   ├── theme.py            # 다크 테마 색상 및 CSS 스타일시트
│   └── highlighters.py     # 언어별 QSyntaxHighlighter 구현
├── assets/                 # 리소스 파일
│   └── images/
│       └── icon.ico        # 앱 아이콘 (256px)
├── scripts/                # 관리용 스크립트
│   └── build.bat           # PyInstaller 빌드 실행 파일
└── README.md
```

---

## 🚀 사용자 가이드

### ⌨️ 단축키 (Shortcuts)

| 기능 | 단축키 | 설명 |
|--------|------|------|
| **SQL 정렬** | `Ctrl + Enter` | 입력된 SQL을 보기 좋게 정렬 |
| **Java VO 변환** | `Ctrl + Shift + Enter` | DDL을 Java 클래스로 변환 |
| **JSON 정렬** | `Alt + J` | JSON 데이터를 들여쓰기 정렬 |
| **결과 복사** | `Ctrl + Shift + C` | 출력창 내용을 클립보드로 복사 |
| **입력 초기화** | `Ctrl + Delete` | 입력창 및 출력창 모두 비우기 |

---

## 💻 개발자 가이드 (Build & Run)

### 1. 환경 설정 및 실행
```bash
# 가상환경 생성 및 활성화
python -m venv venv
.\venv\Scripts\activate

# 의존성 패키지 설치
pip install -r requirements.txt

# 프로그램 실행
python main.py
```

### 2. 실행 파일(EXE) 생성
`scripts\build.bat`를 실행하면 원클릭으로 빌드가 완료됩니다.
- 빌드 결과물: `dist\Refiner.exe` (모든 데이터와 아이콘이 포함된 단일 파일)

---

## 🗺️ Oracle → Java 타입 매핑 가이드

| Oracle 타입 | Java 타입 |
|------------|-----------|
| `VARCHAR2`, `CHAR`, `CLOB` | `String` |
| `NUMBER(p, 0)` p<=9 | `Integer` |
| `NUMBER(p, 0)` p<=18 | `Long` |
| `NUMBER` (p, s) | `BigDecimal` |
| `DATE`, `TIMESTAMP` | `LocalDateTime` |
| `BLOB`, `RAW` | `byte[]` |
