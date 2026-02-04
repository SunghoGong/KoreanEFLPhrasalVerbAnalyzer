import os
import glob
import fitz  # PyMuPDF
import spacy
import re
import copy
from wtpsplit import SaT
import torch

def extract_text_from_pdfs(input_folder, output_raw_txt="merged_raw.txt"):
    """폴더 내의 모든 PDF를 읽어 텍스트 파일 하나로 병합"""
    print(f"📂 PDF 추출 시작: {input_folder}")
    
    # PDF 파일 리스트 확보
    pdf_files = glob.glob(os.path.join(input_folder, '**', '*.pdf'), recursive=True)
    if not pdf_files:
        print("❌ 처리할 PDF 파일이 없습니다.")
        return None

    # spaCy 로드 (문장 단위 1차 분리용)
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        from spacy.cli import download
        download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
    
    # 파이프라인 최적화
    disable_list = ["ner", "tagger", "attribute_ruler", "lemmatizer"]
    if "senter" in nlp.pipe_names: disable_list.append("parser")
    nlp.disable_pipes(disable_list)
    if "senter" not in nlp.pipe_names: nlp.add_pipe("senter")

    all_sentences = []

    for pdf_path in pdf_files:
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text = page.get_text()
                if not text: continue
                # spaCy로 1차 문장 분리 및 줄바꿈 처리
                spacy_doc = nlp(text)
                for sent in spacy_doc.sents:
                    clean_sent = sent.text.strip()
                    if clean_sent:
                        all_sentences.append(clean_sent)
            doc.close()
            print(f"  - 처리 완료: {os.path.basename(pdf_path)}")
        except Exception as e:
            print(f"  - 오류 발생 ({pdf_path}): {e}")

    # 병합된 텍스트 저장
    with open(output_raw_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(all_sentences))
    
    print(f"✅ 1차 병합 완료: {output_raw_txt} (총 {len(all_sentences)} 문장)")
    return output_raw_txt

def clean_text_logic(raw_text):
    """사용자의 정규식 로직을 적용하여 텍스트 정제"""
    # 1. 특수 문자 및 비영어권 문자 제거를 위한 패턴 식별
    # 원본 코드 로직: 한글/영어/숫자 등을 공백으로 치환 -> 남은건 특수문자/쓰레기값
    garbage_check = re.sub(r"[가-힣a-zA-Z0-9!?.\"]+", " ", raw_text)
    garbage_check = re.sub(r"[\s]", " ", garbage_check)
    garbage_list = list(set(garbage_check.split()))
    garbage_list.sort(key=len, reverse=True) # 긴 것부터 제거

    # 2. 텍스트 정제 시작
    text = copy.deepcopy(raw_text)
    
    # 기본적인 치환
    replacements = {
        "’": "'", "‘": "'", "“": '"', "”": '"',
        "á": "a", "ﬂ": "fl", "é": "e", "ﬁ": "fi",
        "è": "e", "É": "E", "ü": "u", "…": "..."
    }
    for k, v in replacements.items():
        text = text.replace(k, v)

    # 한글 제거
    text = re.sub(r'[가-힣]+', '', text)

    # 1번에서 식별한 Garbage 문자 제거
    for trash in garbage_list:
        if trash:
            text = text.replace(trash, " ")

    # 최종 공백 정리
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def refine_and_segment(input_txt_path, output_refined_txt="refined_text.txt"):
    """텍스트 정제 후 SaT 모델로 문장 분리"""
    print("🧹 텍스트 정제 및 SaT 문장 분리 시작...")
    
    with open(input_txt_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    # 정제 함수 호출
    cleaned_text = clean_text_logic(raw_text)

    # SaT 모델 로드
    sat = SaT("sat-12l-sm")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  - SaT 모델 로딩 중 (Device: {device})")
    if device == "cuda":
        sat.half().to(device)
    
    # 문장 분리
    seg_list = sat.split(cleaned_text)
    
    # 최종 리스트 다듬기
    final_sentences = []
    for seg in seg_list:
        seg = re.sub(r'\s+', ' ', seg).strip()
        if seg:
            final_sentences.append(seg)

    # 파일 저장 (한 줄에 한 문장)
    with open(output_refined_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(final_sentences))

    print(f"✨ 정제 및 분리 완료: {output_refined_txt} (총 {len(final_sentences)} 문장)")
    return final_sentences