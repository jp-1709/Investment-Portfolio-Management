import frappe
from frappe.model.document import Document
from frappe.utils import nowdate
from investment_portfolio_management.investment_portfolio_management.doctype.investment_ledger_entry.investment_ledger_entry import create_investment_ledger_entry

class Investment(Document):
    def before_insert(self):
        if self.amended_from:
            self.status = "Active"

    def validate(self):
        if not self.posting_date:
            self.posting_date = nowdate()
        self.validate_mandatory_fields()
        
    def validate_mandatory_fields(self):
        # Fetch Investment Type settings
        if not self.investment_type:
            return
            
        inv_type = frappe.get_doc("Investment Type", self.investment_type)
        
        if inv_type.requires_broker and not self.broker:
            frappe.throw(f"Broker is required for Investment Type: {self.investment_type}")
            
        if inv_type.has_scheme and not self.investment_scheme:
            frappe.throw(f"Investment Scheme is required for Investment Type: {self.investment_type}")
            
        if inv_type.has_maturity and not self.maturity_date:
            frappe.throw(f"Maturity Date is required for Investment Type: {self.investment_type}")

    def on_submit(self):
        self.create_ledger_entry()
        self.create_journal_entry()
        self.status = "Active"
        
    def on_cancel(self):
        # In-place cancellation
        from investment_portfolio_management.investment_portfolio_management.doctype.investment_ledger_entry.investment_ledger_entry import process_cancellation
        process_cancellation(self.name, self.name) # For Investment, voucher_no is the name
        self.status = "Cancelled"

    def create_journal_entry(self):
        jv = frappe.new_doc("Journal Entry")
        jv.posting_date = self.posting_date
        jv.voucher_type = "Journal Entry"
        jv.company = self.company
        jv.remark = f"Investment Entry for {self.name}"
        jv.custom_investment = self.name 
        # Credit Bank Account
        jv.append('accounts', {
            'account': self.bank_account,
            'credit_in_account_currency': self.amount_invested,
            'cost_center': frappe.get_cached_value('Company',  self.company,  'cost_center')
        })
        
        # Debit Investment Account
        jv.append('accounts', {
            'account': self.investment_account,
            'debit_in_account_currency': self.amount_invested,
            'cost_center': frappe.get_cached_value('Company',  self.company,  'cost_center')
        })
        
        try:
            jv.save()
            jv.submit()
            
            frappe.msgprint(f"Journal Entry {jv.name} created successfully")
            self.db_set('reference_jv', jv.name)
            
        except Exception as e:
            frappe.throw(f"Failed to create Journal Entry: {str(e)}")

    def create_ledger_entry(self, cancel=False):
        args = {
            "investment": self.name,
            "posting_date": self.posting_date or self.creation,
            "transaction_type": "Investment",
            "document_date": self.investment_date,
            "remarks": self.remarks,
            "voucher_no": self.name
        }
        
        args["debit_amount"] = self.amount_invested
        args["units_in"] = self.units
            
        create_investment_ledger_entry(args)

