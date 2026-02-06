"""
pdfplumber를 사용한 PDF 파싱 테스트
MinerU와 비교하기 위한 간단한 파서
"""
import pdfplumber
from pathlib import Path

PDF_PATH = "/home/bbo/my_project_2026/특구사업/MinerU/output/Regulatory Guide 1.206/auto/Regulatory Guide 1.206_origin.pdf"
OUTPUT_DIR = Path("/home/bbo/my_project_2026/특구사업/pdfplumber_test")

def extract_text_to_markdown(pdf_path: str, output_dir: Path):
    """PDF에서 텍스트 추출하여 마크다운으로 저장"""

    md_lines = []
    tables_found = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"총 페이지 수: {total_pages}")

        for i, page in enumerate(pdf.pages):
            print(f"Processing page {i+1}/{total_pages}", end='\r')

            # 텍스트 추출
            text = page.extract_text()
            if text:
                md_lines.append(f"\n<!-- Page {i+1} -->\n")
                md_lines.append(text)

            # 테이블 추출
            tables = page.extract_tables()
            if tables:
                for j, table in enumerate(tables):
                    tables_found.append({
                        'page': i+1,
                        'table_idx': j,
                        'rows': len(table),
                        'cols': len(table[0]) if table else 0
                    })

                    # 마크다운 테이블로 변환
                    md_lines.append(f"\n<!-- Table from page {i+1} -->\n")
                    if table and len(table) > 0:
                        # 헤더
                        header = table[0]
                        header_clean = [str(cell).replace('\n', ' ') if cell else '' for cell in header]
                        md_lines.append("| " + " | ".join(header_clean) + " |")
                        md_lines.append("|" + "|".join(["---"] * len(header)) + "|")

                        # 데이터 행
                        for row in table[1:]:
                            row_clean = [str(cell).replace('\n', ' ') if cell else '' for cell in row]
                            md_lines.append("| " + " | ".join(row_clean) + " |")
                    md_lines.append("")

    print(f"\nProcessing complete!")

    # 마크다운 파일 저장
    md_content = "\n".join(md_lines)
    md_path = output_dir / "Regulatory_Guide_1.206_pdfplumber.md"
    md_path.write_text(md_content, encoding='utf-8')
    print(f"Markdown saved: {md_path}")
    print(f"File size: {md_path.stat().st_size / 1024:.1f} KB")

    # 통계 출력
    print(f"\n=== 통계 ===")
    print(f"총 테이블: {len(tables_found)}개")

    return md_path, tables_found

if __name__ == "__main__":
    md_path, tables = extract_text_to_markdown(PDF_PATH, OUTPUT_DIR)
