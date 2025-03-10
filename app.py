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
# from docling import Document
from pdf2image import convert_from_path
import pdf2md
import md2pdf

SAMPLE_PDF_DOCUMENT= Path("./sample_files/benchmark.pdf")
SAMPLE_MARKDOWN_DOCUMENT = Path("./sample_files/benchmark.md")

conversion_menu = {
    "PDF to Markdown": ["PyMuPDF", "PyMuPDF4LLM", "Docling"],
    "Markdown to PDF": ["WeasyPrint", "Pandoc"]
}

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

def get_md_sample_file_content(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            input_content = f.read()
            
        return input_content
    else:
        st.error("Benchmark markdown file not found.")
        return ''

def get_uploaded_file_content():
    uploaded_file = st.file_uploader("Upload a markdown file", type=["md", "markdown", "txt"])
    return uploaded_file

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

def preview(file_path: str):
    file_path = str(file_path)
    if file_path.endswith(".pdf"):
        cols = st.columns(4)
        with cols[0]:
            width_pct = st.slider("PDF Preview Size", 10, 100, 50)-1
        images = convert_from_path(file_path)
        for i, image in enumerate(images):
            cols = st.columns([width_pct / 100, 1 - (width_pct / 100)])
            cols[0].image(image, caption=f'Page {i + 1}', use_container_width=True)
    elif file_path.endswith(".md"):
        with open(file_path, "r") as f:
            content = f.read()
        st.markdown(content)

st.set_page_config(
    page_title="PDF-Markdown Converter",
    page_icon="📄",
    layout="wide"
)

# Create directories for sample files if they don't exist
if not os.path.exists("sample_files"):
    os.makedirs("sample_files")
    

# ------------------------------------------------------------------------------------------------------
# App UISAMPLE_PDF_DOCUMENT
# ------------------------------------------------------------------------------------------------------

st.title("PDF ↔ Markdown Converter")

# Conversion direction
conversion_type = st.radio(
    "Select conversion type:",
    list(conversion_menu.keys()),
    horizontal=True
)

# Package selection for PDF to Markdown
conversion_package = st.selectbox(
        "Select conversion package:",
        conversion_menu[conversion_type],
    )
    
# File source selection
file_source = st.radio(
    "Choose file source:",
    ["Use benchmark file", "Upload my own file"],
    horizontal=True
)

uploaded_file = None
file_path = None
converter = None
if conversion_type == "Markdown to PDF":
    if file_source == "Use benchmark file":
        file_path = SAMPLE_MARKDOWN_DOCUMENT
        md_content = get_md_sample_file_content(file_path)
    else:  # Upload option
        uploaded_file = get_uploaded_file_content()
        if uploaded_file:
            md_content = uploaded_file.getvalue().decode()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as temp_file:
                temp_file.write(uploaded_file.getvalue())
                file_path = temp_file.name    
    with st.expander("Preview Markdown Input File"):
        preview(file_path)
    converter = md2pdf.Converter(conversion_package, file_path)
    
else:  # PDF to Markdown
    if file_source == "Use benchmark file":
        if os.path.exists(SAMPLE_PDF_DOCUMENT):
            file_path = SAMPLE_PDF_DOCUMENT
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
    with st.expander("Preview PDF Input File"):
        preview(file_path)
    converter = pdf2md.Converter(conversion_package, file_path)


# Convert button
if st.button("Convert", type="primary"):
    with st.spinner("Converting..."):
        try:
            converter.convert()
            with st.expander("Preview Output File"):
                preview(converter.output_path)
            st.markdown(get_file_download_link(converter.output_path, "📥 Download Converted File"), unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Conversion failed: {str(e)}")

# App footer
st.markdown("---")
st.markdown("PDF-Markdown Converter v 0.0.3| Made with Streamlit | [git repo](https://github.com/lcalmbach/pdf2md-converter)")

# Cleanup temporary files on session end
def cleanup():
    if 'output_path' in locals():
        try:
            os.unlink(converter.output_path)
        except:
            pass

# Register cleanup function
import atexit
atexit.register(cleanup)