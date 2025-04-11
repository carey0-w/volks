from odoo import api, fields, models
from odoo.exceptions import ValidationError

class SalesQuotation(models.Model):
    _name = "sales.quotation" 
    _inherit = ['mail.thread']
    _description = "Sales Quotation"
    
    name = fields.Char(string='Quotation Id', required=True, tracking=True, default='New')
    uola_sale_quo_id = fields.Char(string='UOLA Sale Quo Id')
    uola_sale_quo_date = fields.Date(string='Tanggal Penawaran')
    uola_sale_quo_number = fields.Char(string='Nomor Penawaran')
    uola_sale_quo_contact_id = fields.Char(string='Contact')
    uola_sale_quo_brand_id = fields.Char(string='Brand')
    partner_id = fields.Many2one('project.project', string='Project')
    user_id = fields.Many2one('res.users', string='User')
    uola_sale_quo_location_id = fields.Char(string='Location')
    uola_sale_quo_margin = fields.Char(string='Margin')
    uola_sale_quo_remarks = fields.Text(string='Remarks')
    uola_main_ids = fields.One2many('sales.quotation.main', 'uola_main_id', string='Main')
    
    
    # Membuat nomor quotation secara otomatis sesuai dengan tahun terkoneksi dengan sequence.xml
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'New':
                sequence = self.env['ir.sequence'].next_by_code('sales.quotation')
                if not sequence:
                    raise ValidationError("Tidak dapat menghasilkan nomor invoice. Pastikan sequence 'invoice' sudah dikonfigurasi.")
                vals['name'] = sequence
        return super().create(vals_list)
    
    # Menghubungkan user 
    def get_user_info(self):
        for record in self:
            if record.user_id:
                user_name = record.user_id.name
                user_email = record.user_id.login
                print(f"Pengguna: {user_name}, Email: {user_email}")
            else:
                print("Tidak ada pengguna terkait.")
                                

class SalesQuotationMain(models.Model):
    _name = "sales.quotation.main" 
    _description = "Main Sales Quotation"
    _rec_name = "uola_sale_quo_ref"
    
    uola_main_id = fields.Many2one('sales.quotation', string='Main Id')
    uola_sale_quo_ref = fields.Char(string='Referensi')
    uola_sale_quantity = fields.Float(string='Qty')
    uola_sale_unit_price = fields.Float(string='Unit Price')
    uola_sale_amount = fields.Float(string='Amount', compute='_compute_amount', store=True)
    uola_sale_tax = fields.Float(string='Tax', compute='_compute_tax_11_percent', store=True)
    uola_sale_total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)
    # invoice_content_ids = fields.One2many('uola.invoice', 'quotation_id', string='Invoice Contents')
    
    
    # Menghitung jumlah quantity dan unit price tanpa pajak            
    @api.depends('uola_sale_quantity', 'uola_sale_unit_price')
    def _compute_amount(self):
        for record in self:
            record.uola_sale_amount = record.uola_sale_quantity * record.uola_sale_unit_price

    # Menghitung total dengan pajak 11%
    @api.depends('uola_sale_amount')
    def _compute_tax_11_percent(self):
        for record in self:
            record.uola_sale_tax = record.uola_sale_amount * 0.11  # 11% tax

    # Total keseluruhan dengan pajak 11%
    @api.depends('uola_sale_amount', 'uola_sale_tax')
    def _compute_total_amount(self):
        for record in self:
            record.uola_sale_total_amount = record.uola_sale_amount + record.uola_sale_tax