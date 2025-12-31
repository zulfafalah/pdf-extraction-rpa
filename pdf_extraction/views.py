import logging
import tempfile
import os
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

import pdfplumber

from .serializers import PDFTextExtractionSerializer, PDFTextExtractionResponseSerializer

logger = logging.getLogger(__name__)


class PDFTextExtractionView(APIView):
    """
    API endpoint to extract text from PDF files using pdfplumber
    No authentication required
    Returns a downloadable .txt file with raw extracted text
    """
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]  # No authentication required

    @extend_schema(
        request=PDFTextExtractionSerializer,
        responses={200: PDFTextExtractionResponseSerializer},
        description="Upload a PDF file and download extracted text as .txt file",
        tags=["PDF Extraction"]
    )
    def post(self, request, *args, **kwargs):
        """
        Extract text from uploaded PDF file and return as downloadable .txt file

        Args:
            request: HTTP request containing PDF file

        Returns:
            HttpResponse with text/plain content for download
        """
        serializer = PDFTextExtractionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        pdf_file = serializer.validated_data['pdf_file']

        # Get original filename without extension
        original_filename = os.path.splitext(pdf_file.name)[0]

        # Create a temporary file to save the uploaded PDF
        temp_file = None
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                for chunk in pdf_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            # Extract text from PDF
            extracted_text = ""
            page_count = 0

            with pdfplumber.open(temp_file_path) as pdf:
                page_count = len(pdf.pages)

                for page_num, page in enumerate(pdf.pages, start=1):
                    logger.debug(f"Processing page {page_num} of {page_count}")
                    page_text = page.extract_text()

                    if page_text:
                        # Add raw text as-is from pdfplumber
                        extracted_text += page_text + "\n"
                    else:
                        logger.warning(f"No text found on page {page_num}")

            if not extracted_text.strip():
                logger.warning(f"No text could be extracted from the PDF")
                return Response(
                    {"error": "No text could be extracted from the PDF"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            logger.info(f"Successfully extracted {len(extracted_text)} characters from PDF with {page_count} pages")

            response = HttpResponse(extracted_text, content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{original_filename}_extracted.txt"'

            return response

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return Response(
                {"error": f"Error processing PDF: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    logger.debug(f"Cleaned up temporary file: {temp_file_path}")
                except Exception as e:
                    logger.error(f"Error cleaning up temporary file: {str(e)}")
