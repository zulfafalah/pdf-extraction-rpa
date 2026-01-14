import logging
import tempfile
import os
from io import BytesIO
import json
import openpyxl
from openpyxl import Workbook
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .export_excel import create_simple_export

import pdfplumber

from .serializers import PDFTextExtractionSerializer, PDFTextExtractionResponseSerializer
from .services import PDFExtractionService


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # Skip CSRF check

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


@method_decorator(csrf_exempt, name='dispatch')
class PDFUploadAndExportView(APIView):
    """
    API endpoint untuk upload PDF, ekstrak data regex, dan return JSON + Excel
    """
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, *args, **kwargs):
        """
        Upload PDF, ekstrak data, dan return hasil + Excel file
        """
        # Validasi file
        if 'pdf_file' not in request.FILES:
            return Response(
                {'error': 'File PDF diperlukan'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pdf_file = request.FILES['pdf_file']
        customer_name = request.data.get('customer_name', 'Food Hall')
        extraction_type = request.data.get('extraction_type', 'customer')
        
        # Validasi format file
        if not pdf_file.name.lower().endswith('.pdf'):
            return Response(
                {'error': 'File harus berformat PDF'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        temp_file_path = None
        try:
            # Simpan file sementara
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                for chunk in pdf_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            # Proses ekstraksi menggunakan PDFExtractionService
            service = PDFExtractionService()
            
            # Ekstrak teks dari PDF
            extracted_text = service.extract_text_from_pdf(temp_file_path, 'regex')
            
            # Ekstrak data menggunakan regex
            extracted_data = service.extract_data_using_regex(extracted_text, customer_name, extraction_type)
            
            logger.info(f"Successfully extracted data for {pdf_file.name}: {extracted_data}")
            
            return Response({
                'success': True,
                'filename': pdf_file.name,
                'customer_name': customer_name,
                'extraction_type': extraction_type,
                'extracted_data': extracted_data
            })
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        finally:
            # Hapus file sementara
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.error(f"Error cleaning up temp file: {str(e)}")


@method_decorator(csrf_exempt, name='dispatch')
class ExportToExcelView(APIView):
    """
    API endpoint untuk export extracted data ke file Excel
    """
    permission_classes = [AllowAny]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, *args, **kwargs):
        extracted_data = request.data.get('extracted_data')

        if not extracted_data:
            return Response(
                {'error': 'Data diperlukan'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if isinstance(extracted_data, str):
            try:
                extracted_data = json.loads(extracted_data)
            except json.JSONDecodeError:
                return Response(
                    {'error': 'Format JSON tidak valid'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        try:
            excel_file = create_simple_export(extracted_data)

            response = HttpResponse(
                excel_file.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="extraction_results.xlsx"'
            return response

        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class CustomerListView(APIView):
    """
    API endpoint untuk mendapatkan daftar customer/PPH berdasarkan extraction_type
    """
    permission_classes = [AllowAny]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def get(self, request, *args, **kwargs):
        """
        Return list of customers based on extraction_type
        """
        extraction_type = request.query_params.get('extraction_type', 'customer')
        
        try:
            # Import models di dalam fungsi untuk avoid circular import
            from regex_engine.models import CustomerRegexRule, PPHRegexRule
            
            if extraction_type in ['pph_masukan', 'pph_keluaran']:
                # Untuk PPH, ambil dari PPHRegexRule
                pph_rules = PPHRegexRule.objects.values_list('pph_name', flat=True).distinct()
                customers = list(pph_rules)
            else:
                # Customer extraction - ambil dari CustomerRegexRule
                customers = list(CustomerRegexRule.objects.values_list(
                    'customer_name', flat=True
                ).distinct())
                
                # Jika tidak ada, gunakan default
                if not customers:
                    customers = ['Food Hall']
            
            return Response({
                'success': True,
                'extraction_type': extraction_type,
                'customers': customers
            })
            
        except Exception as e:
            logger.error(f"Error getting customer list: {str(e)}")
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class UploadAndExportMultiView(APIView):
    """
    API endpoint untuk upload multiple PDF files dan return JSON + Excel
    """
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [AllowAny]
    authentication_classes = [CsrfExemptSessionAuthentication]

    def post(self, request, *args, **kwargs):
        """
        Upload multiple PDFs, ekstrak data, dan return hasil + Excel file
        """
        pdf_files = request.FILES.getlist('pdf_files')
        customer_name = request.data.get('customer_name', 'Food Hall')
        extraction_type = request.data.get('extraction_type', 'customer')
        
        if not pdf_files:
            return Response(
                {'error': 'File PDF diperlukan'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = {}
        temp_files = []
        
        try:
            service = PDFExtractionService()
            
            for pdf_file in pdf_files:
                filename = pdf_file.name
                
                if not filename.lower().endswith('.pdf'):
                    results[filename] = {'success': False, 'error': 'Format file bukan PDF'}
                    continue
                
                temp_file_path = None
                try:
                    # Simpan file sementara
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                        for chunk in pdf_file.chunks():
                            temp_file.write(chunk)
                        temp_file_path = temp_file.name
                    temp_files.append(temp_file_path)
                    
                    # Ekstrak teks dan data
                    extracted_text = service.extract_text_from_pdf(temp_file_path, 'regex')
                    extracted_data = service.extract_data_using_regex(
                        extracted_text, customer_name, extraction_type
                    )
                    
                    results[filename] = {
                        'success': True,
                        'customer_name': customer_name,
                        'extracted_data': extracted_data
                    }
                    
                except Exception as e:
                    results[filename] = {'success': False, 'error': str(e)}
            
            return Response({
                'success': True,
                'total_files': len(pdf_files),
                'results': results
            })
            
        finally:
            # Hapus file sementara
            for temp_file_path in temp_files:
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                    except:
                        pass
