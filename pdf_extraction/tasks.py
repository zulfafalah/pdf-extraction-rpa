import logging
from typing import Dict, Any, List
from celery import shared_task
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def save_extraction_to_provider(self, extraction_item_id: int) -> Dict[str, Any]:
    """
    Celery task to save extracted PDF data to RpaCustomerPoHeader and RpaCustomerPoItems.

    This task runs in the background after PDF extraction is complete.
    """
    from .models import PDFExtractionItem
    from providers.models import RpaCustomerPoHeader, RpaCustomerPoItems

    try:
        # Get the extraction item with result_data
        extraction_item = PDFExtractionItem.objects.select_related('pdf_extraction').get(id=extraction_item_id)

        if not extraction_item.result_data:
            logger.warning(f"No result_data found for PDFExtractionItem {extraction_item_id}")
            return {"status": "skipped", "reason": "No result_data available"}

        result_data = extraction_item.result_data
        items_data = result_data.pop('items', [])
        header_data = result_data

        # Get customer_id from the parent extraction
        customer_id = extraction_item.pdf_extraction.customer_id
        customer_name = extraction_item.pdf_extraction.customer_name

        with transaction.atomic(using='providers'):
            # Create the header record
            header = _create_header_record(header_data, customer_id, customer_name)

            # Create item records
            items_created = _create_item_records(items_data, header.id)

            logger.info(
                f"Successfully saved extraction data: Header ID={header.id}, "
                f"Items created={items_created}"
            )

            return {
                "status": "success",
                "header_id": header.id,
                "items_created": items_created,
                "extraction_item_id": extraction_item_id
            }

    except PDFExtractionItem.DoesNotExist:
        logger.error(f"PDFExtractionItem with id {extraction_item_id} does not exist")
        return {"status": "error", "reason": "PDFExtractionItem not found"}
    except Exception as e:
        logger.exception(f"Error saving extraction to provider: {str(e)}")
        # Retry the task on failure
        raise self.retry(exc=e)


