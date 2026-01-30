import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {} 

    columns = get_columns()
    data = get_data(filters)

    # Returning only columns and data ensures NO chart appears on the report page
    return columns, data

def get_columns(): 
    return [
        {"label": _("Ledger Entry Name"), "fieldname": "ledger_entry_name", "fieldtype": "Link", "options": "Investment Ledger Entry", "width": 180},
        {"label": _("Investment Name"), "fieldname": "investment_name", "fieldtype": "Link", "options": "Investment", "width": 150},
        {"label": _("Investment Date"), "fieldname": "investment_date", "fieldtype": "Date", "width": 150},
        {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
        {"label": _("Transaction Type"), "fieldname": "transaction_type", "fieldtype": "Data", "width": 140},
        {"label": _("Investment Type"), "fieldname": "investment_type", "fieldtype": "Data", "width": 140},
        {"label": _("Category"), "fieldname": "investment_category", "fieldtype": "Data", "width": 120},
        {"label": _("Broker"), "fieldname": "broker", "fieldtype": "Data", "width": 120},
        {"label": _("Investment Scheme"), "fieldname": "investment_scheme", "fieldtype": "Link", "options": "Investment", "width": 180},
        {"label": _("Units In"), "fieldname": "units_in", "fieldtype": "Float", "width": 100},
        {"label": _("Units Out"), "fieldname": "units_out", "fieldtype": "Float", "width": 100},
        {"label": _("Debit Amount"), "fieldname": "debit_amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Credit Amount"), "fieldname": "credit_amount", "fieldtype": "Currency", "width": 140},
        {"label": _("Balance Units"), "fieldname": "balance_units", "fieldtype": "Float", "width": 120},
        {"label": _("Balance Amount"), "fieldname": "balance_amount", "fieldtype": "Currency", "width": 140}
    ]

def get_data(filters):
    conditions = ""
    
    if filters.get("investment_type"):
        conditions += " AND i.investment_type = %(investment_type)s"
    if filters.get("broker"):
        conditions += " AND i.broker = %(broker)s"
    if filters.get("from_date"):
        conditions += " AND ile.posting_date >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " AND ile.posting_date <= %(to_date)s"

    sql_query = f"""
        SELECT
            ile.name AS ledger_entry_name,
            ile.investment AS investment_name,
            i.investment_date AS investment_date, 
            ile.transaction_type AS transaction_type,
            IFNULL(ile.units_in, 0) AS units_in,
            IFNULL(ile.units_out, 0) AS units_out,
            IFNULL(ile.debit_amount, 0) AS debit_amount,
            IFNULL(ile.credit_amount, 0) AS credit_amount,
            IFNULL(ile.balance_units, 0) AS balance_units,
            IFNULL(ile.balance_amount, 0) AS balance_amount,
            ile.posting_date AS posting_date, 
            i.investment_type AS investment_type,
            i.investment_category AS investment_category,
            i.broker AS broker,
            i.name AS investment_scheme
        FROM
            `tabInvestment Ledger Entry` ile
        LEFT JOIN
            `tabInvestment` i ON ile.investment = i.name
        WHERE
            i.docstatus = 1 
            AND i.status = 'Active'
            AND (i.maturity_date >= CURDATE() OR i.maturity_date IS NULL OR i.maturity_date = '')
            {conditions}
        ORDER BY
            ile.posting_date DESC
    """
    return frappe.db.sql(sql_query, filters, as_dict=True)