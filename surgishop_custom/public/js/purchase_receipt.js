// Purchase Receipt Total Quantity = Received Warehouse
console.log('--- Purchase Receipt Totals Script Loaded ---');

(() => {
    const debounceDelay = 150;
    let debounceTimer;

    const scheduleTotalsUpdate = (frm) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => updateParentTotals(frm), debounceDelay);
    };

    const getAcceptedQuantity = (item) => {
        if (item.accepted_qty != null) {
            return flt(item.accepted_qty);
        }
        if (item.qty != null) {
            return flt(item.qty);
        }
        return 0;
    };

    const updateParentTotals = (frm) => {
        let totalAccepted = 0;
        let totalBlemish = 0;
        let totalRejected = 0;

        (frm.doc.items || []).forEach((item) => {
            const warehouse = (item.warehouse || '').toLowerCase();
            const acceptedQty = getAcceptedQuantity(item);
            const blemishQty = flt(item.custom_blemish_quantity || 0);
            const rejectedQty = flt(item.rejected_qty || 0);

            if (warehouse.includes('blemish')) {
                totalBlemish += blemishQty || acceptedQty;
            } else if (warehouse.includes('store')) {
                totalAccepted += acceptedQty;
            }

            totalRejected += rejectedQty;
        });

        const totalReceived = totalAccepted + totalBlemish + totalRejected;

        frm.set_value('total_qty', flt(totalAccepted));
        frm.set_value('custom_total_blemish_quantity', flt(totalBlemish));
        frm.set_value('custom_total_rejected_quantity', flt(totalRejected));
        frm.set_value('custom_total_received', flt(totalReceived));
    };

    frappe.ui.form.on('Purchase Receipt Item', {
        accepted_qty: scheduleTotalsUpdate,
        qty: scheduleTotalsUpdate,
        custom_blemish_quantity: scheduleTotalsUpdate,
        rejected_qty: scheduleTotalsUpdate,
        warehouse: scheduleTotalsUpdate,
        items_add: scheduleTotalsUpdate,
        items_remove: scheduleTotalsUpdate,
        form_render: scheduleTotalsUpdate,
    });

    frappe.ui.form.on('Purchase Receipt', {
        refresh(frm) {
            scheduleTotalsUpdate(frm);
        },
        validate(frm) {
            updateParentTotals(frm);
        },
    });
})();
