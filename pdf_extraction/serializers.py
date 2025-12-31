from rest_framework import serializers


class PDFTextExtractionSerializer(serializers.Serializer):
    """Serializer for PDF text extraction"""
    pdf_file = serializers.FileField(
        required=True,
        help_text="PDF file to extract text from"
    )

    def validate_pdf_file(self, value):
        """Validate that the uploaded file is a PDF"""
        if not value.name.endswith('.pdf'):
            raise serializers.ValidationError("File must be a PDF")

        # Check file size (limit to 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size must not exceed 10MB")

        return value


class PDFTextExtractionResponseSerializer(serializers.Serializer):
    """Serializer for PDF text extraction response"""
    text = serializers.CharField(help_text="Extracted text from PDF")
    page_count = serializers.IntegerField(help_text="Number of pages in PDF")
    character_count = serializers.IntegerField(help_text="Total characters extracted")
