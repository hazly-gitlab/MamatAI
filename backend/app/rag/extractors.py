import os
import pandas as pd
from pypdf import PdfReader
from docx import Document as DocxDocument

def extract_text_from_pdf(filepath: str) -> str:
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_text_from_docx(filepath: str) -> str:
    try:
        doc = DocxDocument(filepath)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        return f"Error reading DOCX: {str(e)}"

def extract_text_from_xlsx(filepath: str) -> str:
    try:
        xls = pd.ExcelFile(filepath)
        text = ""
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            text += f"Sheet: {sheet_name}\n" + df.to_string() + "\n"
        return text
    except Exception as e:
        return f"Error reading Excel file: {str(e)}"

def extract_text_from_csv(filepath: str) -> str:
    try:
        df = pd.read_csv(filepath)
        return df.to_string()
    except Exception as e:
        return f"Error reading CSV: {str(e)}"

def extract_text_from_file(filepath: str, file_type: str) -> str:
    ext = file_type.lower() or os.path.splitext(filepath)[1].lower()

    if "pdf" in ext:
        return extract_text_from_pdf(filepath)
    elif "docx" in ext:
        return extract_text_from_docx(filepath)
    elif "xlsx" in ext or "xls" in ext:
        return extract_text_from_xlsx(filepath)
    elif "csv" in ext:
        return extract_text_from_csv(filepath)
    else:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            return f"Error reading plain text file: {str(e)}"
