// Auto populate sales person on Sales Orders
frappe.ui.form.on('Sales Order', {
    onload: function(frm) {
        // Only run this logic for a new Sales Order (draft status) and if Sales Team is empty
        if (frm.doc.docstatus === 0 && frm.doc.__islocal === 1 && frm.doc.sales_team.length === 0) {
            
            // Call a safer method that handles the Sales Person lookup
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "User",
                    name: frappe.session.user
                },
                callback: function(r) {
                    if (r.message) {
                        var sales_person_name = null;
                        
                        // Try to get sales_person field if it exists
                        if (r.message.sales_person) {
                            sales_person_name = r.message.sales_person;
                        }
                        // Alternative: Check if there's an employee link, then get sales person from employee
                        else if (r.message.employee) {
                            frappe.call({
                                method: "frappe.client.get",
                                args: {
                                    doctype: "Employee",
                                    name: r.message.employee
                                },
                                callback: function(emp_r) {
                                    if (emp_r.message && emp_r.message.name) {
                                        // Check if there's a Sales Person with the same name as Employee
                                        frappe.call({
                                            method: "frappe.client.get_list",
                                            args: {
                                                doctype: "Sales Person",
                                                filters: {
                                                    "employee": emp_r.message.name
                                                },
                                                fields: ["name"],
                                                limit: 1
                                            },
                                            callback: function(sp_r) {
                                                if (sp_r.message && sp_r.message.length > 0) {
                                                    add_sales_person_to_team(frm, sp_r.message[0].name);
                                                }
                                            }
                                        });
                                    }
                                }
                            });
                            return; // Exit here since we're doing async lookup
                        }
                        
                        // If we found a sales person directly, add them
                        if (sales_person_name) {
                            add_sales_person_to_team(frm, sales_person_name);
                        }
                    }
                },
                error: function(r) {
                    // Silently handle error - don't show to user
                    console.log("Could not fetch user sales person");
                }
            });
        }
    },
    
    customer: function(frm) {
        if (!frm.doc.customer) return;

        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Customer",
                name: frm.doc.customer
            },
            callback: function(r) {
                if (r.message && r.message.custom_account_locked) {
                    frappe.msgprint({
                        title: __("Customer Locked"),
                        message: __("This customer is locked and cannot be used for Sales Orders."),
                        indicator: "red"
                    });
                }
            }
        });
    }
});

function add_sales_person_to_team(frm, sales_person_name) {
    // Clear any existing rows (should be zero, but good practice)
    frm.clear_table('sales_team');
    
    // Add a new row to the Sales Team child table
    var new_row = frm.add_child('sales_team');
    
    // Set the Sales Person and their contribution
    frappe.model.set_value(new_row.doctype, new_row.name, 'sales_person', sales_person_name);
    frappe.model.set_value(new_row.doctype, new_row.name, 'contribution', 100);
    
    // Refresh the Sales Team grid
    frm.refresh_field('sales_team');
    
    frappe.show_alert({
        message: __("Sales Person set to {0}", [sales_person_name]),
        indicator: 'green'
    }, 5);
}
