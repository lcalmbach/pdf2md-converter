import streamlit as st
import os
import base64
from pathlib import Path
import tempfile
import markdown
import fitz  # PyMuPDF
import pypandoc
import re
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import importlib.util
import shutil
from pdf2image import convert_from_path

SAMPLE_PDF_DOCUMENT= Path("./sample_files/benchmark.pdf")
SAMPLE_MARKDOWN_DOCUMENT = Path("./sample_files/benchmark.md")

# Check for optional dependencies
def is_package_installed(package_name):
    return importlib.util.find_spec(package_name) is not None

# Check for pymupdf4llm
PYMUPDF4LLM_AVAILABLE = is_package_installed("pymupdf4llm")
if PYMUPDF4LLM_AVAILABLE:
    import pymupdf4llm

# Check for docling
DOCLING_AVAILABLE = is_package_installed("docling")
if DOCLING_AVAILABLE:
    import docling

# Check if pandoc is installed
def is_pandoc_available():
    try:
        # Try to get the version, which will throw an exception if pandoc is not available
        pypandoc.get_pandoc_version()
        return True
    except (OSError, ImportError, RuntimeError):
        return False

PANDOC_AVAILABLE = is_pandoc_available()

st.set_page_config(
    page_title="PDF-Markdown Converter",
    page_icon="📄",
    layout="wide"
)

# Create directories for sample files if they don't exist
if not os.path.exists("sample_files"):
    os.makedirs("sample_files")
    

def md_to_pdf(md_content, output_path):
    """Convert markdown to PDF using WeasyPrint"""
    # Convert markdown to HTML
    html = markdown.markdown(
        md_content,
        extensions=['extra', 'codehilite', 'tables']
    )
    
    # Add basic styling
    font_config = FontConfiguration()
    styled_html = f"""
    <html>
    <head>
        <style>
            @page {{
                margin: 2.5cm;
            }}
            body {{
                font-family: sans-serif;
                line-height: 1.6;
            }}
            pre {{
                background-color: #f4f4f4;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
            }}
            code {{
                font-family: monospace;
                background-color: #f4f4f4;
                padding: 2px 4px;
                border-radius: 3px;
            }}
            blockquote {{
                border-left: 4px solid #ccc;
                padding-left: 15px;
                color: #666;
                margin-left: 0;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            h1, h2, h3, h4, h5, h6 {{
                margin-top: 1em;
                margin-bottom: 0.5em;
            }}
            p {{
                margin-top: 0.5em;
                margin-bottom: 0.5em;
            }}
            ul, ol {{
                margin-top: 0.5em;
                margin-bottom: 0.5em;
            }}
        </style>
    </head>
    <body>
        {html}
    </body>
    </html>
    """
    
    # Generate PDF with WeasyPrint
    html_doc = HTML(string=styled_html)
    html_doc.write_pdf(output_path, font_config=font_config)
    
    return output_path