def _create_header_record(header_data: Dict[str, Any], customer_id: str, customecustomer_namer_name: str) -> 'RpaCustomerPoHeader':
    """Create a RpaCustomerPoHeader record from extracted data."""
    from providers.models import RpaCustomerPoHeader

    now = timezone.now()

    # Map extracted fields to model fields
    # The field names in header_data should match the regex rule field_names
    header = RpaCustomerPoHeader(
        customer_id=customer_id or header_data.get('customer_id'),
        customer_name= header_data.get('customer_name'),
        customer_pic_po=header_data.get('customer_pic_po'),
        group_customer_id=header_data.get('group_customer_id'),
        group_customer_name=header_data.get('group_customer_name'),
        top_id=header_data.get('top_id'),
        ship_to_customer_name=header_data.get('ship_to_customer_name'),
        ship_to_address=header_data.get('ship_to_address'),
        ship_to_city=header_data.get('ship_to_city'),
        ship_to_postal_code=header_data.get('ship_to_postal_code'),
        ship_to_phone_1=header_data.get('ship_to_phone_1'),
        ship_to_phone_2=header_data.get('ship_to_phone_2'),
        ship_to_pic=header_data.get('ship_to_pic'),
        ship_to_customer_address_id=header_data.get('ship_to_customer_address_id'),
        ship_to_npwp=header_data.get('ship_to_npwp'),
        ship_to_top_id=header_data.get('ship_to_top_id'),
        ship_to_parent_customer_id=header_data.get('ship_to_parent_customer_id'),
        ship_to_sales_origin_id=header_data.get('ship_to_sales_origin_id'),
        ship_to_distribution_channel_id=header_data.get('ship_to_distribution_channel_id'),
        ship_to_division_id=header_data.get('ship_to_division_id'),
        bill_to_customer_address_id=header_data.get('bill_to_customer_address_id'),
        bill_to_customer_name=header_data.get('bill_to_customer_name'),
        bill_to_pic=header_data.get('bill_to_pic'),
        bill_to_address=header_data.get('bill_to_address'),
        bill_to_city=header_data.get('bill_to_city'),
        bill_to_postal_code=header_data.get('bill_to_postal_code'),
        bill_to_phone_1=header_data.get('bill_to_phone_1'),
        bill_to_phone_2=header_data.get('bill_to_phone_2'),
        bill_to_npwp=header_data.get('bill_to_npwp'),
        bill_to_top_id=header_data.get('bill_to_top_id'),
        bill_to_parent_customer_id=header_data.get('bill_to_parent_customer_id'),
        bill_to_type=header_data.get('bill_to_type'),
        bill_to_sales_org_id=header_data.get('bill_to_sales_org_id'),
        bill_to_distribution_channel_id=header_data.get('bill_to_distribution_channel_id'),
        bill_to_division_id=header_data.get('bill_to_division_id'),
        npwp=header_data.get('npwp'),
        created_by=header_data.get('created_by', 'RPA_SYSTEM'),
        updated_by=header_data.get('updated_by', 'RPA_SYSTEM'),
        entry_by=header_data.get('entry_by', 'RPA_SYSTEM'),
        customer_po_no=header_data.get('customer_po_no'),
        tanggal_cetak=_parse_datetime(header_data.get('tanggal_cetak')) or now,
        tanggal_pesan=_parse_datetime(header_data.get('tanggal_pesan')) or now,
        tanggal_kirim=_parse_datetime(header_data.get('tanggal_kirim')) or now,
        expiry_date_po=_parse_datetime(header_data.get('expiry_date_po')) or now,
        jadwal_jam_pengiriman=header_data.get('jadwal_jam_pengiriman'),
        catatan_pengiriman=header_data.get('catatan_pengiriman'),
        top=header_data.get('top'),
        tanggal_order_entry=_parse_datetime(header_data.get('tanggal_order_entry')) or now,
        jam_order_entry=header_data.get('jam_order_entry'),
        vendor_code=header_data.get('vendor_code'),
        discount_po_percentage=_parse_decimal(header_data.get('discount_po_percentage')),
        discount_amount=_parse_decimal(header_data.get('discount_amount')),
        dc_allowance_percentage=_parse_decimal(header_data.get('dc_allowance_percentage')),
        damage_allowance=_parse_decimal(header_data.get('damage_allowance')),
        pay_allowance_percentage=_parse_decimal(header_data.get('pay_allowance_percentage')),
        total_discount_amount=_parse_decimal(header_data.get('total_discount_amount')),
        total_before_discount_amount=_parse_decimal(header_data.get('total_before_discount_amount')),
        total_after_discount_amount=_parse_decimal(header_data.get('total_after_discount_amount')),
        ppn_percentage=_parse_decimal(header_data.get('ppn_percentage')),
        ppn_amount=_parse_decimal(header_data.get('ppn_amount')),
        has_amount=_parse_int(header_data.get('has_amount')),
        total_amount=_parse_decimal(header_data.get('total_amount')),
        scanned_po=header_data.get('scanned_po'),
        status=_parse_int(header_data.get('status', 0)),
        minimum_expiry_date=_parse_datetime(header_data.get('minimum_expiry_date')) or now,
        sales_code=header_data.get('sales_code'),
        customer_po_type=_parse_int(header_data.get('customer_po_type')),
        is_reserve=_parse_int(header_data.get('is_reserve', 0)),
        date_release_so=_parse_datetime(header_data.get('date_release_so')) or now,
        supplier_id=header_data.get('supplier_id'),
        is_full_free=_parse_int(header_data.get('is_full_free', 0)),
        is_cod=_parse_int(header_data.get('is_cod', 0)),
        sales_id=_parse_int(header_data.get('sales_id')),
        sales_name=header_data.get('sales_name'),
    )

    header.save(using='providers')
    logger.info(f"Created RpaCustomerPoHeader with ID: {header.id}")
    return header


