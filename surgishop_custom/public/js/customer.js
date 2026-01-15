// Credit Limit base on Facility Type
frappe.ui.form.on('Customer', {
    refresh(frm) {
        restrict_credit_limit_access(frm);
        update_customer_credit(frm);
        add_purchase_history_button(frm);
        update_lock_banner(frm);
    },
    custom_facility_type(frm) {
        update_credit_limit(frm);
    },
    custom_account_lock_days_overdue(frm) {
        update_lock_banner(frm);
    }
});

function restrict_credit_limit_access(frm) {
    // Disable the child table fields by default
    if (frm.fields_dict.credit_limits && frm.fields_dict.credit_limits.grid) {
        frm.fields_dict.credit_limits.grid.wrapper.find('.grid-remove-rows').hide();
        frm.fields_dict.credit_limits.grid.wrapper.find('.grid-add-row').hide();
        
        // Check user roles
        if (!frappe.user.has_role('Accounts Manager') && !frappe.user.has_role('System Manager')) {
            // Loop through each row and disable editing
            frm.fields_dict.credit_limits.grid.wrapper.find('[data-fieldname="credit_limit"]').prop('disabled', true);
        } else {
            // Show add/remove buttons for authorized users
            frm.fields_dict.credit_limits.grid.wrapper.find('.grid-remove-rows').show();
            frm.fields_dict.credit_limits.grid.wrapper.find('.grid-add-row').show();
        }
    }
}

function update_credit_limit(frm) {
    if (!frm.doc.custom_facility_type) return;

    const limits = {
        'Hospital': 40000,
        'Surgery Center': 10000,
        'Urgent Care': 10000,
        'Veterinary': 10000,
        'B2B': 999999,
        'Wholesale': 999999
    };

    const new_limit = limits[frm.doc.custom_facility_type] || 0;

    // Find existing child or create new
    let child = frm.doc.credit_limits && frm.doc.credit_limits.length > 0
        ? frm.doc.credit_limits[0]
        : frm.add_child('credit_limits', { company: frappe.defaults.get_default('company') });

    frappe.model.set_value(child.doctype, child.name, 'credit_limit', new_limit);
    frm.refresh_field('credit_limits');
}

// Customer Credit Field
function update_customer_credit(frm) {
    if (frm.is_new()) return;
    
    // The frappe.call is used to execute a Python function on the server side
    frappe.call({
        // Function to call for calculating the customer/party balance on a given date
        method: "erpnext.accounts.utils.get_balance_on",
        args: {
            // The balance must be calculated up to the current date (today)
            date: frappe.datetime.nowdate(),
            party_type: 'Customer',
            // The name of the current Customer being viewed
            party: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                // r.message contains the calculated balance (e.g., -100.00 for a credit)
                var balance = r.message;
                
                // Set the value of your custom field
                frm.set_value('custom_customer_credit', balance);
                
                // Refresh the field to display the new value immediately
                frm.refresh_field('custom_customer_credit');
            }
        }
    });
}

// Customer Purchase History
function add_purchase_history_button(frm) {
    if (!frm.is_new()) {
        frm.add_custom_button(__('Purchase History'), function() {
            frappe.set_route('query-report', 'Customer Item Purchase History', {
                'customer': frm.doc.name  // lowercase
            });
        }, __('Reports'));
    }
}

// Overdue Banner
function update_lock_banner(frm) {
    const overdue_field = "custom_account_lock_days_overdue";  // numeric field for overdue days
    const lock_field = "custom_lock_status";                   // HTML field for banner

    const overdue_days = frm.doc[overdue_field] || 0;

    console.log("Overdue days:", overdue_days);  // DEBUG: confirm value

    let banner_html = "";

    if (overdue_days >= 50) {
        // 🔴 HARD LOCK
        banner_html = `
            <div style="
                background-color: #f8d7da;
                color: #721c24;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                border: 1px solid #f5c6cb;
                display: flex;
                align-items: center;
                gap: 6px;
            ">
                <i class="fa fa-lock"></i>
                CUSTOMER IS HARD LOCKED (50+ DAYS OVERDUE)
            </div>`;
    } else if (overdue_days >= 40) {
        // 🟡 SOFT LOCK
        banner_html = `
            <div style="
                background-color: #fff3cd;
                color: #856404;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                border: 1px solid #ffeeba;
                display: flex;
                align-items: center;
                gap: 6px;
            ">
                <i class="fa fa-exclamation-triangle"></i>
                CUSTOMER IS SOFT LOCKED (40+ DAYS OVERDUE) SEE ACCOUNTING
            </div>`;
    }

    // Render banner or hide if empty
    if (frm.fields_dict[lock_field]) {
        frm.fields_dict[lock_field].$wrapper.html(banner_html);

        if (!banner_html) {
            $(frm.fields_dict[lock_field].wrapper).hide();
        } else {
            $(frm.fields_dict[lock_field].wrapper).show();
        }
    } else {
        console.warn("Lock HTML field not found:", lock_field);
    }
}
