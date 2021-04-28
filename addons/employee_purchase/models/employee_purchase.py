from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime


class EmployeePurchase(models.Model):
    _name = 'employee_purchase.employee_purchase'
    _inherit = ['portal.mixin', 'mail.thread']
    _description = 'Employee Purchase'

    name = fields.Char(string='Order Number', required=True, copy=False,
                       readonly=True, states={'draft': [('readonly', False)]},
                       index=True, default=lambda self: _('New'))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('purchase in progress', 'Purchase in progress'),
        ('ready to pick-up', 'Ready to pick-up'),
        ('done', 'Done')
        ], string="Status", readonly=True, copy=False, default="draft")
    purchase_id = fields.Many2one('purchase.order', string='Related Purchase')
    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  required=True)
    user_id = fields.Many2one(related="employee_id.user_id")
    product_id = fields.Many2one('product.product', string="Product",
                                 required=True)
    supplierinfo_id = fields.Many2one('product.supplierinfo',
                                      string="Vendor Pricelist", required=True)
    vendor_id = fields.Many2one(related="supplierinfo_id.name",
                                string="vendor", required=True)
    purchase_qty = fields.Integer('Purchase Quantity', required=True)
    net_price = fields.Float(string='Net Price', compute="_compute_prices",
                             store=True)
    gross_price = fields.Float(string='Gross Price', compute="_compute_prices",
                               store=True)
    tax_amount = fields.Float(string='Tax Amount', compute="_compute_prices",
                              store=True)
    picking_date = fields.Date(string='Picking Date')
    signed_doc = fields.Binary(string="Signed Document")

    @api.model
    def create(self, vals):
        pqty = int(vals.get('purchase_qty'))
        employee = self.env['hr.employee'].sudo()\
            .browse(int(vals.get('employee_id')))
        ep_restriction = int(employee.max_allowed_quantity)

        # Validate Product Quantity Restriction
        if pqty > ep_restriction:
            raise ValidationError(
                        _("You cannot place an order of more than %s quantity because\
 it is the restricted amount for you.") % (ep_restriction))

        # Validate monthly rejected Orders
        year = datetime.now().year
        month = datetime.now().month
        order_this_month = self.env['employee_purchase.employee_purchase']\
            .sudo().search([
                ['create_date', '>=', datetime(year, month, 1)],
                ['employee_id', '=', int(vals.get('employee_id'))],
            ])
        for o in order_this_month:
            if o.state == 'rejected':
                raise ValidationError(
                        _("You cannot place an order for this month, because\
 your order %s was rejected by your manager.\
 Please place your order next month.") % (o.name))

        # Validate product matches with supplier info
        si = self.env['product.supplierinfo'].sudo()\
            .browse(int(vals.get('supplierinfo_id')))
        if si.product_id:
            if int(vals.get('product_id')) != si.product_id.id:
                raise ValidationError(
                    _("The Product does not match with the vendor Pricelist.")
                )
        else:
            template_products = self.env['product.product'].sudo()\
                .search([('product_tmpl_id', '=', si.product_tmpl_id.id)])
            if int(vals.get('product_id')) not in template_products.ids:
                raise ValidationError(
                    _("The Product does not match with the vendor Pricelist.")
                )

        # Calculate name
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'date_order' in vals:
                seq_date = fields.Datetime.context_timestamp(
                            self,
                            fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = self.env['ir.sequence'].next_by_code(
                        'employee.purchase',
                        sequence_date=seq_date) or _('New')
        ep = super(EmployeePurchase, self).create(vals)

        # Send creation email to manager
        template = self.env.ref('employee_purchase.ep_new_order')
        self.env['mail.template'].browse(template.id)\
            .send_mail(ep.id)
        return ep

    def write(self, vals):
        response = super(EmployeePurchase, self).write(vals)
        if 'state' in vals:
            if vals['state'] == 'approved':
                template = self.env.ref('employee_purchase.ep_approved')
                self.env['mail.template'].browse(template.id)\
                    .send_mail(self.id)
            elif vals['state'] == 'rejected':
                template = self.env.ref('employee_purchase.ep_rejected')
                self.env['mail.template'].browse(template.id)\
                    .send_mail(self.id)
        return response

    @api.depends('purchase_qty', 'supplierinfo_id')
    def _compute_prices(self):
        for record in self:
            net_price = record.purchase_qty * record.supplierinfo_id.price
            if record.employee_id.tax_id:
                usedTax = record.employee_id.tax_id
            else:
                usedTax = record.employee_id.company_id.account_purchase_tax_id
            if usedTax.amount_type == 'percent':
                product_tax = net_price * usedTax.amount / 100
            elif usedTax.amount_type == 'fixed':
                product_tax == usedTax.amount
            record.write({
                'net_price': net_price,
                'tax_amount': product_tax,
                'gross_price': net_price + product_tax,
            })

    def _compute_access_url(self):
        super(EmployeePurchase, self)._compute_access_url()
        for record in self:
            record.access_url = '/employee/%s' % (record.id)

    # TODO: Better if we do it using css?
    @api.model
    def get_state_tag_bg_color(self):
        for o in self:
            if o.state == "draft":
                return "#717171"
            elif o.state == "approved":
                return "#1391d2"
            elif o.state == "rejected":
                return "#d41616"
            elif o.state == "purchase in progress":
                return "#f719c1"
            elif o.state == "ready to pick-up":
                return "#289c3f"
            elif o.state == "done":
                return "#7ce217"
            else:
                return ""

    def action_ready_to_pickup(self):
        for record in self:
            template = record.env.ref('employee_purchase.ep_ready_to_pickup')
            record.env['mail.template'].browse(template.id)\
                .send_mail(record.id)
            record.write({
                'state': 'ready to pick-up'
            })

    def action_done(self):
        for record in self:
            record.write({
                'state': 'done'
            })
