import frappe
from frappe.model.document import Document
from frappe.utils import flt
from investment_portfolio_management.investment_portfolio_management.doctype.investment_ledger_entry.investment_ledger_entry import create_investment_ledger_entry

class ExitInvestment(Document):
    def validate(self):
        if not self.posting_date:
            self.posting_date = frappe.utils.nowdate()
            
        self.calculate_financials()
        self.validate_units()

    def calculate_financials(self):
        self.exit_amount = flt(self.units_sold) * flt(self.exit_price)
        self.net_amount = self.exit_amount - flt(self.charges)
        
        # Calculate P&L
        if self.investment:
            inv_doc = frappe.get_doc("Investment", self.investment)
            buy_price = flt(inv_doc.price_per_unit)
            
           
            cost_of_sold = flt(self.units_sold) * buy_price
            
            # P&L = Net Amount - Cost
            self.pnl = self.net_amount - cost_of_sold

    def validate_units(self):
        # Check if we have enough balance units
        if self.is_new():
            last_entry = frappe.db.get_value("Investment Ledger Entry", 
                {"investment": self.investment}, 
                ["balance_units"], 
                order_by="posting_date desc, creation desc", 
                as_dict=1
            )
            bal_units = flt(last_entry.balance_units) if last_entry else 0.0
            
            if flt(self.units_sold) > bal_units:
                frappe.throw(f"Insufficient units to sell. Available: {bal_units}, Requested: {self.units_sold}")

    def on_submit(self):
        self.create_ledger_entry()
        self.create_journal_entry()
        self.update_investment_status()
        self.status = "Submitted"

    def on_cancel(self):
        from investment_portfolio_management.investment_portfolio_management.doctype.investment_ledger_entry.investment_ledger_entry import process_cancellation
        process_cancellation(self.investment, self.name)
        self.update_investment_status()
        self.status = "Cancelled"
        
    def before_insert(self):
        if self.amended_from:
            self.status = "Submitted"

    def create_ledger_entry(self, cancel=False):
        args = {
            "investment": self.investment,
            "posting_date": self.posting_date,
            "transaction_type": "Exit",
            "document_date": self.exit_date,
            "remarks": self.remarks or f"Exit: {self.exit_type}",
            "pnl": self.pnl,
            "voucher_no": self.name
        }
        
        inv_doc = frappe.get_doc("Investment", self.investment)
        buy_price = flt(inv_doc.price_per_unit)
        cost_of_sold = flt(self.units_sold) * buy_price
        
        args["credit_amount"] = cost_of_sold
        args["units_out"] = self.units_sold
            
        create_investment_ledger_entry(args)

    def update_investment_status(self):
        last_entry = frappe.db.get_value("Investment Ledger Entry", 
            {"investment": self.investment}, 
            ["balance_units"], 
            order_by="posting_date desc, creation desc", 
            as_dict=1
        )
        
        bal_units = flt(last_entry.balance_units) if last_entry else 0.0
        
        status = "Active"
        if bal_units <= 0:
            status = "Closed"
            
        frappe.db.set_value("Investment", self.investment, "status", status)

    def create_journal_entry(self):
        inv_doc = frappe.get_doc("Investment", self.investment)
        
        jv = frappe.new_doc("Journal Entry")
        jv.posting_date = self.posting_date
        jv.voucher_type = "Journal Entry"
        jv.company = self.company
        jv.remark = f"Exit Entry for {self.name}"       
        jv.custom_exit_investment = self.name
        
        #  credit the COST of the units sold.
       
        buy_price = flt(inv_doc.price_per_unit)
        cost_of_sold = flt(self.units_sold) * buy_price
        
        jv.append('accounts', {
            'account': inv_doc.investment_account,
            'credit_in_account_currency': cost_of_sold,
            'cost_center': frappe.get_cached_value('Company',  self.company,  'cost_center')
        })
        
        #  Investment Account
        #  debit the NET AMOUNT received (after charges).
        jv.append('accounts', {
            'account': inv_doc.bank_account,
            'debit_in_account_currency': self.net_amount,
            'cost_center': frappe.get_cached_value('Company',  self.company,  'cost_center')
        })
        
        
        if self.pnl > 0:
            income_account = self.get_income_account_from_settings()
            if not income_account:
                 # Fallback to Company Default if not in Settings (optional, but safer)
                income_account = frappe.get_cached_value('Company', self.company, 'default_income_account')

            if not income_account:
                frappe.throw(f"Default Income Account not set in Investment Account Settings for {self.company} nor in Company master.")
                
            jv.append('accounts', {
                'account': income_account,
                'credit_in_account_currency': self.pnl,
                'cost_center': frappe.get_cached_value('Company',  self.company,  'cost_center')
            })
        elif self.pnl < 0:
            expense_account = frappe.get_cached_value('Company', self.company, 'default_expense_account')
            if not expense_account:
                frappe.throw("Default Expense Account not set in Company. Please set it to book Losses.")
                
            jv.append('accounts', {
                'account': expense_account,
                'debit_in_account_currency': abs(self.pnl),
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

