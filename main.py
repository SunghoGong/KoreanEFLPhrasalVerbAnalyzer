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
    - output_txt: 정제된 TXT 파일 이름 (최종 저장물)
    이 버전은 중간 텍스트 파일 저장/불러오기를 건너뜁니다.
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
        
        if filename.lower().endswith('.pdf'):
            pdf_files.append(file_path)
        elif filename.lower().endswith('.zip'):
            print(f"ZIP 파일 해제 중: {filename}")
            unzip_command = f"unzip -o {file_path} -d {upload_folder}"
            subprocess.run(unzip_command, shell=True)
            extracted_pdfs = glob.glob(os.path.join(upload_folder, '**', '*.pdf'), recursive=True)
            pdf_files.extend(extracted_pdfs)

    print("업로드된 PDF 파일 수:", len(pdf_files))
    if len(pdf_files) == 0:
        print("처리할 PDF가 없습니다. 함수를 종료합니다.")
        return

    # 2. spaCy 세팅 (문장 분리용) - 한 번만 초기화
    print("spaCy 로딩 및 설정...")
    nlp_spacy = spacy.load("en_core_web_sm")
    disable_list = ["ner", "tagger", "attribute_ruler", "lemmatizer"]
    if "senter" in nlp_spacy.pipe_names:
        disable_list.append("parser")
    nlp_spacy.disable_pipes(disable_list)
    if "senter" not in nlp_spacy.pipe_names and "parser" not in nlp_spacy.pipe_names:
        nlp_spacy.add_pipe("senter")
    print("spaCy 준비 완료.")

    # 3. PDF -> 문장 리스트(메모리)로 추출 (중간 파일 저장 없음)
    sentences_all = []
    total_pages = 0
    for pdf_path in pdf_files:
        try:
            print(f"PDF 파일 로딩 중: {pdf_path}")
            start_time = time.time()
            doc = fitz.open(pdf_path)
            for page in doc:
                text = page.get_text()
                if not text:
                    continue
                spacy_doc = nlp_spacy(text)
                for sent in spacy_doc.sents:
                    clean_sent = sent.text.strip()
                    if clean_sent:
                        sentences_all.append(clean_sent)
                total_pages += 1
            doc.close()
            end_time = time.time()
            print(f"처리 완료: {pdf_path} (소요: {end_time - start_time:.2f}s)")
        except Exception as e:
            print(f"오류로 인해 건너뜀 ({pdf_path}): {e}")

    print(f"추출된 전체 문장 수: {len(sentences_all)} (총 페이지: {total_pages})")

    # 4. 전체 텍스트(문장 단위 합치기)
    allText = "\n".join(sentences_all)

    # 5. 텍스트 정제 (원래 로직 유지)
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

    # 원래 코드의 unique word 제거 로직 유지 (필요 없으면 주석 처리 가능)
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

    # 정제된 텍스트 저장 (결과물 1: output_txt)
    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(testtext)
    print(f"정제된 텍스트 저장 완료: {output_txt}")

    # 6. 문장 분리 (SaT) — testtext 사용
    sat_sm = SaT("sat-12l-sm")
    try:
        sat_sm.half().to("cuda")
    except Exception:
        # CUDA가 없거나 이동 실패 시 경고만 출력하고 계속 진행
        print("GPU로 SaT 이동 실패(또는 CUDA 없음). CPU로 실행합니다.")

    seg_list = sat_sm.split(testtext)
    clean_seg_list = []
    for seg in seg_list:
        seg = re.sub(r'\s+', ' ', seg)
        seg = seg.strip()
        if seg:
            clean_seg_list.append(seg)
    seg_list = clean_seg_list

    # 7. 구동사 리스트 로드
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

    print("구동사 분석 시작...")

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
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass

    print("구동사 분석 완료!")

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
