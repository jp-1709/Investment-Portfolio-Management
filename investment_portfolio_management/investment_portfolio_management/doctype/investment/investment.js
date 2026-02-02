frappe.ui.form.on('Investment', {
    refresh: function (frm) {
        frm.trigger('toggle_fields');
    },

    units: function (frm) {
        frm.trigger('calculate_amount');
    },

    price_per_unit: function (frm) {
        frm.trigger('calculate_amount');
    },

    calculate_amount: function (frm) {
        if (frm.doc.units && frm.doc.price_per_unit) {
            frm.set_value('amount_invested', flt(frm.doc.units) * flt(frm.doc.price_per_unit));
        }
    },

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

        // If in cache use, else fetch
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
});

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

// Add filtering for accounts
frappe.ui.form.on('Investment', {
    setup: function (frm) {
        frm.set_query("bank_account", function () {
            return {
                filters: {
                    "company": frm.doc.company,
                    "is_group": 0,
                    "disabled": 0
                }
            };
        });
        frm.set_query("investment_account", function () {
            return {
                filters: {
                    "company": frm.doc.company,
                    "is_group": 0,
                    "disabled": 0
                }
            };
        });
    }
});
