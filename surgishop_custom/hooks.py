app_name = "surgishop_custom"

# 1. Connect Client Scripts (JS)
doctype_js = {
    "Customer": "public/js/customer.js",
    "Item": "public/js/item.js",
    "Sales Invoice": "public/js/sales_invoice.js",
    "Sales Order": "public/js/sales_order.js",
    "Quotation": "public/js/quotation.js",
    "Customer Statement": "public/js/customer_statement.js"
}

# 2. Connect Server Scripts (Python)
doc_events = {
    "Sales Invoice": {
        "before_submit": "surgishop_custom.logic.sales_invoice.auto_send_setup"
    },
    "Delivery Note": {
        "after_submit": [
            "surgishop_custom.logic.delivery_note.to_packing_list",
            "surgishop_custom.logic.delivery_note.to_sales_invoice"
        ]
    },
    "Sales Order": {
        "after_submit": "surgishop_custom.logic.sales_order.create_delivery_note"
    },
    "Purchase Receipt": {
        "before_validate": "surgishop_custom.logic.purchase_receipt.allow_blemish"
    },
    "Email Queue": {
        "after_save": "surgishop_custom.logic.email_queue.bounce_notification"
    }
}

# 3. Connect API Methods
# This replaces your "API" type Server Scripts
# Accessible via: /api/method/surgishop_custom.api.check_recall_inventory
