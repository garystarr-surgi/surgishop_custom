"""
Email Queue Server Scripts
"""
import frappe
from frappe.utils import escape_html


def bounce_notification(doc, method=None):
    """
    Alert Accounting AND log on Sales Invoice timeline
    Prevents duplicate alerts
    ERPNext v16 compatible
    """
    if (
        doc.reference_doctype == "Sales Invoice"
        and doc.status in ("Error", "Not Sent")
        and not doc.get("custom_alert_sent")
    ):

        invoice_name = doc.reference_name
        error_msg = doc.error or "No error details provided"

        # 1️⃣ Log to Sales Invoice timeline
        try:
            frappe.get_doc("Sales Invoice", invoice_name).add_comment(
                "Info",
                f"""
                <b>Email Delivery Failure</b><br>
                The invoice email failed or bounced.<br><br>
                <b>Error:</b><br>
                <pre>{escape_html(error_msg)}</pre>
                """
            )
        except Exception as e:
            frappe.log_error(
                f"Failed to log email error to Sales Invoice {invoice_name}: {e}"
            )

        # 2️⃣ Email Accounting
        frappe.sendmail(
            recipients=["accounting@surgishop.com"],
            subject=f"[ALERT] Sales Invoice Email Failed – {invoice_name}",
            message=f"""
            <p><b>Sales Invoice Email Failure</b></p>

            <p>
            The email for Sales Invoice <b>{invoice_name}</b> failed to send or bounced.
            </p>

            <p><b>Error Details:</b></p>
            <pre>{escape_html(error_msg)}</pre>

            <p>
            Please verify the customer email address and resend the invoice.
            </p>
            """,
            delayed=False
        )

        # 3️⃣ Mark alert as sent (prevents duplicates)
        doc.db_set("custom_alert_sent", 1, update_modified=False)
