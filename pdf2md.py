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
import openai
import pdfplumber

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


    def pdfplumber_conversion(self):
        """Extracts text with headings and tables from a PDF while maintaining structure."""
        structured_text = []
        
        with pdfplumber.open(self.input_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text_blocks = page.extract_words()  # Extract text blocks
                char_data = page.objects.get("char", [])  # Get character-level metadata

                font_sizes = [char["size"] for char in char_data if "size" in char]  # Extract font sizes
                avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 12  # Default to 12 if unknown

                last_font_size = avg_font_size  # Base reference font size

                # Process each word and infer headings based on font size
                for word in text_blocks:
                    text = word["text"]
                    
                    # Find corresponding font size (fallback to avg)
                    word_font_size = next((char["size"] for char in char_data if char["text"] == text), avg_font_size)

                    # Heading detection: If font size is significantly larger than the average, assume heading
                    if word_font_size > avg_font_size * 1.2:  # 20% larger than avg
                        structured_text.append(f"\n# {text}\n")  # Markdown heading
                    else:
                        structured_text.append(text)

                # Extract Tables
                tables = page.extract_tables()
                for table in tables:
                    structured_text.append("\n| " + " | ".join(table[0]) + " |\n")  # Markdown Table Header
                    structured_text.append("|" + " --- |" * len(table[0]))  # Table divider
                    for row in table[1:]:
                        structured_text.append("| " + " | ".join(row) + " |")

                structured_text.append("\n---\n")  # Page separator
        return "\n".join(structured_text)
    
    
    def openai_conversion(self, text):
        """Sends structured text to OpenAI to enhance Markdown formatting."""
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": (
                "You are a Markdown conversion assistant. Your task is to convert the following extracted text into properly formatted Markdown, "
                "preserving ALL content exactly as given. DO NOT summarize, shorten, or omit any details. "
                "Ensure that:\n"
                "- All headings are formatted correctly using `#`, `##`, `###`.\n"
                "- Tables are formatted using Markdown syntax (`| Column1 | Column2 |` with proper dividers).\n"
                "- Lists are converted to `-` for bullet points or `1.` for numbered lists.\n"
                "- Any section breaks, page numbers, and special characters are kept as-is.\n"
                "- Inline formatting (bold, italic) is preserved if present.\n"
                "- Code blocks are wrapped in triple backticks if detected.\n"
                "The goal is to reproduce the document in Markdown EXACTLY as it appears in the extracted text."
            )},
                    {"role": "user", "content": text}]
        )
        markdown_content = response.choices[0].message.content
        return markdown_content

    def convert(self):
        md_content = ""
        if self.lib.lower() == 'docling':
            md_content = self.docling_conversion()
        elif self.lib.lower() == 'pymupdf4llm':
            md_content = self.pymupdf4llm_conversion()
        elif self.lib.lower() == 'pdfplumber+chatgpt4o':
            md_content = self.pdfplumber_conversion()
            md_content = self.openai_conversion(md_content)
        else:
            md_content = self.pymupdf_conversion()
        with open(self.output_path, "w") as f:
            f.write(md_content)