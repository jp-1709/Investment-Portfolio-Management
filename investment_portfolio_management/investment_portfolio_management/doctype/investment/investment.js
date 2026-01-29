frappe.ui.form.on('Investment', {
<<<<<<< HEAD
    refresh: function (frm) {
        frm.trigger('toggle_fields');
    },
=======
>>>>>>> sahil-feature

    investment_type: function (frm) {
        if (!frm.doc.investment_type) return;

        frappe.db.get_doc('Investment Type', frm.doc.investment_type)
            .then(doc => {
                frm.inv_type_settings = doc; // Store for later
                frm.trigger('toggle_fields');
            });
    },

    toggle_fields: function (frm) {
        if (!frm.doc.investment_type) return;

<<<<<<< HEAD
        // If in cache use, else fetch
=======
        // If in cache use, else fetch 
>>>>>>> sahil-feature
        if (frm.inv_type_settings) {
            apply_settings(frm, frm.inv_type_settings);
        } else {
            frappe.db.get_doc('Investment Type', frm.doc.investment_type)
                .then(doc => {
                    frm.inv_type_settings = doc;
                    apply_settings(frm, doc);
                });
        }
    }
<<<<<<< HEAD
});

=======
    
});

function calculate_amount(frm) {
    let units = frm.doc.units || 0;
    let price = frm.doc.price_per_unit || 0;

    let amount = units * price;

    frm.set_value('amount_invested', amount);
}

>>>>>>> sahil-feature
function apply_settings(frm, settings) {
    // has_scheme -> investment_scheme
    frm.toggle_display('investment_scheme', settings.has_scheme);
    frm.toggle_reqd('investment_scheme', settings.has_scheme);

    // requires_broker -> broker
    frm.toggle_display('broker', settings.requires_broker);
    frm.toggle_reqd('broker', settings.requires_broker);

    // has_maturity -> maturity_date
    frm.toggle_display('maturity_date', settings.has_maturity);
    frm.toggle_reqd('maturity_date', settings.has_maturity);
}
