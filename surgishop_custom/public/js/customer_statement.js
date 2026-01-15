// Customer Statement Print Buttons
frappe.ui.form.on('Customer Statement', {
    refresh: function(frm) {
        // Only show buttons if document is saved
        if (!frm.is_new()) {
            // Remove default print button group to avoid confusion
            frm.page.clear_primary_action();
            
            // Button 1: Full Customer Statement
            frm.add_custom_button(__('Full Statement'), function() {
                var print_format = 'Surgi Customer Statement';
                var url = frappe.urllib.get_full_url(
                    '/printview?'
                    + 'doctype=' + encodeURIComponent(frm.doc.doctype)
                    + '&name=' + encodeURIComponent(frm.doc.name)
                    + '&format=' + encodeURIComponent(print_format)
                    + '&no_letterhead=0'
                    + '&letterhead=Your%20Letter%20Head'
                    + '&settings=%7B%7D'
                    + '&_lang=en'
                );
                window.open(url, '_blank');
            }, __('Print'));
            
            // Button 2: Transaction Statement
            frm.add_custom_button(__('Transaction Statement'), function() {
                var print_format = 'Surgi Transaction Statement';
                var url = frappe.urllib.get_full_url(
                    '/printview?'
                    + 'doctype=' + encodeURIComponent(frm.doc.doctype)
                    + '&name=' + encodeURIComponent(frm.doc.name)
                    + '&format=' + encodeURIComponent(print_format)
                    + '&no_letterhead=0'
                    + '&letterhead=Your%20Letter%20Head'
                    + '&settings=%7B%7D'
                    + '&_lang=en'
                );
                window.open(url, '_blank');
            }, __('Print'));
            
            // Button 3: Open Items Statement
            frm.add_custom_button(__('Open Items'), function() {
                var print_format = 'Surgi Open Items Statement';
                 var url = frappe.urllib.get_full_url(
                    '/printview?'
                    + 'doctype=' + encodeURIComponent(frm.doc.doctype)
                    + '&name=' + encodeURIComponent(frm.doc.name)
                    + '&format=' + encodeURIComponent(print_format)
                    + '&no_letterhead=0'
                    + '&letterhead=Your%20Letter%20Head'
                    + '&settings=%7B%7D'
                    + '&_lang=en'
                );
                window.open(url, '_blank');
            }, __('Print'));
        }
    }
});
