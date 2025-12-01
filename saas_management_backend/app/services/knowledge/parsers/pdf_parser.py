import io
import logging
from pypdf import PdfReader
from fastapi import UploadFile, HTTPException

logger = logging.getLogger("knowledge")

class PDFParser:
    @staticmethod
    async def parse(file: UploadFile) -> str:
        # 1. Security: Magic Number Validation
        # Read first 4 bytes to verify it's actually a PDF, not a renamed .exe
        head = await file.read(4)
        if head != b'%PDF':
            await file.seek(0)
            raise HTTPException(status_code=400, detail="Invalid file header. Not a PDF.")
        
        await file.seek(0)
        content = await file.read()
        
        try:
            pdf_stream = io.BytesIO(content)
            reader = PdfReader(pdf_stream)
            
            # 2. Enterprise: Metadata Extraction
            # Extract title/author to improve search relevance later
            meta = reader.metadata
            title = meta.title if meta and meta.title else "Untitled"
            
            text = []
            for i, page in enumerate(reader.pages):
                extracted = page.extract_text()
                if extracted:
                    # Clean up layout artifacts
                    cleaned = extracted.replace('\xa0', ' ').strip()
                    if len(cleaned) > 50: # Skip empty/nav pages
                        text.append(cleaned)
            
            if not text:
                raise ValueError("PDF contains no extractable text (scanned image?). OCR required.")
                
            return "\n\n".join(text)
            
        except Exception as e:
            logger.error(f"PDF Parse Error: {e}")
            raise HTTPException(status_code=422, detail=f"Unreadable PDF: {str(e)}")