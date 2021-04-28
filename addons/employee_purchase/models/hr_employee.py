from odoo import api, models, fields


class Employee(models.Model):
    _inherit = ['hr.employee']

    is_manager = fields.Boolean(string="Is Manager",
                                compute="_compute_is_manager", store=True,
                                compute_sudo=True)
    allowed_categories = fields.Many2many(
        'product.category',
        string="Allowed Categories")
    max_allowed_quantity = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3')
        ], string="Max. Allowed Quantity", copy=False, default='1')
    tax_id = fields.Many2one('account.tax', string="Custom Tax")

    @api.depends('child_ids')
    def _compute_is_manager(self):
        for record in self:
            if record.child_ids:
                record.is_manager = True
            else:
                record.is_manager = False
