import docx
doc = docx.Document(r'c:\Users\G Mukesh Vardhan\OneDrive\Desktop\My Project\Major  Project Documentation Guide Lines-4-4-2025 (1) (1).docx')
for p in doc.paragraphs:
    if p.text.strip():
        print(p.text)
