# PDF to Markdown Converter

This repository contains a tool for converting PDF files to Markdown format and vice versa. It leverages several libraries to handle PDF parsing and Markdown generation.

## Requirements

The following Python packages are required (included in requirements.txt):

- streamlit
- docling
- pymupdf4llm
- markdown
- pdfkit
- pymupdf
- pypandoc
- weasyprint
- [pdfplumber](https://github.com/jsvine/pdfplumber) 
- openai

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/pdf2markdown.git
    cd pdf2markdown
    ```

2. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

## Usage
```
>.venv/scripts/activate (Windows) or
>.venv/scripts/activate (Linux)
>(.venv)streamlit run app.py
```

Use the demo files to get a first impression and compress the `convert` button.

Then change the file source to *Upload my own file* and upload your file, press `convert` button again.

## Combined Text-Extraction and Markdown-Conversion using ChatGPT
The pdfplumber + ChatGPT option all


## Development

To contribute to this project, follow these steps:

1. Fork the repository.
2. Create a new branch:
    ```sh
    git checkout -b feature-branch
    ```
3. Make your changes and commit them:
    ```sh
    git commit -m "Description of changes"
    ```
4. Push to the branch:
    ```sh
    git push origin feature-branch
    ```
5. Create a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Conversion Package Comparison 

| Feature | PyMuPDF | Pandoc | PyMuPDF4LLM | Docling |
|---------|---------|--------|-------------|---------|
| Table detection | ⭐⭐☆ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐☆ |
| List detection | ⭐⭐☆ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Structure preservation | ⭐⭐☆ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Image handling | ⭐☆☆ | ⭐⭐☆ | ⭐⭐☆ | ⭐⭐⭐ |
| Formula detection | ☆☆☆ | ⭐⭐☆ | ⭐⭐⭐ | ⭐⭐☆ |
| Speed | ⭐⭐⭐ | ⭐⭐☆ | ⭐⭐☆ | ⭐☆☆ |
| Dependencies | Minimal | Requires Pandoc | Moderate | Extensive |

**Additional notes:**
- **PyMuPDF**: Fast with minimal dependencies but may struggle with complex formatting
- **Pandoc**: Excellent all-around converter but requires external Pandoc installation
- **PyMuPDF4LLM**: Optimized for creating LLM-friendly markdown from PDFs with good structure detection
- **Docling**: Advanced document understanding with semantic analysis, but may be slower