def pdf_to_md_pymupdf(pdf_path):
    """Convert PDF to markdown using PyMuPDF (fitz) for text extraction and custom formatting"""
    doc = fitz.open(pdf_path)
    text_blocks = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Get text blocks with formatting information
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    if "spans" in line:
                        line_text = ""
                        is_bold = False
                        is_heading = False
                        font_size = 0
                        
                        for span in line["spans"]:
                            # Check for formatting hints
                            if span["text"].strip():
                                current_font_size = span["size"]
                                current_font = span["font"].lower()
                                current_text = span["text"]
                                
                                # Detect possible headings based on font size
                                if current_font_size > font_size:
                                    font_size = current_font_size
                                
                                # Detect bold text
                                if "bold" in current_font or span["flags"] & 2:  # 2 is bold flag
                                    is_bold = True
                                
                                line_text += current_text
                        
                        if line_text.strip():
                            # Determine if this might be a heading based on font size
                            if font_size > 12:  # Arbitrary threshold - adjust as needed
                                is_heading = True
                            
                            text_blocks.appeSAMPLE_PDF_DOCUMENTnd({
                                "text": line_text.strip(),
                                "is_bold": is_bold,
                                "is_heading": is_heading,
                                "font_size": font_size,
                                "page": page_num + 1
                            })
    
    # Convert to markdown
    md_lines = []
    prev_block = None
    
    for block in text_blocks:
        text = block["text"].strip()
        
        # Skip empty lines
        if not text:
            continue
            
        # Detect headings based on formatting and content
        if block["is_heading"] or (len(text) < 80 and not text.endswith(('.', ',', ';', ':', '?', '!'))):
            # Determine heading level based on font size
            if block["font_size"] >= 18:
                md_lines.append(f"# {text}")
            elif block["font_size"] >= 16:
                md_lines.append(f"## {text}")
            elif block["font_size"] >= 14:
                md_lines.append(f"### {text}")
            elif block["is_bold"]:
                md_lines.append(f"**{text}**")
            else:
                md_lines.append(text)
        else:
            # Regular text paragraph
            if block["is_bold"]:
                md_lines.append(f"**{text}**")
            else:
                md_lines.append(text)
            
        # Add separator between blocks from different pages
        if prev_block and prev_block["page"] != block["page"]:
            md_lines.append("\n---\n")
            
        prev_block = block
    
    # Join all lines
    md_content = "\n\n".join(md_lines)
    
    # Some post-processing to clean up the text
    # Remove excess newlines
    md_content = re.sub(r'\n{3,}', '\n\n', md_content)
    SAMPLE_PDF_DOCUMENT
    """Convert PDF to markdown using Pandoc"""
    if not PANDOC_AVAILABLE:
        return "Pandoc is not installed or not available. Please install Pandoc and ensure it's in your PATH."
    
    try:
        md_content = pypandoc.convert_file(pdf_path, 'md')
        return md_content
    except Exception as e:
        st.error(f"Pandoc conversion error: {str(e)}")
        return "Conversion failed. Make sure Pandoc is installed correctly."

def pdf_to_md_pymupdf4llm(pdf_path):
    """Convert PDF to markdown using pymupdf4llm"""
    if not PYMUPDF4LLM_AVAILABLE:
        return "pymupdf4llm package is not installed. Please install it with 'pip install pymupdf4llm'."
    
    try:
        from pymupdf4llm import parse_pdf
        result = parse_pdf(pdf_path, merge_overlapping=True, detect_lists=True, convert_formulas=True)
        return result.get_markdown()
    except Exception as e:
        st.error(f"pymupdf4llm conversion error: {str(e)}")
        return f"Conversion with pymupdf4llm failed: {str(e)}"

def pdf_to_md_docling(pdf_path):
    """Convert PDF to markdown using docling"""
    if not DOCLING_AVAILABLE:
        return "docling package is not installed. Please install it with 'pip install docling'."
    
    try:
        from docling import Document
        doc = Document.from_pdf(pdf_path)
        return doc.to_markdown()
    except Exception as e:
        st.error(f"docling conversion error: {str(e)}")
        return f"Conversion with docling failed: {str(e)}"

def create_download_link(content, filename, text):
    """Generate a download link for the given content"""
    b64 = base64.b64encode(content).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{text}</a>'
    return href

def get_file_download_link(file_path, link_text):
    """Generate a download link for an existing file"""
    with open(file_path, "rb") as f:
        bytes_data = f.read()
    b64 = base64.b64encode(bytes_data).decode()
    mime_type = "application/pdf" if file_path.endswith(".pdf") else "text/markdown"
    filename = os.path.basename(file_path)
    href = f'<a href="data:file/{mime_type};base64,{b64}" download="{filename}">{link_text}</a>'
    return href

def display_pdf_preview(pdf_path):
    """Generate and display PDF preview using pdf2image"""
    cols = st.columns(4)
    with cols[0]:
        width_pct = st.slider("Size", 10, 100, 50)-1
    images = convert_from_path(pdf_path)
    for i, image in enumerate(images):
        cols = st.columns([width_pct / 100, 1 - (width_pct / 100)])
        cols[0].image(image, caption=f'Page {i + 1}', use_container_width=True)

