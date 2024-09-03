from llama_parse import LlamaParse


def parse_pdf(pdf_file, api_key):
    parser = LlamaParse(
        api_key=api_key,  # can also be set in your env as LLAMA_CLOUD_API_KEY
        result_type="markdown",  # "markdown" and "text" are available
        num_workers=4,  # if multiple files passed, split in `num_workers` API calls
        verbose=True,
        language="en",  # Optionally you can define a language, default=en
    )
    documents = parser.load_data(pdf_file)
    return documents[0].text
