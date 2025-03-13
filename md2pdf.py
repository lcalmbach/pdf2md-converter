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
from pdf2image import convert_from_path
import subprocess
import os
from PIL import Image


class Converter():
    def __init__(self, lib: str, input_path):
        self.lib = lib
        self.input_path = input_path
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        output_file.close()
        self.output_path = output_file.name

    
    def pandoc_convert(self):
        """
        Convert a Markdown file to a PDF using Pandoc.
        
        Parameters:
            md_file (str): Path to the input Markdown file.
            pdf_file (str): Path to the output PDF file.
            pdf_engine (str): PDF engine to use (default: xelatex for better font support).
            toc (bool): Whether to include a Table of Contents.
            font (str): Font for the PDF output.
            margin (str): Page margins (default: 1 inch).
        """
        print(os.path.getsize(self.input_path) , os.path.getsize(self.input_path), 123)
        
        # Check if input file is empty
        if os.path.getsize(self.input_path) == 0:
            print("❌ Error: Input file is empty")
        
        pdf_engine="xelatex"
        toc=False
        font="TeX Gyre Termes"
        margin="1in"

        command = [
            "pandoc", self.input_path,
            "-o", self.output_path,
            "--pdf-engine=" + pdf_engine,
            "-V", f"mainfont={font}",
            "-V", f"geometry:margin={margin}"
        ]
        
        if toc:
            command.append("--toc")  # Add table of contents if requested
        
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            return False, f"❌ Error during conversion: {e}"


    def weasy_convert(self):
        """Convert markdown to PDF using WeasyPrint"""
        # Convert markdown to HTML
        # open self.input_path as f: and read conent to md_conent 
        with open(self.input_path, "r") as f:
            md_content = f.read()
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
        html_doc.write_pdf(Path(self.output_path), font_config=font_config)

    
    def convert(self):
        if self.lib.lower() == 'pandoc':
            self.pandoc_convert()
        elif self.lib.lower() == 'weasyprint':
            self.weasy_convert()