# App UISAMPLE_PDF_DOCUMENT
st.title("PDF ↔ Markdown Converter")

# Instructions
with st.expander("How to use this app"):
    st.markdown("""
    1. Choose the conversion direction (PDF to Markdown or Markdown to PDF)
    2. Select a benchmark file or upload your own
    3. For PDF to Markdown conversion, select the conversion package you want to use
    4. Click the 'Convert' button
    5. Preview the conversion result
    6. Use the download link to save the generated file
    
    **Conversion Packages:**
    - **Pandoc**: A universal document converter, good for preserving structure
    - **PyMuPDF**: Uses direct text extraction with heuristics to determine structure
    - **PyMuPDF4LLM**: Enhanced version of PyMuPDF designed for LLM-friendly markdown output
    - **Docling**: Document processing library with good semantic structure preservation
    
    **Note:** PDF to Markdown conversion may not preserve all formatting perfectly, and results vary by package.
    """)

# Conversion direction
conversion_type = st.radio(
    "Select conversion type:",
    ["Markdown to PDF", "PDF to Markdown"],
    horizontal=True
)

# Package selection for PDF to Markdown
conversion_package = None
if conversion_type == "PDF to Markdown":
    conversion_package = st.selectbox(
        "Select conversion package:",
        ["PyMuPDF (Default)", "Pandoc", "PyMuPDF4LLM", "Docling"],
        help="Different packages have different strengths in preserving document structure and formatting"
    )
    
    # Show package availability status
    cols = st.columns(4)
    with cols[0]:
        pandoc_status = "✅ Available" if PANDOC_AVAILABLE else "❌ Not Found"
        pymupdf_status = "✅ Available"  # Always available since it's a required dependency
        st.markdown(f"**Pandoc**: {pandoc_status}")
        st.markdown(f"**PyMuPDF**: {pymupdf_status}")
    with cols[1]:
        pymupdf4llm_status = "✅ Available" if PYMUPDF4LLM_AVAILABLE else "❌ Not Installed"
        docling_status = "✅ Available" if DOCLING_AVAILABLE else "❌ Not Installed"
        st.markdown(f"**PyMuPDF4LLM**: {pymupdf4llm_status}")
        st.markdown(f"**Docling**: {docling_status}")

# File source selection
file_source = st.radio(
    "Choose file source:",
    ["Use benchmark file", "Upload my own file"],
    horizontal=True
)

uploaded_file = None
file_path = None

if conversion_type == "Markdown to PDF":
    if file_source == "Use benchmark file":
        if os.path.exists(SAMPLE_MARKDOWN_DOCUMENT):
            with open(SAMPLE_MARKDOWN_DOCUMENT, "r") as f:
                input_content = f.read()
                
            st.subheader("Benchmark Markdown Content")
            st.text_area("Markdown Content", input_content, height=200, disabled=True)
        else:
            st.error("Benchmark markdown file not found.")
    else:  # Upload option
        uploaded_file = st.file_uploader("Upload a markdown file", type=["md", "markdown", "txt"])
        if uploaded_file:
            input_content = uploaded_file.getvalue().decode()
            st.subheader("Uploaded Markdown Content")
            st.text_area("Markdown Content", input_content, height=200, disabled=True)
            
            # Save uploaded file to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as temp_file:
                temp_file.write(uploaded_file.getvalue())
                file_path = temp_file.name
else:  # PDF to Markdown
    if file_source == "Use benchmark file":
        if os.path.exists(SAMPLE_PDF_DOCUMENT):
            st.subheader("Benchmark PDF Preview")
            display_pdf_preview(SAMPLE_PDF_DOCUMENT)
        else:
            st.error("Benchmark PDF file not found.")
    else:  # Upload option
        uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
        if uploaded_file:
            # Save uploaded file to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(uploaded_file.getvalue())
                file_path = temp_file.name
                
            # Display PDF preview in an expander
            st.subheader("Uploaded PDF Preview")
            with st.expander("Preview PDF"):
                display_pdf_preview(file_path)

