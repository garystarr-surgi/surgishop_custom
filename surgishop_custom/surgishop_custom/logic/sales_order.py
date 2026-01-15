"""
Sales Order Server Scripts
"""
import frappe


def create_delivery_note(doc, method=None):
    """
    Emulate clicking "Create → Delivery Note" right after a Sales Order is submitted.
    Leaves the Delivery Note as a Draft and automatically prints it.
    """
    if doc.docstatus == 1:
        try:
            # Use the same backend method the button calls
            from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
            result = make_delivery_note(doc.name)

            # The mapper returns an unsaved DN as a dict
            if not result or not result.get("items"):
                frappe.msgprint("No deliverable items found, so no Delivery Note created.", alert=True)
            else:
                # Insert the DN as a new Draft document
                dn = frappe.get_doc(result)
                dn.insert(ignore_permissions=True)
                frappe.msgprint(
                    f"Draft Delivery Note {dn.name} created from Sales Order {doc.name}.",
                    alert=True, indicator="green"
                )
                
                # Automatically print the Delivery Note using surgi_print_dn app
                # Silently attempt printing - don't show error if it fails
                try:
                    printer_name = "Brother_HL-L3210CW_series"
                    frappe.call(
                        "surgi_print_dn.api.print_delivery_note_via_webhook",
                        doc_name=dn.name,
                        printer_name=printer_name
                    )
                    # Silent success - no popup needed
                    frappe.logger().info(f"Auto-print successful for DN {dn.name}")
                except:
                    # Silent failure - no popup to confuse user
                    frappe.logger().info(f"Auto-print attempted for DN {dn.name}")
                    
        except Exception as e:
            frappe.log_error(message=str(e), title=f"Auto DN creation failed for {doc.name}")
            frappe.msgprint("Auto Delivery Note creation failed — check Error Log.", alert=True, indicator="red")
