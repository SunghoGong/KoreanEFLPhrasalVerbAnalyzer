import argparse
import os
import utils
import analyzer

def main():
    parser = argparse.ArgumentParser(description="PDF 구동사 분석기")
    
    # 실행 모드 설정
    parser.add_argument('--mode', type=str, default='all', choices=['clean', 'analyze', 'all'],
                        help="실행 모드: clean(정제만), analyze(분석만), all(전체)")
    
    # 경로 설정
    parser.add_argument('--input_dir', type=str, default='./pdfs', help="PDF 파일이 있는 폴더 경로")
    parser.add_argument('--pv_file', type=str, default='Phrasal Verb List Updating Project.xlsx', help="구동사 리스트 엑셀 파일 경로")
    parser.add_argument('--output_txt', type=str, default='refined_text.txt', help="정제된 텍스트 저장 경로")
    parser.add_argument('--output_excel', type=str, default='final_result.xlsx', help="최종 결과 엑셀 파일 경로")

    args = parser.parse_args()

    # 1단계: PDF 추출 및 텍스트 정제
    if args.mode in ['clean', 'all']:
        # PDF 폴더가 있는지 확인
        if not os.path.exists(args.input_dir) and args.mode == 'clean':
            print(f"경고: 입력 폴더({args.input_dir})가 없습니다.")
        
        # 임시 파일명
        raw_txt = "temp_raw.txt"
        
        # PDF -> Raw Text
        if os.path.exists(args.input_dir):
            utils.extract_text_from_pdfs(args.input_dir, raw_txt)
        
        # Raw Text -> Refined Text (Cleaning + SaT)
        if os.path.exists(raw_txt):
            utils.refine_and_segment(raw_txt, args.output_txt)
            os.remove(raw_txt) # 임시 파일 삭제
        else:
            print("처리할 텍스트 소스가 없습니다.")

    # 2단계: 구동사 분석
    if args.mode in ['analyze', 'all']:
        if not os.path.exists(args.output_txt):
            print(f"오류: 분석할 텍스트 파일({args.output_txt})이 없습니다. 먼저 clean 모드를 실행하세요.")
            return

        if not os.path.exists(args.pv_file):
            print(f"오류: 구동사 리스트 파일({args.pv_file})이 없습니다.")
            return

        # 정제된 텍스트 로드
        with open(args.output_txt, 'r', encoding='utf-8') as f:
            sentences = [line.strip() for line in f if line.strip()]

        # 분석 실행
        analyzer.run_phrasal_analysis(sentences, args.pv_file, args.output_excel)

if __name__ == "__main__":
    main()