def _create_item_records(items_data: List[Dict[str, Any]], header_id: int) -> int:
    """Create RpaCustomerPoItems records from extracted item data."""
    from providers.models import RpaCustomerPoItems

    items_created = 0

    for item_data in items_data:
        try:
            item = RpaCustomerPoItems(
                header_id=header_id,
                sku_cust_id=item_data.get('sku_cust_id'),
                sku_samb=item_data.get('sku_samb'),
                sku_samb_description=item_data.get('sku_samb_description'),
                qty_dipesan=_parse_int(item_data.get('qty_dipesan')),
                qty_in_pcs=_parse_int(item_data.get('qty_in_pcs')),
                uom=item_data.get('uom'),
                uom_id=item_data.get('uom_id'),
                free_goods=_parse_int(item_data.get('free_goods')),
                expiry_date=_parse_datetime(item_data.get('expiry_date')),
                keterangan=item_data.get('keterangan'),
                free_buy=_parse_int(item_data.get('free_buy')),
                free_get=_parse_int(item_data.get('free_get')),
                principle_id=item_data.get('principle_id'),
                disc_1=_parse_decimal(item_data.get('disc_1')),
                disc_2=_parse_decimal(item_data.get('disc_2')),
                disc_3=_parse_decimal(item_data.get('disc_3')),
                disc_4=_parse_decimal(item_data.get('disc_4')),
                rbp_price_carton=_parse_decimal(item_data.get('rbp_price_carton')),
                rbp_price=_parse_decimal(item_data.get('rbp_price')),
                conversion_factor=_parse_int(item_data.get('conversion_factor')),
                amount_customer=_parse_decimal(item_data.get('amount_customer')),
                sku_samb_id=item_data.get('sku_samb_id'),
                master_item_id=item_data.get('master_item_id'),
                tax_code=item_data.get('tax_code'),
                tax_description=item_data.get('tax_description'),
                tax_amount=_parse_decimal(item_data.get('tax_amount')),
                item_group_1=item_data.get('item_group_1'),
                item_group_1_desc=item_data.get('item_group_1_desc'),
                item_group_2=item_data.get('item_group_2'),
                item_group_2_desc=item_data.get('item_group_2_desc'),
                item_group_3=item_data.get('item_group_3'),
                item_group_3_desc=item_data.get('item_group_3_desc'),
                item_group_4=item_data.get('item_group_4'),
                item_group_4_desc=item_data.get('item_group_4_desc'),
                item_group_5=item_data.get('item_group_5'),
                item_group_5_desc=item_data.get('item_group_5_desc'),
                condition_record_number=item_data.get('condition_record_number'),
                qty_pcs_case=_parse_int(item_data.get('qty_pcs_case')),
                created_by=item_data.get('created_by', 'RPA_SYSTEM'),
                updated_by=item_data.get('updated_by', 'RPA_SYSTEM'),
            )
            item.save(using='providers')
            items_created += 1
        except Exception as e:
            logger.error(f"Error creating item record: {str(e)}, item_data: {item_data}")
            continue

    logger.info(f"Created {items_created} RpaCustomerPoItems records for header {header_id}")
    return items_created


def _parse_datetime(value):
    """Parse datetime from various formats."""
    if value is None:
        return None

    from datetime import datetime
    from django.utils import timezone

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        # Try common date formats
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d/%m/%Y',
            '%d-%m-%Y %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(value, fmt)
                return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
            except ValueError:
                continue

    return None


def _parse_decimal(value):
    """Parse decimal from string."""
    if value is None:
        return None

    from decimal import Decimal, InvalidOperation

    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))

    if isinstance(value, str):
        # Clean up the string (remove currency symbols, spaces, etc.)
        cleaned = value.replace(',', '.').replace(' ', '').strip()
        # Remove common currency prefixes
        for prefix in ['Rp', 'IDR', '$', 'USD']:
            cleaned = cleaned.replace(prefix, '')
        cleaned = cleaned.strip()

        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None

    return None


def _parse_int(value):
    """Parse integer from string."""
    if value is None:
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        # Clean up the string
        cleaned = value.replace(',', '').replace('.', '').replace(' ', '').strip()
        try:
            return int(cleaned)
        except ValueError:
            return None

    return None
