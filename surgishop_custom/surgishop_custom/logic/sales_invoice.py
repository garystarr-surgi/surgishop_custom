"""
Sales Invoice Server Scripts
"""
import frappe
from frappe.utils import add_to_date, now_datetime, format_datetime


def auto_send_setup(doc, method=None):
    """
    Server Script: Sales Invoice - Auto Send Setup
    Type: DocType Event
    DocType: Sales Invoice
    Event: Before Submit
    """
    # Skip auto-send for returns/credit notes
    if not doc.is_return:
        # Calculate send time (24 hours from now) using frappe.utils
        send_time = add_to_date(now_datetime(), hours=24)
        
        # Set custom field values (we only need send_time and status)
        doc.custom_scheduled_send_time = send_time
        doc.custom_auto_send_status = 'Scheduled'
        
        frappe.msgprint(
            "Invoice will be automatically sent to customer on " + str(format_datetime(send_time)),
            indicator='green',
            title='Auto-Send Scheduled'
        )


def send_pending_invoices():
    """
    Server Script: Send Pending Invoices
    Type: Scheduler Event
    Event: Hourly
    """
    # Get all invoices scheduled for auto-send where send time has passed
    # Exclude returns/credit notes (is_return = 0)
    invoices = frappe.db.sql("""
        SELECT name, customer, customer_name, contact_email
        FROM `tabSales Invoice`
        WHERE docstatus = 1
        AND is_return = 0
        AND custom_auto_send_status = 'Scheduled'
        AND custom_scheduled_send_time IS NOT NULL
        AND custom_scheduled_send_time <= NOW()
    """, as_dict=True)
    
    for invoice in invoices:
        try:
            send_invoice_email(invoice.name)
            
            # Update status
            frappe.db.set_value(
                'Sales Invoice',
                invoice.name,
                {
                    'custom_auto_send_status': 'Sent',
                    'custom_actual_send_time': now_datetime()
                },
                update_modified=False
            )
            frappe.db.commit()
            
        except Exception as e:
            # Mark as failed and log error
            frappe.db.set_value(
                'Sales Invoice',
                invoice.name,
                'custom_auto_send_status',
                'Failed',
                update_modified=False
            )
            frappe.db.commit()
            
            frappe.log_error(
                message="Invoice: " + invoice.name + "\nError: " + str(e),
                title="Failed to send invoice email"
            )


def send_invoice_email(invoice_name):
    """
    Send the invoice email with PDF attachment
    """
    # Get the invoice document
    invoice = frappe.get_doc('Sales Invoice', invoice_name)
    
    # Get customer email
    recipient = invoice.contact_email or frappe.db.get_value('Customer', invoice.customer, 'email_id')
    
    if not recipient:
        raise Exception("No email found for customer " + invoice.customer)
    
    # Email subject
    subject = "Invoice " + invoice.name + " from SurgiShop"
    
    # Email body - UPDATE THIS WITH YOUR CUSTOM TEXT
    customer_name = invoice.customer_name or invoice.customer
    message = "Dear " + customer_name + ",\n\n"
    message = message + "Please find attached invoice " + invoice.name + ".\n\n"
    message = message + "[YOUR CUSTOM EMAIL BODY WILL GO HERE]\n\n"
    message = message + "Best regards,\nSurgiShop Accounting Team"
    
    # Generate PDF with custom print format
    print_format = "Surgi Sales Invoice"
    
    # Get PDF content using frappe.utils.pdf
    from frappe.utils.pdf import get_pdf
    pdf_content = get_pdf(
        'Sales Invoice',
        invoice.name,
        print_format=print_format
    )
    
    # Send email with attachment
    frappe.sendmail(
        recipients=[recipient],
        sender="accounting@surgishop.com",
        subject=subject,
        message=message,
        attachments=[{
            'fname': invoice.name + '.pdf',
            'fcontent': pdf_content
        }],
        reference_doctype='Sales Invoice',
        reference_name=invoice.name
    )
    
    # Add comment to invoice
    invoice.add_comment(
        'Comment',
        'Invoice automatically sent to ' + recipient + ' via email'
    )
