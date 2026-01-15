// Valid Til
frappe.ui.form.on('Quotation', {
    refresh: function(frm) {
        if (frm.doc.__islocal && !frm.doc.valid_till) {
            let quotation_date = frappe.datetime.str_to_obj(frm.doc.transaction_date);
            // Example: Add 2 days
            let valid_till = frappe.datetime.add_days(quotation_date, 2);
            frm.set_value('valid_till', frappe.datetime.obj_to_str(valid_till));
        }
    },
    
    onload: function(frm) {
        // Attach listener directly to the customer field once the form loads
        if (frm.fields_dict.customer) {
            frm.fields_dict.customer.df.onchange = () => {
                if (frm.doc.customer) {
                    check_customer_lock(frm);
                }
            };
        }
    },
    
    customer: function(frm) {
        if (frm.doc.customer) {
            check_customer_lock(frm);
        }
    },
    
    validate: function(frm) {
        // Block saving if locked
        if (frm.doc.customer) {
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Customer",
                    fieldname: "custom_account_locked",
                    filters: { name: frm.doc.customer }
                },
                async: false,
                callback: function (r) {
                    if (r.message && r.message.custom_account_locked) {
                        frappe.throw(__("This customer is locked and cannot be used for " + frm.doctype + "."));
                    }
                }
            });
        }
    }
});

function check_customer_lock(frm) {
    frappe.call({
        method: "frappe.client.get_value",
        args: {
            doctype: "Customer",
            fieldname: "custom_account_locked",
            filters: { name: frm.doc.customer }
        },
        callback: function (r) {
            if (r.message && r.message.custom_account_locked) {
                frappe.msgprint({
                    title: __("Customer Locked"),
                    message: __("This customer is locked and cannot be used for " + frm.doctype + "."),
                    indicator: "red"
                });
                frm.set_value("customer", null);
            }
        }
    });
}
