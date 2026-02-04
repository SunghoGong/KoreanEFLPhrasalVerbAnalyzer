# KoreanEFLPhrasalVerbAnalyzer
A tool for analyzing phrasal verbs in Korean English textbooks: Upload PDFs (single, multiple, or ZIP folder) in Colab, convert to refined TXT, parse with Stanza for verb frequency counts, and export results as Excel and TXT files.

---

# 📘 Textbook Phrasal Verb Analyzer (교과서 구동사 분석기)

이 프로젝트는 **영어 교과서 PDF**를 입력받아 텍스트를 추출 및 정제하고, **특정 구동사(Phrasal Verbs)의 사용 빈도와 예문**을 분석하여 엑셀로 저장하는 도구입니다.

## 🚀 주요 기능

1. **PDF 텍스트 추출:** 여러 개의 PDF 파일에서 텍스트를 자동으로 추출합니다.
2. **텍스트 정제 & 문장 분리:** 불필요한 문자 제거 및 `SaT` 모델을 이용한 고성능 문장 분리를 수행합니다.
3. **구동사 분석:** `Stanza` NLP 모델을 활용하여 문맥에 맞는 구동사를 식별하고 카운팅합니다.
4. **결과 저장:** 구동사별 빈도수와 해당 예문들이 정리된 엑셀 파일을 생성합니다.

---

## ⚡ Google Colab에서 바로 실행하기 (추천)

복잡한 설치 과정 없이 Colab에서 바로 실행할 수 있습니다.

1. 아래 코드를 복사하여 Colab 코드 셀에 붙여넣으세요.
2. 실행 후 분석할 **PDF 파일들**을 업로드하면 자동으로 분석이 시작됩니다.

```python
# 1. 깃허브 코드 가져오기 & 환경 설정
!git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git  # 본인 주소로 변경!
%cd YOUR_REPO_NAME

print("📦 라이브러리 설치 중...")
!pip install -r requirements.txt
!python -m spacy download en_core_web_sm

# 2. PDF 파일 업로드
import os
from google.colab import files
import shutil

print("\n📂 분석할 PDF 파일들을 업로드하세요.")
uploaded = files.upload()

# PDF 폴더 정리
pdf_dir = "./user_pdfs"
if os.path.exists(pdf_dir): shutil.rmtree(pdf_dir)
os.makedirs(pdf_dir)

for filename in uploaded.keys():
    shutil.move(os.path.join("../", filename), os.path.join(pdf_dir, filename))

# 3. 분석 실행 (기본 내장된 엑셀 리스트 사용)
print("\n🔥 분석 시작...")
!python main.py --mode all --input_dir "$pdf_dir" --output_excel "result.xlsx"

# 4. 결과 다운로드
if os.path.exists("result.xlsx"):
    files.download("result.xlsx")

```

---

## 💻 로컬 환경에서 실행하기

### 1. 설치

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
pip install -r requirements.txt

```

### 2. 실행 방법

**PDF 파일들을 `pdfs` 폴더(사용자 생성)에 넣고 아래 명령어를 실행하세요.**

```bash
# 전체 과정 실행 (PDF 변환 -> 정제 -> 분석)
python main.py --mode all --input_dir ./pdfs --output_excel result.xlsx

```

**옵션별 실행:**

```bash
# 텍스트 정제만 수행 (결과: refined_text.txt)
python main.py --mode clean --input_dir ./pdfs

# 이미 정제된 텍스트로 분석만 수행
python main.py --mode analyze --output_txt refined_text.txt

```

---

## 📂 파일 구조

* `main.py`: 실행 메인 파일
* `utils.py`: PDF 처리 및 텍스트 정제 모듈
* `analyzer.py`: 구동사 분석 모듈
* `Phrasal Verb List Updating Project.xlsx`: 분석 기준이 되는 구동사 리스트 (기본 포함)
* `requirements.txt`: 필요 라이브러리 목록
