# KoreanEFLPhrasalVerbAnalyzer
A tool for analyzing phrasal verbs in Korean English textbooks: Upload PDFs (single, multiple, or ZIP folder) in Colab, convert to refined TXT, parse with Stanza for verb frequency counts, and export results as Excel and TXT files.

한국 영어 교과서 PDF → 구동사 빈도 분석 도구

## 한 줄로 실행하기 (Colab)
```python
# 1. GitHub에서 클론
!git clone https://github.com/당신의아이디/KoreanEFLPhrasalVerbAnalyzer.git
%cd KoreanEFLPhrasalVerbAnalyzer

# 2. 한 줄 실행 (PDF 업로드 창 바로 뜸)
analyze_phrasal_verbs()
