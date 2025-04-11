from venv import logger
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from num2words import num2words

class Invoice(models.Model):
    _name = "uola.invoice"
    _inherit = ['mail.thread']
    _description = "Sales Invoice"
    
    name = fields.Char(string='Invoice No.', default='New Draft')
    inv_date = fields.Date(string='Invoice Date', default=fields.Date.context_today)
    company_id = fields.Many2one('res.partner', string='Addressed to', tracking=True)
    company_address = fields.Char(string='Address')
    partner_id = fields.Many2one('project.project', string='Project')
    uola_inv_po_number = fields.Char('PO. No.')
    uola_inv_do_number = fields.Char('DO. No.')
    phone = fields.Char(string='Phone')
    invoice_payment_term_id = fields.Many2one('account.payment.term', string='Due Date')
    currency_id = fields.Many2one('res.currency', string='Currency')
    bank_account_id = fields.Many2one('res.partner.bank', string='Bank Account') 
    display_date = fields.Char(string='Display Date', compute='_compute_display_date', store=False, default='Date Today')
    state = fields.Selection([
         ('draft', 'Draft'), ('confirmed', 'Confirmed'),
         ('done', 'Done'), ('cancel', 'Cancelled')
        ], default="draft")
    quotation_id = fields.Many2one('sales.quotation', string="Sales Quotation")
    inv_content_ids = fields.One2many('invoice.content', 'inv_content_id', string="Content")
    
    # Membuat nomor invoice secara otomatis sesuai dengan tahun terkoneksi dengan sequence.xml
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'New':
                sequence = self.env['ir.sequence'].next_by_code('uola.invoice')
                if not sequence:
                    raise ValidationError("Tidak dapat menghasilkan nomor invoice. Pastikan sequence 'invoice' sudah dikonfigurasi.")
                vals['name'] = sequence
        return super().create(vals_list)
    
    def action_confirm (self):
        for rec in self:
            rec.state = 'confirmed'

    def action_done (self):
        for rec in self:
            rec.state = 'done'

    def action_cancel (self):
        for rec in self:
            rec.state = 'cancel'
    
    @api.onchange('company_id')
    # Membuat phone terkonek saat memilih company
    def _onchange_company_id(self):
        if self.company_id:
            self.phone = self.company_id.phone
            if self._origin:
                self._origin.write({'phone': self.company_id.phone})
        else:
            self.phone = False
            if self._origin:
                self._origin.write({'phone': False})
                
    # Memunculkan alamat company saat memilih company
        if self.company_id:
            address = self.company_id.street or ""
            if self.company_id.city:
                address += f", {self.company_id.city}"
            if self.company_id.state_id:
                address += f", {self.company_id.state_id.name}"
            if self.company_id.country_id:
                address += f", {self.company_id.country_id.name}"
            self.company_address = address
        else:
            self.company_address = False
        
            
    # Payment terms
    @api.depends('partner_id')
    def _compute_invoice_payment_term_id(self):
        for move in self:
            move = move.with_company(move.company_id)
            if move.is_sale_document(include_recipts=True) and move.partner_id.property_payment_term_id:
                move.invoice_payment_term_id = move.partner_id.property_payment_term_id.id
            elif move.is_purchase_document(include_invoices=True) and move.partner_id.property_supplier_payment_term_id:
                move.invoice_payment_term_id = move.partner_id.property_supplier_payment_term_id.id
            else:
                move.invoice_payment_term_id = False
                
    # Tanggal untuk invoice
    @api.depends('inv_date')
    def _compute_display_date(self):
        for record in self:
            if record.inv_date:
                # Format tanggal sebagai "DD Month YYYY" (misalnya, "27 Febuari 2025")
                record.display_date = record.inv_date.strftime('%d %b %Y')
            else:
                record.display_date = False
                
    @api.onchange('bank_account_id')
    def _onchange_bank_account_id(self):
        if self.bank_account_id:
            # Misalnya, ingin otomatis mengisi jurnal berdasarkan bank
            bank_journal = self.env['account.journal'].search([
                ('type', '=', 'bank'),
                ('bank_account_id', '=', self.bank_account_id.id)
            ], limit=1)
            if bank_journal:
                self.journal_id = bank_journal.id
                
                
class InvoiceContent(models.Model):
    _name = "invoice.content"
    _description = "Sales Invoice Content"
    
    inv_content_id = fields.Many2one('uola.invoice', string="Invoice")
    # uola_inv_item_description = fields.Char(string="Item Description")
    uola_inv_qty = fields.Float(
        string='Qty', 
        related='inv_content_id.quotation_id.uola_main_ids.uola_sale_quantity', 
        store=True)
    uola_inv_unit_price = fields.Float(
        string='Unit Price',
        related='inv_content_id.quotation_id.uola_main_ids.uola_sale_unit_price',
        store=True)
    uola_inv_amount = fields.Float(
        string='Amount',
        related='inv_content_id.quotation_id.uola_main_ids.uola_sale_amount',
        store=True)
    uola_inv_discount = fields.Float(string='Discount')
    uola_inv_payment = fields.Float(string='Payment')
    uola_inv_freight = fields.Float(string='Freight')
    uola_inv_tax = fields.Float(
        string='Tax',
        related='inv_content_id.quotation_id.uola_main_ids.uola_sale_tax',
        store=True)
    uola_inv_total = fields.Float(
        string='Total Amount',
        related='inv_content_id.quotation_id.uola_main_ids.uola_sale_total_amount',
        store=True)
    uola_inv_say = fields.Char(string='Say', compute='_compute_uola_inv_say', store=True)
    quotation_id = fields.Many2one(
        'sales.quotation',
        string="Related Quotation",
        related='inv_content_id.quotation_id',
        store=True,
        readonly=True)
    main_unit_quotation= fields.Many2one(
        'sales.quotation.main',
        string="Item Description",
        domain="[('uola_main_id', '=', quotation_id)]")
    

    # Konversi total amount ke teks (say)
    @api.depends('uola_inv_total')
    def _compute_uola_inv_say(self):
        for record in self:
            if record.uola_inv_total:
                # Konversi angka ke teks dalam bahasa Inggris menggunakan num2words
                amount_words = num2words(record.uola_inv_total, lang='en')
                # Hilangkan koma dan tambahkan "rupiah"
                record.uola_inv_say = f"{amount_words} rupiah".replace(",", "").capitalize()
            else:
                record.uola_inv_say = "zero rupiah" 
    
   
