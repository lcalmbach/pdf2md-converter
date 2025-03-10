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
import subprocess
import os
import pymupdf4llm
from docling.document_converter import DocumentConverter

class Converter():
    def __init__(self, lib: str, input_path):
        self.lib = lib
        self.input_path = input_path
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".md")
        output_file.close()
        self.output_path = output_file.name

    def pymupdf_conversion(self):
        """Convert PDF to markdown using PyMuPDF (fitz) for text extraction and custom formatting"""
        doc = fitz.open(self.input_path)
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
                                
                                text_blocks.append({
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
        md_content = re.sub(r'\n{3,}', '\n\n', md_content)
        return md_content

    def pymupdf4llm_conversion(self):
        """Convert PDF to markdown using pymupdf4llm"""
        try:
            md_content = pymupdf4llm.to_markdown(self.input_path)
            return md_content
        except Exception as e:
            st.error(f"pymupdf4llm conversion error: {str(e)}")
            return f"Conversion with pymupdf4llm failed: {str(e)}"

    def docling_conversion(self):
        """Convert PDF to markdown using docling"""
        try:
            doc = DocumentConverter()
            conversion_result = doc.convert(self.input_path)
            md_content = conversion_result.document.export_to_markdown()
            return md_content

        except Exception as e:
            st.error(f"docling conversion error: {str(e)}")
            return f"Conversion with docling failed: {str(e)}"

    def convert(self):
        md_content = ""
        if self.lib.lower() == 'docling':
            md_content = self.docling_conversion()
        elif self.lib.lower() == 'pymupdf4llm':
            md_content = self.pymupdf4llm_conversion()
        else:
            md_content = self.pymupdf_conversion()
        with open(self.output_path, "w") as f:
            f.write(md_content)