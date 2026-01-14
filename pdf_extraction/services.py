import logging
from typing import Optional, Dict, Any, List
from django.core.exceptions import ValidationError
from django.db import transaction

import regex_engine
from .models import PDFExtraction, PDFExtractionItem
from regex_engine.models import CustomerRegexRule, PPHRegexRule

logger = logging.getLogger(__name__)


class PDFExtractionService:
    def prosess_extraction(self, extraction_id: int) -> None:
        """Process the PDF extraction for the given extraction ID"""
        try:
            extraction = PDFExtraction.objects.get(id=extraction_id)
        except PDFExtraction.DoesNotExist:
            logger.error(f"PDFExtraction with id {extraction_id} does not exist.")
            return

        pdf_items = extraction.pdf_items.all()
        extraction_type = getattr(extraction, 'extraction_type', 'customer')
        for item in pdf_items:
            self._process_pdf_item(item, extraction.extraction_method, customer_name=extraction.customer_name, extraction_type=extraction_type)

    def _process_pdf_item(self, item: PDFExtractionItem, method: str, customer_name: str, extraction_type: str = 'customer') -> None:
        if method == 'regex':
            text = self.extract_text_from_pdf(item.pdf_file.path, method)
            extracted_data = self.extract_data_using_regex(text, customer_name, extraction_type)

            # Log the extracted data
            logger.info(f"Extracted data for PDF item {item.id}: {extracted_data}")

            # Save extracted data to result_data field without triggering signals
            from django.db.models.signals import post_save
            from .signals import handle_pdf_extraction_item_save

            post_save.disconnect(handle_pdf_extraction_item_save, sender=PDFExtractionItem)
            item.result_data = extracted_data
            item.save(update_fields=['result_data', 'updated_at'])
            post_save.connect(handle_pdf_extraction_item_save, sender=PDFExtractionItem)

            logger.info(f"Successfully saved extracted data for PDF item {item.id}")

        if method == 'ai':
            pass  #

    @staticmethod
    def extract_text_from_pdf(file_path: str, method: str) -> str:
        """Extract text from PDF using pdfplumber, this function will be return extracted text"""
        import pdfplumber

        try:
            extracted_text = ""

            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    logger.debug(f"Processing page {page_num} of {len(pdf.pages)}")
                    page_text = page.extract_text()

                    if page_text:
                        extracted_text += page_text + "\n"
                    else:
                        logger.warning(f"No text found on page {page_num}")

            if not extracted_text.strip():
                logger.warning(f"No text could be extracted from {file_path}")
                return ""

            logger.info(f"Successfully extracted {len(extracted_text)} characters from {file_path}")
            return extracted_text.strip()

        except FileNotFoundError:
            logger.error(f"PDF file not found: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            raise

    def extract_data_using_regex(self, text, customer_name, extraction_type='customer'):
        """Extract data from text using provided regex rules"""
        # Extract header and item data separately based on extraction_type
        if extraction_type in ['pph_masukan', 'pph_keluaran']:
            header_data = self.extract_header_data_pph(text, extraction_type)
            item_data = self.extract_item_data_pph(text, extraction_type)
        else:
            header_data = self.extract_header_data(text, customer_name)
            item_data = self.extract_item_data(text, customer_name)

        # Combine both data
        extracted_data = {
            **header_data,
            'items': item_data
        }

        return extracted_data

    def extract_header_data_pph(self, text: str, pph_type: str) -> Dict[str, Any]:
        """Extract header data from text using PPHRegexRule"""
        import re

        # Get PPH rules based on type (is_item_field=False)
        pph_rules = PPHRegexRule.objects.filter(
            pph_name=pph_type,
            is_item_field=False
        )

        if not pph_rules.exists():
            logger.warning(f"No PPH rules found for type: {pph_type}")
            return {}

        extracted_data = {}

        for rule in pph_rules:
            field_name = rule.field_name
            pattern = rule.regex_pattern
            group_num = rule.regex_group

            try:
                match = re.search(pattern, text, re.MULTILINE | re.DOTALL)

                if match:
                    extracted_value = match.group(group_num)
                    extracted_data[field_name] = extracted_value.strip()
                    logger.info(f"PPH {pph_type} - header '{field_name}': {extracted_value.strip()}")
                else:
                    logger.warning(f"No match for PPH header field '{field_name}'")
                    extracted_data[field_name] = None

            except re.error as e:
                logger.error(f"Invalid regex pattern for PPH header '{field_name}': {pattern}. Error: {str(e)}")
                extracted_data[field_name] = None
            except IndexError:
                logger.error(f"Group {group_num} not found in PPH regex match for '{field_name}'")
                extracted_data[field_name] = None
            except Exception as e:
                logger.error(f"Unexpected error extracting PPH header '{field_name}': {str(e)}")
                extracted_data[field_name] = None

        return extracted_data

    def extract_item_data_pph(self, text: str, pph_type: str) -> List[Dict[str, Any]]:
        """Extract item data from text using PPHRegexRule where is_item_field=True"""
        import re

        # Get item PPH rules only (is_item_field=True)
        item_rules = PPHRegexRule.objects.filter(
            pph_name=pph_type,
            is_item_field=True
        ).order_by('id')

        if not item_rules.exists():
            logger.warning(f"No PPH item rules found for type: {pph_type}")
            return []

        items = []

        for rule in item_rules:
            field_name = rule.field_name
            group_num = rule.regex_group

            # Collect all available patterns in order
            patterns_to_try = []
            if rule.regex_pattern:
                patterns_to_try.append(('regex_pattern', rule.regex_pattern))
            if rule.regex_pattern_v2:
                patterns_to_try.append(('regex_pattern_v2', rule.regex_pattern_v2))
            if rule.regex_pattern_v3:
                patterns_to_try.append(('regex_pattern_v3', rule.regex_pattern_v3))

            if not patterns_to_try:
                logger.warning(f"No patterns available for PPH field '{field_name}'")
                continue

            matched = False
            matches_found = []

            # Try each pattern in order until we get matches
            for pattern_name, pattern in patterns_to_try:
                try:
                    matches = list(re.finditer(pattern, text, re.MULTILINE | re.DOTALL))

                    if matches:
                        matches_found = matches
                        logger.info(f"PPH {pph_type} - field '{field_name}' matched using {pattern_name} with {len(matches)} items")
                        matched = True
                        break
                    else:
                        logger.debug(f"No matches found for PPH field '{field_name}' using {pattern_name}, trying next...")

                except re.error as e:
                    logger.error(f"Invalid PPH regex pattern ({pattern_name}) for '{field_name}': {pattern}. Error: {str(e)}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error with PPH pattern ({pattern_name}) for '{field_name}': {str(e)}")
                    continue

            # Process the matches if found
            if matched and matches_found:
                try:
                    for match_index, match in enumerate(matches_found):
                        groups = match.groups()

                        while len(items) <= match_index:
                            items.append({})

                        if len(groups) >= group_num:
                            extracted_value = groups[group_num - 1]
                            items[match_index][field_name] = extracted_value.strip() if extracted_value else None
                            logger.info(f"PPH {pph_type} - item {match_index + 1} '{field_name}': {extracted_value.strip() if extracted_value else None}")
                        else:
                            items[match_index][field_name] = None
                            logger.warning(f"Group {group_num} not found for PPH item {match_index + 1} '{field_name}'")

                except Exception as e:
                    logger.error(f"Error processing PPH matches for '{field_name}': {str(e)}")
            else:
                logger.warning(f"No items found for PPH field '{field_name}' after trying all patterns")

        logger.info(f"PPH {pph_type} - Total items extracted: {len(items)}")
        return items

    def extract_header_data(self, text: str, customer_name: str) -> Dict[str, Any]:
        """Extract header data from text using regex rules where is_item_field=False"""
        import re

        # Get header regex rules only (is_item_field=False)
        header_rules = CustomerRegexRule.objects.filter(
            customer_name=customer_name,
            is_item_field=False
        )

        if not header_rules.exists():
            logger.warning(f"No header regex rules found for customer: {customer_name}")
            return {}

        extracted_data = {}

        for rule in header_rules:
            field_name = rule.field_name
            pattern = rule.regex_pattern
            group_num = rule.regex_group

            try:
                match = re.search(pattern, text, re.MULTILINE | re.DOTALL)

                if match:
                    # Extract the value using the specified group number
                    extracted_value = match.group(group_num)

                    # Clean up the extracted value (strip whitespace)
                    extracted_data[field_name] = extracted_value.strip()

                    logger.info(f"Successfully extracted header field '{field_name}': {extracted_value.strip()}")
                else:
                    logger.warning(f"No match found for header field '{field_name}' with pattern: {pattern}")
                    extracted_data[field_name] = None

            except re.error as e:
                logger.error(f"Invalid regex pattern for header field '{field_name}': {pattern}. Error: {str(e)}")
                extracted_data[field_name] = None
            except IndexError:
                logger.error(f"Group {group_num} not found in regex match for header field '{field_name}'")
                extracted_data[field_name] = None
            except Exception as e:
                logger.error(f"Unexpected error extracting header field '{field_name}': {str(e)}")
                extracted_data[field_name] = None

        return extracted_data

    def extract_item_data(self, text: str, customer_name: str) -> List[Dict[str, Any]]:
        """Extract item data from text using regex rules where is_item_field=True"""
        import re

        # Get item regex rules only (is_item_field=True)
        item_rules = CustomerRegexRule.objects.filter(
            customer_name=customer_name,
            is_item_field=True
        ).order_by('id')

        if not item_rules.exists():
            logger.warning(f"No item regex rules found for customer: {customer_name}")
            return []

        items = []

        for rule in item_rules:
            field_name = rule.field_name
            group_num = rule.regex_group

            # Collect all available patterns in order
            patterns_to_try = []
            if rule.regex_pattern:
                patterns_to_try.append(('regex_pattern', rule.regex_pattern))
            if rule.regex_pattern_v2:
                patterns_to_try.append(('regex_pattern_v2', rule.regex_pattern_v2))
            if rule.regex_pattern_v3:
                patterns_to_try.append(('regex_pattern_v3', rule.regex_pattern_v3))

            if not patterns_to_try:
                logger.warning(f"No patterns available for field '{field_name}'")
                continue

            matched = False
            matches_found = []

            # Try each pattern in order until we get matches
            for pattern_name, pattern in patterns_to_try:
                try:
                    # Use finditer to get all matches for items
                    matches = list(re.finditer(pattern, text, re.MULTILINE | re.DOTALL))

                    if matches:
                        matches_found = matches
                        logger.info(f"Field '{field_name}' matched using {pattern_name} with {len(matches)} items")
                        matched = True
                        break  # Stop trying other patterns once we get a match
                    else:
                        logger.debug(f"No matches found for field '{field_name}' using {pattern_name}, trying next pattern...")

                except re.error as e:
                    logger.error(f"Invalid regex pattern ({pattern_name}) for field '{field_name}': {pattern}. Error: {str(e)}")
                    continue  # Try next pattern
                except Exception as e:
                    logger.error(f"Unexpected error with pattern ({pattern_name}) for field '{field_name}': {str(e)}")
                    continue  # Try next pattern

            # Process the matches if found
            if matched and matches_found:
                try:
                    for match_index, match in enumerate(matches_found):
                        # Extract all groups from the match
                        groups = match.groups()

                        # Ensure we have enough items in the list
                        while len(items) <= match_index:
                            items.append({})

                        # Extract the value using the specified group number
                        if len(groups) >= group_num:
                            extracted_value = groups[group_num - 1]
                            items[match_index][field_name] = extracted_value.strip() if extracted_value else None
                            logger.info(f"Extracted item {match_index + 1} - '{field_name}': {extracted_value.strip() if extracted_value else None}")
                        else:
                            items[match_index][field_name] = None
                            logger.warning(f"Group {group_num} not found for item {match_index + 1} - '{field_name}'")

                except Exception as e:
                    logger.error(f"Error processing matches for field '{field_name}': {str(e)}")
            else:
                logger.warning(f"No items found for field '{field_name}' after trying all available patterns")

        logger.info(f"Total items extracted: {len(items)}")
        return items


