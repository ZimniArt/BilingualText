from deep_translator import GoogleTranslator
import pykakasi
import re
from fpdf import FPDF
from tqdm import tqdm
import time
import os

 #parameters
left_margin = 15
cell_width = 180
batch_size = 7   

source_file = "input.txt"

source_language = 'en'
target_language = 'ja'
needs_furigana = True


script_dir = os.path.dirname(__file__)  
font_address = os.path.join(script_dir, "MPLUSRounded1c-Medium.ttf")
font_name ="font_name"


translator  = GoogleTranslator(source=source_language, target=target_language)

def pdf_setup():
    # PDF setup
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_font( font_name, "", font_address)
    pdf.set_font( font_name, style="", size=12)

    return pdf

def split_into_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in sentences if s]

def batch_list(lst, batch_size):
    for i in range(0, len(lst), batch_size):
        yield lst[i:i + batch_size]


def safe_batch_translate(batch, retries=3, delay=2.0):
    """Translate a batch but never crash. Failed entries return None."""
    for attempt in range(retries):
        try:
            result = translator.translate_batch(batch)
            # deep_translator sometimes returns list with None
            return [r if r else None for r in result]
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print(f"[ERROR] Batch failed permanently, will mark failed items.")
                return [None] * len(batch)

kks = pykakasi.kakasi()

with open(source_file, "r", encoding="utf-8") as f:
    original_text = f.read()

sentences = split_into_sentences(original_text)

    
pdf = pdf_setup()

print("Starting batch translation...\n")

for batch in tqdm(list(batch_list(sentences, batch_size)), desc="Batches", unit="batch"):
    translated_batch = safe_batch_translate(batch)

    for sentence, jp in zip(batch, translated_batch):
    
        if jp is None:
            translated_text = "[Translation failed]"
        else:
            translated_text = jp

        if needs_furigana and jp:
            result = kks.convert(jp)
            furigana_text = " ".join([item['hira'] for item in result])
        else:
            furigana_text = ""

        # --- English ---
        pdf.set_x(left_margin)
        #pdf.set_font(font_name, size=12)
        pdf.multi_cell(cell_width, 8, sentence)

        # --- Furigana ---
        if furigana_text:
            pdf.set_x(left_margin)
           # pdf.set_font(font_name, size=9)
            pdf.multi_cell(cell_width, 8, furigana_text)

        # --- Japanese ---
        pdf.set_x(left_margin)
       # pdf.set_font(font_name, size=14)
        pdf.multi_cell(cell_width, 8, translated_text)

        pdf.ln(5)


pdf.output("translated_text.pdf")
print("\nPDF successfully created")
