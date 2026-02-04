import pandas as pd
import stanza
import torch
import gc
from tqdm import tqdm
from collections import defaultdict

def run_phrasal_analysis(sentences, phrasal_verb_path, output_excel="result.xlsx"):
    """정제된 문장 리스트와 구동사 리스트를 받아 분석 수행"""
    print("🔍 구동사 분석 시작...")

    # 구동사 리스트 로드
    try:
        df_pv = pd.read_excel(phrasal_verb_path)
        pv_list = df_pv['Phrasal verb'].tolist()
        # set으로 만들어 검색 속도 향상
        # (로직상 lemma_key in verbDict 검사를 위해 dict 초기화가 필요)
        verbDict = {each: 0 for each in pv_list}
        sentDict = {each: [] for each in pv_list}
    except Exception as e:
        print(f"❌ 구동사 리스트 로드 실패: {e}")
        return

    # Stanza 파이프라인 설정
    stanza.download('en')
    nlp = stanza.Pipeline('en', processors='tokenize,lemma,pos,depparse', 
                          tokenize_no_ssplit=True, verbose=True, use_gpu=True)
    
    TARGET_DEPS = {'prt', 'advmod', 'compound:prt', 'prep'}
    batch_size = 1000

    # 문장 리스트 정렬 (배치 처리 효율화)
    sentences.sort(key=len)

    # 청크 나누기 함수
    def list_chunk(lst, n):
        return [lst[i:i+n] for i in range(0, len(lst), n)]

    # 20만개 단위로 청크 분할 (메모리 관리)
    chunks = list_chunk(sentences, 200000)

    print(f"  - 총 {len(sentences)} 문장, {len(chunks)}개 청크로 처리")

    for idx, chunk in enumerate(chunks):
        print(f"  Processing Chunk {idx+1}/{len(chunks)}")
        
        for i in tqdm(range(0, len(chunk), batch_size)):
            batch = chunk[i : i + batch_size]
            docs = nlp(batch)
            
            for sentence in docs.sentences:
                for head, relation, dep in sentence.dependencies:
                    if head.upos == 'VERB' and relation in TARGET_DEPS:
                        lemma_key = f"{head.lemma} {dep.lemma}"
                        
                        if lemma_key in verbDict:
                            verbDict[lemma_key] += 1
                            sentDict[lemma_key].append(sentence.text)
            
            # 메모리 정리
            del docs
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    # 결과 정리 및 저장
    print("💾 결과 저장 중...")
    
    unique_sentDict = {k: list(set(v)) for k, v in sentDict.items()} # 중복 문장 제거
    
    df_count = pd.DataFrame(list(verbDict.items()), columns=['Verb', 'Count'])
    df_sentences = pd.DataFrame(list(unique_sentDict.items()), columns=['Verb', 'Sentences_List'])
    
    df_merged = pd.merge(df_count, df_sentences, on='Verb', how='inner')
    
    # 리스트를 줄바꿈 문자열로 변환
    df_final = df_merged.assign(
        Sentences=lambda x: x['Sentences_List'].apply(lambda s: '\n'.join(s))
    ).drop(columns=['Sentences_List'])

    df_final.to_excel(output_excel, index=False)
    print(f"🎉 분석 완료! 결과 파일: {output_excel}")