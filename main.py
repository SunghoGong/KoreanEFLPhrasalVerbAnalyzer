# 필요한 라이브러리 설치 (Colab에서 한 번 실행)
# !pip install pymupdf spacy wtpsplit stanza pandas tqdm torch
# !python -m spacy download en_core_web_sm
# !pip install pdf2image pytesseract  # OCR 필요 시
# !apt-get install -y unzip  # ZIP 해제용

import glob
import os
import fitz  # PyMuPDF
import spacy
import time
import re
import copy
from wtpsplit import SaT
import pandas as pd
import stanza
from collections import defaultdict
from tqdm import tqdm
import torch
import gc
from google.colab import files  # Colab 파일 업로드용
import subprocess  # ZIP 해제용

def analyze_phrasal_verbs(phrasal_verb_file="Phrasal Verb List Updating Project.xlsx",
                          output_excel='교과서count.xlsx',
                          output_txt='refined_text.txt'):
    """
    한국 영어 교과서 PDF를 업로드하고, 구동사 분석을 수행하는 함수.
    - phrasal_verb_file: 구동사 리스트 Excel 파일 경로 (개인 설정)
    - output_excel: 출력 Excel 파일 이름
    - output_txt: 정제된 TXT 파일 이름
    """

    # 1. PDF 파일 업로드 (사용자가 직접 업로드)
    print("PDF 파일을 업로드하세요. (하나의 PDF, 여러 PDF, 또는 ZIP 압축 폴더 가능)")
    uploaded = files.upload()

    # 업로드된 파일 처리
    pdf_files = []  # 최종 PDF 목록
    upload_folder = '/content/uploaded_pdfs/'  # 임시 폴더
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    for filename in uploaded.keys():
        file_path = os.path.join(upload_folder, filename)
        with open(file_path, 'wb') as f:
            f.write(uploaded[filename])
        
        if filename.endswith('.pdf'):
            pdf_files.append(file_path)
        elif filename.endswith('.zip'):
            print(f"ZIP 파일 해제 중: {filename}")
            unzip_command = f"unzip -o {file_path} -d {upload_folder}"
            subprocess.run(unzip_command, shell=True)
            extracted_pdfs = glob.glob(upload_folder + '**/*.pdf', recursive=True)
            pdf_files.extend(extracted_pdfs)

    file_list = pdf_files
    print("업로드된 PDF 파일 수:", len(file_list))

    # PDF 파일 이름만 추출 (확장자 제외)
    pure_names = []
    for f in file_list:
        name_without_ext = os.path.splitext(os.path.basename(f))[0]
        pure_names.append(name_without_ext)
    print("파일 이름 목록:", pure_names)

    # 2. PDF를 TXT로 변환하는 함수
    def save_pdf_to_text(pdf_filename, output_filename):
        print(f"PDF 파일 로딩 중: {pdf_filename}")
        start_time = time.time()

        nlp = spacy.load("en_core_web_sm")
        disable_list = ["ner", "tagger", "attribute_ruler", "lemmatizer"]
        if "senter" in nlp.pipe_names:
            disable_list.append("parser")
        nlp.disable_pipes(disable_list)
        if "senter" not in nlp.pipe_names and "parser" not in nlp.pipe_names:
            nlp.add_pipe("senter")

        print("NLP 설정 완료. 변환 시작...")

        doc = fitz.open(pdf_filename)
        sentence_count = 0

        with open(output_filename, "w", encoding="utf-8") as f:
            for page in doc:
                text = page.get_text()
                spacy_doc = nlp(text)
                for sent in spacy_doc.sents:
                    clean_sent = sent.text.strip()
                    if clean_sent:
                        f.write(clean_sent + "\n")
                        sentence_count += 1

        doc.close()
        end_time = time.time()
        print(f"저장 완료: {output_filename}")
        print(f"소요 시간: {end_time - start_time:.2f}초")
        print(f"저장된 문장 수: {sentence_count}개")

    # 각 PDF를 TXT로 변환
    for each in pure_names:
        input_pdf = next((f for f in file_list if os.path.basename(f).startswith(each)), None)
        if input_pdf:
            output_txt_single = each + '.txt'
            try:
                save_pdf_to_text(input_pdf, output_txt_single)
            except Exception as e:
                print(f"오류: {e}")

    # 3. TXT 파일들 합치기
    txt_files = glob.glob('/content/*.txt')
    print(f"TXT 파일 수: {len(txt_files)}")

    with open('merged_all.txt', 'w', encoding='utf-8') as outfile:
        for file_path in txt_files:
            with open(file_path, 'r', encoding='utf-8') as infile:
                content = infile.read()
                outfile.write(content)
                outfile.write('\n')

    # 4. 합친 텍스트 불러오기
    with open('merged_all.txt', 'r', encoding='utf-8') as file:
        allText = file.read()

    # 5. 텍스트 정제
    testtext = copy.deepcopy(allText)
    testtext = testtext.replace("’", "'")
    testtext = testtext.replace('‘', "'")
    testtext = testtext.replace('“', '"')
    testtext = testtext.replace('”', '"')
    testtext = testtext.replace('á', 'a')
    testtext = testtext.replace('ﬂ', 'fl')
    testtext = testtext.replace('é', 'e')
    testtext = testtext.replace('ﬁ', 'fi')
    testtext = testtext.replace('è', 'e')
    testtext = testtext.replace('É', 'E')
    testtext = testtext.replace('ü', 'u')
    testtext = testtext.replace('…', '...')

    testtext = re.sub(r"[가-힣]+", " ", testtext)
    pattern = r"['!\"#$%&()*+,\-./:;<=>?@\[\\\]^_`{|}~]+"
    testtext = re.sub(pattern, " ", testtext)
    testtext = re.sub(r"\s+", " ", testtext)
    testtext = re.sub(r'\s\n', ' ', testtext)
    testtext = testtext.strip()

    words = re.split(r"\s+", allText)
    unique_words = []
    seen = set()
    for word in words:
        if word and word not in seen:
            unique_words.append(word)
            seen.add(word)
    unique_words.sort(key=len, reverse=True)

    for word in unique_words:
        testtext = testtext.replace(word, " ")

    # 정제된 텍스트 저장 (결과물 1: output_txt 사용)
    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(testtext)

    # 6. 문장 분리
    sat_sm = SaT("sat-12l-sm")
    sat_sm.half().to("cuda")

    seg_list = sat_sm.split(testtext)
    clean_seg_list = []
    for seg in seg_list:
        seg = re.sub(r'\s+', ' ', seg)
        seg = seg.strip()
        if seg:
            clean_seg_list.append(seg)
    seg_list = clean_seg_list

    # 7. 구동사 리스트 로드 (개인 설정: phrasal_verb_file 사용)
    df = pd.read_excel(phrasal_verb_file)
    phrasalVerb = df['Phrasal verb'].tolist()
    phrasalVerb_set = set(phrasalVerb)

    verbDict = {}
    sentDict = {}
    for verb in phrasalVerb:
        verbDict[verb] = 0
        sentDict[verb] = []

    seg_list.sort(key=len)

    def list_chunk(lst, n):
        chunks = []
        for i in range(0, len(lst), n):
            chunk = lst[i:i+n]
            chunks.append(chunk)
        return chunks

    list_chunked = list_chunk(lst=seg_list, n=200000)

    # 8. Stanza 설정
    stanza.download('en')
    nlp = stanza.Pipeline('en', processors='tokenize,lemma,pos,depparse', tokenize_no_ssplit=True, verbose=True, use_gpu=True)

    TARGET_DEPS = {'prt', 'advmod', 'compound:prt', 'prep'}
    batch_size = 1000

    print("분석 시작...")

    for chunk_idx in range(len(list_chunked)):
        current_list = list_chunked[chunk_idx]
        total_sents = len(current_list)
        print(f"Chunk {chunk_idx} 시작 - 문장 수: {total_sents}")

        for i in tqdm(range(0, total_sents, batch_size)):
            batch = current_list[i:i + batch_size]
            docs = nlp(batch)

            for sentence in docs.sentences:
                for head, relation, dep in sentence.dependencies:
                    if head.upos == 'VERB' and relation in TARGET_DEPS:
                        lemma_key = f"{head.lemma} {dep.lemma}"
                        if lemma_key in verbDict:
                            verbDict[lemma_key] += 1
                            sentDict[lemma_key].append(sentence.text)

            del docs
            gc.collect()
            torch.cuda.empty_cache()

    print("분석 완료!")

    # 9. 결과 데이터프레임 만들기
    verb_list = []
    count_list = []
    sentences_list = []
    for key in verbDict:
        verb_list.append(key)
        count_list.append(verbDict[key])
        unique_sentences = list(set(sentDict[key]))
        sentences_list.append('\n'.join(unique_sentences))

    df_count = pd.DataFrame({'Verb': verb_list, 'Count': count_list})
    df_sentences = pd.DataFrame({'Verb': verb_list, 'Sentences': sentences_list})
    df_final = pd.merge(df_count, df_sentences, on='Verb')

    # 10. 엑셀 저장 (결과물 2: output_excel 사용)
    df_final.to_excel(output_excel, index=False)
    print(f"엑셀 저장 완료: {output_excel}")
