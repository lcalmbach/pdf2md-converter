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
MAX_PAGES_PREVIEW = 2  # max number of pages for pdf docs to preview in order not to crash the app on streamlit community cloud

conversion_menu = {
    "PDF to Markdown": ["PyMuPDF", "PyMuPDF4LLM", "Docling", "PDFplumber+ChatGPT-4o", "ChatGPT-4o-vision", "Mistral-OCR"],
    "Markdown to PDF": ["WeasyPrint", "Pandoc"]
}


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

def preview(file_path: Path):
    if file_path.suffix == ".pdf":
        cols = st.columns(4)
        with cols[0]:
            width_pct = st.slider("PDF Preview Size", 10, 100, 50)-1
        images = convert_from_path(str(file_path), last_page = MAX_PAGES_PREVIEW -1)
        for i, image in enumerate(images):
            cols = st.columns([width_pct / 100, 1 - (width_pct / 100)])
            cols[0].image(image, caption=f'Page {i + 1}', use_container_width=True)
    elif file_path.suffix == ".md":
        with file_path.open("r") as f:
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
# App UI SAMPLE_PDF_DOCUMENT
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
    if "converter" in st.session_state:
        st.session_state.converter.lib = conversion_package
        st.session_state.converter.input_path = file_path
    else:
        st.session_state.converter = md2pdf.Converter(conversion_package, file_path)
    
else:  # PDF to Markdown
    if file_source == "Use benchmark file":
        file_path = SAMPLE_PDF_DOCUMENT
    else:  # Upload option
        file_path = None
        uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
        if uploaded_file:
            # Save uploaded file to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(uploaded_file.getvalue())
                file_path = Path(temp_file.name)
            # Display PDF preview in an expander
            st.subheader("Uploaded PDF Preview")
    
    if "converter" in st.session_state:
        st.session_state.converter.lib = conversion_package
        st.session_state.converter.input_file = file_path
    else:
        st.session_state.converter = pdf2md.Converter(conversion_package, file_path)
    if st.session_state.converter.has_image_extraction(): 
        create_image_zip_file = st.checkbox("Get image zip file")
        st.session_state.converter.create_image_zip_file = create_image_zip_file

if file_path:
    with st.expander("Preview Input File"):
        preview(st.session_state.converter.input_file)    

if st.button("Convert", type="primary"):
    with st.spinner("Converting..."):
        try:
            st.session_state.converter.convert()
        except Exception as e:
            st.error(f"Conversion failed: {str(e)}")

if st.session_state.converter.md_content:
    with st.expander("Preview Output File"):
        preview(st.session_state.converter.output_file)
        st.markdown(
            st.session_state.converter.get_file_download_link("📥 Download Converted File"), 
            unsafe_allow_html=True
        )

st.markdown("---")
st.markdown("PDF-Markdown Converter v 0.1.2| Made with Streamlit | [git repo](https://github.com/lcalmbach/pdf2md-converter)")