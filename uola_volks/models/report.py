from odoo import api, fields, models

class UolaInvoiceReport(models.AbstractModel):
    _name = 'report.uola_volks.inv_content_id'
    _description = 'Sales Invoice'

    def _get_report_values(self, docids, data=None):
        docs = self.env['invoice.content'].browse(docids)
        company = self.env.company  # Mengambil data perusahaan aktif
        return {
            'doc_ids': docids,
            'doc_model': 'invoice.content',
            'docs': docs,
            'company': company,  # Pastikan company dimasukkan dalam konteks
        }