from llama_parse import LlamaParse

def parse_pdf(pdf_file, api_key):
    llama = LlamaParse(api_key=api_key)
    result = llama.parse_file(pdf_file)
    return result.text