# Convert button
if st.button("Convert", type="primary"):
    with st.spinner("Converting..."):
        try:
            if conversion_type == "Markdown to PDF":
                # Read input content if not already loaded
                if 'input_content' not in locals():
                    with open(file_path, "r") as f:
                        input_content = f.read()
                
                # Generate output file path
                output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                output_file.close()
                output_path = output_file.name
                
                # Convert markdown to PDF
                md_to_pdf(input_content, output_path)
                
                # Display PDF preview
                st.subheader("Generated PDF Preview")
                display_pdf_preview(output_path)
                
                # Provide download link
                st.markdown(get_file_download_link(output_path, "📥 Download PDF"), unsafe_allow_html=True)
            else:  # PDF to Markdown
                # Convert PDF to markdown based on selected package
                if conversion_package == "Pandoc":
                    md_content = pdf_to_md_pandoc(file_path)
                elif conversion_package == "PyMuPDF4LLM":
                    md_content = pdf_to_md_pymupdf4llm(file_path)
                elif conversion_package == "Docling":
                    md_content = pdf_to_md_docling(file_path)
                else:  # Default to PyMuPDF
                    md_content = pdf_to_md_pymupdf(file_path)
                
                # Display markdown preview
                st.subheader("Generated Markdown Preview")
                st.text_area("Markdown Output", md_content, height=300, disabled=True)
                
                # Save to temporary file for download
                output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".md")
                output_file.write(md_content.encode())
                output_file.close()
                
                # Provide download link
                st.markdown(get_file_download_link(output_file.name, "📥 Download Markdown"), unsafe_allow_html=True)
                
                # Show rendered preview in an expander
                with st.expander("Rendered Markdown Preview"):
                    st.markdown(md_content)
                
                # Add a comparison note if multiple conversions were done
                if conversion_package in ["Pandoc", "PyMuPDF4LLM", "Docling"]:
                    st.info(f"Conversion completed using {conversion_package}. Different packages may produce different results.")
                
        except Exception as e:
            st.error(f"Conversion failed: {str(e)}")

# Add a feature comparison table
with st.expander("PDF to Markdown Conversion Package Comparison"):
    st.markdown("""
    | Feature | PyMuPDF | Pandoc | PyMuPDF4LLM | Docling |
    |---------|---------|--------|-------------|---------|
    | Table detection | ⭐⭐☆ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐☆ |
    | List detection | ⭐⭐☆ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
    | Structure preservation | ⭐⭐☆ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
    | Image handling | ⭐☆☆ | ⭐⭐☆ | ⭐⭐☆ | ⭐⭐⭐ |
    | Formula detection | ☆☆☆ | ⭐⭐☆ | ⭐⭐⭐ | ⭐⭐☆ |
    | Speed | ⭐⭐⭐ | ⭐⭐☆ | ⭐⭐☆ | ⭐☆☆ |
    | Dependencies | Minimal | Requires Pandoc | Moderate | Extensive |
    """)
    
    st.markdown("""
    **Additional notes:**
    - **PyMuPDF**: Fast with minimal dependencies but may struggle with complex formatting
    - **Pandoc**: Excellent all-around converter but requires external Pandoc installation
    - **PyMuPDF4LLM**: Optimized for creating LLM-friendly markdown from PDFs with good structure detection
    - **Docling**: Advanced document understanding with semantic analysis, but may be slower
    """)

# App footer
st.markdown("---")
st.markdown("PDF-Markdown Converter | Made with Streamlit")

# Cleanup temporary files on session end
def cleanup():
    if 'file_path' in locals() and file_source == "Upload my own file":
        try:
            os.unlink(file_path)
        except:
            pass
    if 'output_path' in locals():
        try:
            os.unlink(output_path)
        except:
            pass

# Register cleanup function
import atexit
atexit.register(cleanup)