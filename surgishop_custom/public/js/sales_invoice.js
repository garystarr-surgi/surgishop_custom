// Credit Memo Print Format
frappe.ui.form.on('Sales Invoice', {
    // This runs when the form is first loaded
    onload: function(frm) {
        set_print_format(frm);
    },
    
    // This runs after the document is submitted
    after_save: function(frm) {
        // Only necessary if the print format needs to update after submission logic
        set_print_format(frm);
    }
});

var set_print_format = function(frm) {
    if (frm.doc.is_return === 1) {
        // Set the default print format to your Credit Note format
        frm.meta.default_print_format = "Surgi Credit Memo";
        
        // Optional: Alert the user or log to console
        console.log("Print Format changed to Credit Note");
        
    } else {
        // Set the default print format back to your regular Sales Invoice format
        // Replace 'Standard' with the name of your default Sales Invoice print format if you use a custom one
        frm.meta.default_print_format = "Standard"; 
    }
}
