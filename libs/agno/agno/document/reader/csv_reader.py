import asyncio
import csv
import io
import os
from pathlib import Path
from time import sleep
from typing import IO, Any, List, Union
from urllib.parse import urlparse

try:
    import aiofiles
except ImportError:
    raise ImportError("`aiofiles` not installed. Please install it with `pip install aiofiles`")

from agno.document.base import Document
from agno.document.reader.base import Reader
from agno.utils.log import logger


class CSVReader(Reader):
    """Reader for CSV files"""

    def read(self, file: Union[Path, IO[Any]], delimiter: str = ",", quotechar: str = '"') -> List[Document]:
        try:
            if isinstance(file, Path):
                if not file.exists():
                    raise FileNotFoundError(f"Could not find file: {file}")
                logger.info(f"Reading: {file}")
                file_content = file.open(newline="", mode="r", encoding="utf-8")
            else:
                logger.info(f"Reading uploaded file: {file.name}")
                file.seek(0)
                file_content = io.StringIO(file.read().decode("utf-8"))  # type: ignore

            csv_name = Path(file.name).stem if isinstance(file, Path) else file.name.split(".")[0]
            csv_content = ""
            with file_content as csvfile:
                csv_reader = csv.reader(csvfile, delimiter=delimiter, quotechar=quotechar)
                for row in csv_reader:
                    csv_content += ", ".join(row) + "\n"

            documents = [
                Document(
                    name=csv_name,
                    id=csv_name,
                    content=csv_content,
                )
            ]
            if self.chunk:
                chunked_documents = []
                for document in documents:
                    chunked_documents.extend(self.chunk_document(document))
                return chunked_documents
            return documents
        except Exception as e:
            logger.error(f"Error reading: {file.name if isinstance(file, IO) else file}: {e}")
            return []

    async def async_read(
        self, file: Union[Path, IO[Any]], delimiter: str = ",", quotechar: str = '"', page_size: int = 1000
    ) -> List[Document]:
        """
        Read a CSV file asynchronously, processing batches of rows concurrently.

        Args:
            file: Path or file-like object
            delimiter: CSV delimiter
            quotechar: CSV quote character
            page_size: Number of rows per page

        Returns:
            List of Document objects
        """
        try:
            if isinstance(file, Path):
                if not file.exists():
                    raise FileNotFoundError(f"Could not find file: {file}")
                logger.info(f"Reading async: {file}")
                async with aiofiles.open(file, mode="r", encoding="utf-8", newline="") as file_content:
                    content = await file_content.read()
                    file_content_io = io.StringIO(content)
            else:
                logger.info(f"Reading uploaded file async: {file.name}")
                file.seek(0)
                file_content_io = io.StringIO(file.read().decode("utf-8"))  # type: ignore

            csv_name = Path(file.name).stem if isinstance(file, Path) else file.name.split(".")[0]

            # First pass to count rows and detect if the file is small enough for single-document mode
            file_content_io.seek(0)
            csv_reader = csv.reader(file_content_io, delimiter=delimiter, quotechar=quotechar)
            rows = list(csv_reader)
            total_rows = len(rows)

            # For very small files, just create a single document
            if total_rows <= 10:  # Adjust threshold as needed
                csv_content = " ".join(", ".join(row) for row in rows)
                documents = [
                    Document(
                        name=csv_name,
                        id=csv_name,
                        content=csv_content,
                    )
                ]
            else:
                # Divide rows into pages
                pages = []
                for i in range(0, total_rows, page_size):
                    pages.append(rows[i : i + page_size])

                async def _process_page(page_number: int, page_rows: List[List[str]]) -> Document:
                    """Process a page of rows into a document"""
                    start_row = (page_number - 1) * page_size + 1
                    page_content = " ".join(", ".join(row) for row in page_rows)

                    return Document(
                        name=csv_name,
                        id=f"{csv_name}_page{page_number}",
                        meta_data={"page": page_number, "start_row": start_row, "rows": len(page_rows)},
                        content=page_content,
                    )

                # Process pages in parallel
                documents = await asyncio.gather(
                    *[_process_page(page_number, page) for page_number, page in enumerate(pages, start=1)]
                )

            if self.chunk:
                documents = await self.chunk_documents_async(documents)

            return documents
        except Exception as e:
            logger.error(f"Error reading async: {file.name if isinstance(file, IO) else file}: {e}")
            return []


class CSVUrlReader(Reader):
    """Reader for CSV files"""

    def read(self, url: str) -> List[Document]:
        if not url:
            raise ValueError("No URL provided")

        try:
            import httpx
        except ImportError:
            raise ImportError("`httpx` not installed")

        logger.info(f"Reading: {url}")
        # Retry the request up to 3 times with exponential backoff
        for attempt in range(3):
            try:
                response = httpx.get(url)
                break
            except httpx.RequestError as e:
                if attempt == 2:  # Last attempt
                    logger.error(f"Failed to fetch CSV after 3 attempts: {e}")
                    raise
                wait_time = 2**attempt  # Exponential backoff: 1, 2, 4 seconds
                logger.warning(f"Request failed, retrying in {wait_time} seconds...")
                sleep(wait_time)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise

        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path) or "data.csv"

        file_obj = io.BytesIO(response.content)
        file_obj.name = filename

        documents = CSVReader().read(file=file_obj)

        file_obj.close()

        return documents

    async def async_read(self, url: str) -> List[Document]:
        if not url:
            raise ValueError("No URL provided")

        try:
            import httpx
        except ImportError:
            raise ImportError("`httpx` not installed")

        logger.info(f"Reading async: {url}")

        async def _fetch_with_retry(client: httpx.AsyncClient) -> httpx.Response:
            # Retry the request up to 3 times with exponential backoff
            for attempt in range(3):
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response
                except httpx.RequestError as e:
                    if attempt == 2:  # Last attempt
                        logger.error(f"Failed to fetch CSV after 3 attempts: {e}")
                        raise
                    wait_time = 2**attempt  # Exponential backoff: 1, 2, 4 seconds
                    logger.warning(f"Request failed, retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
                    raise

        async with httpx.AsyncClient() as client:
            response = await _fetch_with_retry(client)

            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path) or "data.csv"

            file_obj = io.BytesIO(response.content)
            file_obj.name = filename

            # Use the async version of CSVReader
            documents = await CSVReader().async_read(file=file_obj)

            file_obj.close()

            return documents
