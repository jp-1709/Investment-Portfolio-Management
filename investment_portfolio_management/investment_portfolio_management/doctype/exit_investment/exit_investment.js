// Copyright (c) 2026, Quantbit Technologies Pvt.Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Exit Investment", {
    refresh(frm) {
        // Filter Investment field to only show Submitted docs
        frm.set_query('investment', function () {
            return {
                filters: {
                    docstatus: 1
                }
            };
        });

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
    },

    exit_type: function (frm) {
        if (frm.doc.exit_type === "Full" && frm.doc.investment) {
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Investment Ledger Entry",
                    filters: {
                        investment: frm.doc.investment
                    },
                    fields: ["balance_units"],
                    order_by: "posting_date desc, creation desc",
                    limit_page_length: 1
                },
                callback: function (r) {
                    if (r.message && r.message.length > 0) {
                        let bal_units = r.message[0].balance_units;
                        frm.set_value('units_sold', bal_units);
                        frm.set_df_property('units_sold', 'read_only', 1);
                    }
                }
            });
        } else {
            frm.set_df_property('units_sold', 'read_only', 0);
        }
    },

    investment: function (frm) {
        if (frm.doc.investment) {
            frappe.db.get_doc('Investment', frm.doc.investment)
                .then(doc => {
                    frm.set_value('broker', doc.broker);
                });
        }
    },

    units_sold: function (frm) {
        // Validation for max units
        if (frm.doc.investment && frm.doc.units_sold) {
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Investment Ledger Entry",
                    filters: {
                        investment: frm.doc.investment
                    },
                    fields: ["balance_units"],
                    order_by: "posting_date desc, creation desc",
                    limit_page_length: 1
                },
                callback: function (r) {
                    if (r.message && r.message.length > 0) {
                        let bal_units = flt(r.message[0].balance_units);
                        if (flt(frm.doc.units_sold) > bal_units) {
                            frappe.msgprint(__("Units Sold cannot be greater than available balance: {0}", [bal_units]));
                            frm.set_value('units_sold', bal_units);
                        }
                    }
                }
            });
        }
        frm.trigger('calculate_totals');
    },

    exit_price: function (frm) {
        frm.trigger('calculate_totals');
    },

    charges: function (frm) {
        frm.trigger('calculate_totals');
    },

    calculate_totals: function (frm) {
        if (frm.doc.units_sold && frm.doc.exit_price) {
            let exit_amount = flt(frm.doc.units_sold) * flt(frm.doc.exit_price);
            frm.set_value('exit_amount', exit_amount);

            let charges = flt(frm.doc.charges) || 0;
            frm.set_value('net_amount', exit_amount - charges);
        }
    }
});
