"""
Purchase Receipt Server Scripts
"""
import frappe
from frappe.utils import flt


def allow_blemish(doc, method=None):
    """
    Purchase Receipt allow blemish in received qty
    DocType Event: Before Validate
    """
    total_blemish = 0.0
    total_rejected = 0.0
    total_received = 0.0

    for item in doc.items:
        qty_ordered = flt(item.get("qty") or 0)
        blemish = flt(item.get("custom_blemish_quantity") or 0)
        rejected = flt(item.get("rejected_qty") or 0)

        accepted = qty_ordered + blemish
        received = accepted + rejected

        item.qty = received
        item.accepted_qty = accepted
        item.received_qty = received

        total_blemish += blemish
        total_rejected += rejected
        total_received += received

    doc.custom_total_blemish_quantity = total_blemish
    doc.custom_total_rejected_quantity = total_rejected
    doc.custom_total_received = total_received
