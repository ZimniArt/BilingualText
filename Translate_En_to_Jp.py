from deep_translator import GoogleTranslator
import pykakasi
import re
from fpdf import FPDF
from tqdm import tqdm
import time

kks = pykakasi.kakasi()

def split_sentence(text):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in sentences if s]

def batch_list(lst, batch_size):
    for i in range(0, len(lst), batch_size):
        yield lst[i:i + batch_size]

def safe_batch_translate(batch, retries=3, delay=2.0):
    """Translate a batch but never crash. Failed entries return None."""
    for attempt in range(retries):
        try:
            result = GoogleTranslator(source='en', target='ja').translate_batch(batch)
            # deep_translator sometimes returns list with None
            return [r if r else None for r in result]
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print(f"[ERROR] Batch failed permanently, will mark failed items.")
                return [None] * len(batch)

# ----------------------------------------------------

with open("input.txt", "r", encoding="utf-8") as f:
    english_text = f.read()

sentences = split_sentence(english_text)

# PDF setup
pdf = FPDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)

pdf.add_font("MPLUSRounded1c", "", r"D:\2_projects\7_simplePDF\MPLUSRounded1c-Medium.ttf")
pdf.set_font("MPLUSRounded1c", style="", size=12)

left_margin = 15
cell_width = 180

batch_size = 30   # ← adjust speed vs. stability

# ----------------------------------------------------

print("Starting batch translation...\n")

for batch in tqdm(list(batch_list(sentences, batch_size)), desc="Batches", unit="batch"):
    translated_batch = safe_batch_translate(batch)

    for sentence, jp in zip(batch, translated_batch):
        
        if jp is None:
            japanese_text = "[Translation failed]"
            furigana_text = ""
        else:
            japanese_text = jp
            result = kks.convert(jp)
            furigana_text = " ".join([item['hira'] for item in result])

        # --- English ---
        pdf.set_x(left_margin)
        pdf.set_font("MPLUSRounded1c", size=12)
        pdf.multi_cell(cell_width, 8, sentence)

        # --- Furigana ---
        if furigana_text:
            pdf.set_x(left_margin)
            pdf.set_font("MPLUSRounded1c", size=9)
            pdf.multi_cell(cell_width, 6, furigana_text)

        # --- Japanese ---
        pdf.set_x(left_margin)
        pdf.set_font("MPLUSRounded1c", size=14)
        pdf.multi_cell(cell_width, 10, japanese_text)

        pdf.ln(5)

# ----------------------------------------------------
pdf.output("translated_text.pdf")
print("\nPDF successfully created")
