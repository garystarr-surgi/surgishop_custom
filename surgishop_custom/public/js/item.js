// New Item Creation Mandatory Fields
frappe.ui.form.on("Item", {
    validate(frm) {
        // Run only for brand new Item creation
        
        console.log("Validate fired! is_new =", frm.is_new(), 
                "recalls =", frm.doc.custom_recalls_checked,
                "temperature =", frm.doc.custom_temperature_checked);

        if (frm.is_new()) {
            let missing = [];

            if (!frm.doc.custom_recalls_checked) {
                missing.push("Recalls Checked");
            }

            if (!frm.doc.custom_temperature_checked) {
                missing.push("Temperature Checked");
            }

            if (missing.length > 0) {
                frappe.throw(
                    __("Please check the following before saving this new Item:<br><br>") +
                    missing.join("<br>")
                );
            }
        }
    }
});
