"""
Servicio centralizado para partición, lectura y guardado de archivos PDF locales.
"""
import os
from pypdf import PdfReader, PdfWriter
from core.logger import get_logger, log_error

logger = get_logger("PdfService")

class PdfService:
    @staticmethod
    def extract_pages(
        pdf_path: str,
        output_dir: str = "pdfs_locales",
        prefix: str = "documento",
        start_page: int = 1
    ) -> list[dict]:
        """
        Divide un archivo PDF en páginas individuales y las guarda en el directorio especificado.
        
        Args:
            pdf_path: Ruta al archivo PDF de entrada.
            output_dir: Carpeta destino.
            prefix: Prefijo del nombre de archivo.
            start_page: Número de página inicial a considerar.
            
        Returns:
            Lista de diccionarios con metadatos de las páginas generadas:
            [{"page_number": int, "file_path": str, "total_pages": int}]
        """
        if not os.path.exists(pdf_path):
            logger.error(f"El archivo PDF no existe: {pdf_path}")
            return []

        os.makedirs(output_dir, exist_ok=True)
        results = []

        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)

            for i in range(total_pages):
                page_num = i + 1
                if start_page > 0 and page_num < start_page:
                    continue

                writer = PdfWriter()
                writer.add_page(reader.pages[i])

                filename = f"{prefix}_Pag_{page_num}.pdf"
                dest_path = os.path.join(output_dir, filename)

                with open(dest_path, "wb") as f:
                    writer.write(f)

                results.append({
                    "page_number": page_num,
                    "file_path": dest_path,
                    "total_pages": total_pages
                })

            logger.info(f"PDF dividido exitosamente: {len(results)} páginas generadas desde {pdf_path}")
            return results
        except Exception as ex:
            log_error(f"PdfService.extract_pages({pdf_path})", ex)
            return []
