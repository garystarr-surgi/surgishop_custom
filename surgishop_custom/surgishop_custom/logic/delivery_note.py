"""
Delivery Note Server Scripts
"""
import frappe


def to_packing_list(doc, method=None):
    """
    This function MUST be linked as a Custom Script or Server Script
    to run on the 'after_submit' event of the 'Delivery Note' DocType.
    """
    # --- Configuration ---
    PRINTER_NAME = "Brother_HL-L3210CW_series"
    PACKING_SLIP_DOCTYPE = "Packing Slip"
    PRINT_FORMAT = "Surgi Packing Slip"

    if doc.doctype != "Delivery Note" or doc.docstatus != 1:
        # Only show this if the hook is somehow misconfigured
        return

    dn = doc

    try:
        # Reload DN silently to ensure latest state
        dn = frappe.get_doc("Delivery Note", doc.name)
        frappe.log_error(message=f"Reloaded DN: {dn.name}", title="Debug: DN Reload Success")
    except Exception as reload_err:
        frappe.msgprint(f"✗ Failed to reload Delivery Note {doc.name}. Error: {str(reload_err)}", alert=True, indicator="red")
        frappe.log_error(message=str(reload_err), title=f"DN Reload Error for {doc.name}")
        return

    # Check if the Packing Slip DocType exists (critical check)
    if not frappe.db.exists("DocType", PACKING_SLIP_DOCTYPE):
        frappe.msgprint("✗ Packing Slip DocType not found! Check configuration.", alert=True, indicator="red")
        return

    try:
        packing_slip = frappe.new_doc(PACKING_SLIP_DOCTYPE)

        # Set REQUIRED fields (General)
        packing_slip.from_case_no = 1
        packing_slip.to_case_no = 1

        # --- MANDATORY HEADER MAPPING ---
        packing_slip.delivery_note = dn.name
        packing_slip.customer = dn.customer

        try:
            packing_slip.customer_name = dn.customer_name
        except Exception:
            packing_slip.customer_name = dn.customer

        packing_slip.naming_series = "MAT-PAC-.YYYY.-"
        packing_slip.company = dn.company
        packing_slip.delivery_date = dn.delivery_date
        packing_slip.shipping_address_name = dn.shipping_address_name
        packing_slip.billing_address_name = dn.billing_address_name
        packing_slip.contact_person = dn.contact_person

        # Map items
        mapped_item_count = 0
        for dn_item in dn.items:
            dn_item_reference_name = dn_item.name

            if not dn_item_reference_name:
                error_msg = f"CRITICAL: Failed to retrieve unique name for item {dn_item.item_code} (idx: {dn_item.idx}). Cannot link to Packing Slip."
                frappe.msgprint(error_msg, alert=True, indicator="red")
                continue

            ps_item = packing_slip.append("items", {})
            try:
                ps_item.dn_detail = dn_item_reference_name
                mapped_item_count += 1
            except Exception:
                frappe.msgprint(f"CRITICAL: Item {dn_item.item_code} failed to link. Field 'dn_detail' not found.", alert=True, indicator="red")
                frappe.log_error(f"Missing mandatory reference field 'dn_detail' on PS Item for {dn_item.item_code}", "PS Item Link Failure")
                packing_slip.items.pop()
                continue

            ps_item.item_code = dn_item.item_code
            ps_item.item_name = dn_item.item_name
            ps_item.qty = dn_item.qty

            try:
                ps_item.description = dn_item.description
            except Exception:
                ps_item.description = ""

            try:
                ps_item.stock_uom = dn_item.stock_uom
            except Exception:
                ps_item.stock_uom = None

            try:
                ps_item.uom = dn_item.uom
            except Exception:
                ps_item.uom = None

            try:
                ps_item.warehouse = dn_item.warehouse
            except Exception:
                ps_item.warehouse = None

        if mapped_item_count == 0:
            frappe.msgprint("✗ No items could be successfully mapped to the Packing Slip.", alert=True, indicator="red")
            return

        packing_slip.insert(ignore_permissions=True)

        # Submit the Packing Slip
        try:
            packing_slip.submit()
            
        except Exception as submit_err:
            error_details = str(submit_err)
            frappe.msgprint(f"✗ Packing Slip submission failed. Details: {error_details}", alert=True, indicator="red")
            frappe.log_error(message=error_details, title=f"PS Submit Error for {packing_slip.name}")
            return
            
        # --- Print the Submitted Packing Slip ---
        print_failed = False
        try:
            # Call the custom app function to print the Packing Slip
            frappe.call(
                "surgi_print_dn.api.print_packing_slip_via_webhook",
                doc_name=packing_slip.name,
                printer_name=PRINTER_NAME,
                print_format=PRINT_FORMAT  # Pass the custom print format defined in the config
            )
        except Exception as print_err:
            error_details = str(print_err)
            print_failed = True
            # Log failure but do not return
            frappe.log_error(message=error_details, title=f"PS Print Error for {packing_slip.name}")

        # --- FINAL SINGLE MESSAGE ---
        if print_failed:
            frappe.msgprint(
                f"✓ Packing Slip {packing_slip.name} created and submitted. ✗ WARNING: Print failed. Check Error Log for details.", 
                alert=True, indicator="orange"
            )
        else:
            frappe.msgprint(
                f"✓ Packing Slip {packing_slip.name} created, submitted, and sent to printer.", 
                alert=True, indicator="green"
            )

    except Exception as ps_err:
        frappe.msgprint(f"✗ Packing Slip creation failed. Error: {str(ps_err)}", alert=True, indicator="red")
        frappe.log_error(message=str(ps_err), title="Packing Slip Creation Error")
        return


def to_sales_invoice(doc, method=None):
    """
    This script MUST be attached as a Server Script
    to run on the 'after_submit' event of the 'Delivery Note' DocType.
    It creates and submits the Sales Invoice only after the Delivery Note is finalized.
    """
    # Ensure the document is a submitted Delivery Note
    if doc.doctype != "Delivery Note" or doc.docstatus != 1:
        return

    dn = doc

    # --- Create and Submit Sales Invoice ---
    try:
        # 1. Call the standard mapper to create the Sales Invoice dict from the Delivery Note
        # We pass BOTH the name (source_name) and the document object (source_doc) for maximum reliability.
        from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
        si_doc_dict = make_sales_invoice(dn.name)

        if si_doc_dict and si_doc_dict.get('doctype') == 'Sales Invoice':
            # 2. Convert dict to DocType object, insert, and submit
            si = frappe.get_doc(si_doc_dict)
            si.insert(ignore_permissions=True)
            si.submit()

            # 3. Final success message
            frappe.msgprint(
                f"✓ Sales Invoice {si.name} automatically created and submitted.",
                alert=True,
                indicator="green"
            )
        else:
            # Handle cases where the mapper returns something unexpected (e.g., already invoiced)
            frappe.msgprint("✗ Sales Invoice creation skipped (DN likely already invoiced).", alert=True, indicator="orange")

    except Exception as si_err:
        error_details = str(si_err)
        # Log failure
        frappe.msgprint(f"✗ Sales Invoice automation failed. Check Error Log. Details: {error_details}", alert=True, indicator="red")
        frappe.log_error(message=error_details, title=f"SI Auto Creation Error for DN {dn.name}")
