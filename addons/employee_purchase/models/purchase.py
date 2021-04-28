from odoo import models, fields


class PurchaseOrder(models.Model):
    _inherit = ['purchase.order']

    ep_id = fields.Many2one('employee_purchase.employee_purchase',
                            string="Related Emplyee Purchase")
