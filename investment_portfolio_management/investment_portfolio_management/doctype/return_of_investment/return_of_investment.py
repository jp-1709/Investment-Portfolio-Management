import frappe
from frappe.model.document import Document
from investment_portfolio_management.investment_portfolio_management.doctype.investment_ledger_entry.investment_ledger_entry import create_investment_ledger_entry

class ReturnofInvestment(Document):
    def validate(self):
        if not self.posting_date:
            self.posting_date = frappe.utils.nowdate()

    def on_submit(self):
        self.create_ledger_entry()
        self.create_journal_entry()
        self.status = "Submitted"
        
    def on_cancel(self):
        from investment_portfolio_management.investment_portfolio_management.doctype.investment_ledger_entry.investment_ledger_entry import process_cancellation
        process_cancellation(self.investment, self.name)
        self.status = "Cancelled"

    # def before_insert(self):
    #     if self.amended_from:
    #         self.status = "Submitted"

    def create_ledger_entry(self, cancel=False):
        args = {
            "investment": self.investment,
            "posting_date": self.posting_date,
            "transaction_type": "Return",
            "document_date": self.return_date,
            "remarks": self.remarks or f"Return: {self.return_type}",
            "voucher_no": self.name
        }
        
        amount = self.amount
        units = self.units_affected or 0.0
        
        if units > 0:
            args["debit_amount"] = amount
            args["units_in"] = units
                
        create_investment_ledger_entry(args)

    def create_journal_entry(self):
        inv_doc = frappe.get_doc("Investment", self.investment)
        
        jv = frappe.new_doc("Journal Entry")
        jv.posting_date = self.posting_date
        jv.voucher_type = "Journal Entry"
        jv.company = self.company
        jv.remark = f"Return Entry for {self.name}"
        jv.custom_return_of_investment = self.name
        
        # Credit Income Account
        income_account = self.get_income_account_from_settings()
        if not income_account:
             # Fallback
            income_account = frappe.get_cached_value('Company', self.company, 'default_income_account')
            
        if not income_account:
            frappe.throw(f"Default Income Account not set in Investment Account Settings for {self.company} nor in Company master.")
            
        jv.append('accounts', {
            'account': income_account,
            'credit_in_account_currency': self.amount,
            'cost_center': frappe.get_cached_value('Company',  self.company,  'cost_center')
        })
        
        # Investment Account
        # If units_affected > 0, it means the return is reinvested (DRIP).
        # We assume if units are affected, it increases the asset value instead of cash.
        
        debit_account = inv_doc.bank_account
        if self.units_affected > 0:
             debit_account = inv_doc.investment_account
             
        jv.append('accounts', {
            'account': debit_account,
            'debit_in_account_currency': self.amount,
            'cost_center': frappe.get_cached_value('Company',  self.company,  'cost_center')
        })
            
        try:
            jv.save()
            jv.submit()
            frappe.msgprint(f"Journal Entry {jv.name} created successfully")
            
        except Exception as e:
            frappe.throw(f"Failed to create Journal Entry: {str(e)}")

    def get_income_account_from_settings(self):
        return frappe.db.get_value("Default Account", 
            {"company": self.company, "parenttype": "Investment Account Settings"}, 
            "deafult_income_account"
        )

