import os
import re
import csv
import logging
import urllib.request
from typing import List, Dict, Any
from app.rag.vectorstore import vector_store

logger = logging.getLogger(__name__)

class DocumentIngestor:
    @staticmethod
    def clean_text(text: str) -> str:
        """Standardize text formatting by removing double spaces and consecutive newlines."""
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 600, chunk_overlap: int = 150) -> List[str]:
        """Split a long text string into overlapping chunks."""
        chunks = []
        if not text:
            return chunks
            
        words = text.split(" ")
        current_chunk = []
        current_len = 0
        
        for word in words:
            current_chunk.append(word)
            current_len += len(word) + 1  # count word + space
            if current_len >= chunk_size:
                chunks.append(" ".join(current_chunk))
                # Backtrack for overlap: keep roughly chunk_overlap characters worth of words at the end
                overlap_chars = 0
                overlap_words = []
                for w in reversed(current_chunk):
                    overlap_words.insert(0, w)
                    overlap_chars += len(w) + 1
                    if overlap_chars >= chunk_overlap:
                        break
                current_chunk = overlap_words
                current_len = overlap_chars
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return [c for c in chunks if len(c.strip()) > 10]

    def ingest_txt(self, file_path: str, filename: str) -> int:
        """Read and ingest a text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            chunks = self.chunk_text(content)
            metadatas = [{"source": filename, "type": "txt"} for _ in chunks]
            vector_store.add_documents(chunks, metadatas)
            return len(chunks)
        except Exception as e:
            logger.error(f"Error ingesting text file {filename}: {e}")
            raise e

    def ingest_csv(self, file_path: str, filename: str) -> int:
        """Read and ingest a CSV database of customer FAQs or tabular data."""
        try:
            chunks = []
            metadatas = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader):
                    # Compile row contents into a structured document text
                    row_content = ", ".join([f"{k}: {v}" for k, v in row.items() if v])
                    chunks.append(row_content)
                    metadatas.append({"source": filename, "type": "csv", "row_index": idx})
            
            vector_store.add_documents(chunks, metadatas)
            return len(chunks)
        except Exception as e:
            logger.error(f"Error ingesting CSV file {filename}: {e}")
            raise e

    def ingest_pdf(self, file_path: str, filename: str) -> int:
        """Read and ingest a PDF file using pypdf."""
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            full_text = []
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    full_text.append(text)
            
            combined_text = "\n".join(full_text)
            chunks = self.chunk_text(combined_text)
            metadatas = [{"source": filename, "type": "pdf"} for _ in chunks]
            vector_store.add_documents(chunks, metadatas)
            return len(chunks)
        except ImportError:
            logger.warning("pypdf library not found. Reading raw file structure as mock text.")
            return self.ingest_txt(file_path, filename)
        except Exception as e:
            logger.error(f"Error ingesting PDF file {filename}: {e}")
            raise e

    def ingest_docx(self, file_path: str, filename: str) -> int:
        """Read and ingest a Microsoft Word document (.docx)."""
        try:
            import docx2txt
            text = docx2txt.process(file_path)
            chunks = self.chunk_text(text)
            metadatas = [{"source": filename, "type": "docx"} for _ in chunks]
            vector_store.add_documents(chunks, metadatas)
            return len(chunks)
        except ImportError:
            logger.warning("docx2txt library not found. Reading raw file structure as mock text.")
            return self.ingest_txt(file_path, filename)
        except Exception as e:
            logger.error(f"Error ingesting DOCX file {filename}: {e}")
            raise e

    def ingest_url(self, url: str) -> int:
        """Scrape webpage content, clean HTML tags, and ingest."""
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8')
                
            # Basic regex-based HTML tag cleaning to avoid external BeautifulSoup dependency
            text = re.sub(r'<script.*?</script>', ' ', html, flags=re.DOTALL)
            text = re.sub(r'<style.*?</style>', ' ', text, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            clean_content = self.clean_text(text)
            
            chunks = self.chunk_text(clean_content)
            metadatas = [{"source": url, "type": "url"} for _ in chunks]
            vector_store.add_documents(chunks, metadatas)
            return len(chunks)
        except Exception as e:
            logger.error(f"Error scraping and ingesting URL {url}: {e}")
            raise e

    def ingest_file(self, file_path: str, original_filename: str) -> int:
        """Route to appropriate loader by file extension."""
        ext = os.path.splitext(original_filename)[1].lower()
        if ext == '.txt':
            return self.ingest_txt(file_path, original_filename)
        elif ext == '.csv':
            return self.ingest_csv(file_path, original_filename)
        elif ext == '.pdf':
            return self.ingest_pdf(file_path, original_filename)
        elif ext in ['.docx', '.doc']:
            return self.ingest_docx(file_path, original_filename)
        else:
            # Fallback for unrecognized formats
            return self.ingest_txt(file_path, original_filename)

# Instantiate singleton ingestor
document_ingestor = DocumentIngestor()
