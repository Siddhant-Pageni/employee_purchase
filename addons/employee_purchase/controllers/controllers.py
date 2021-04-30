import base64
from collections import OrderedDict
from odoo import http, _
from odoo.http import request
from odoo.exceptions import MissingError
from odoo.tools import image_process
from odoo.addons.web.controllers.main import Binary
from odoo.addons.portal.controllers.portal import pager as portal_pager
import logging
from odoo.osv.expression import OR

_logger = logging.getLogger(__name__)


class EmployeePurchase(http.Controller):
    MANDATORY_FIELDS = [
        'product_id',
        'purchase_qty',
        'vendor_id'
    ]
    OPTIONAL_FIELDS = []

    _items_per_page = 20

    @http.route('/employee', type='http', auth="user", website=True)
    def portal_employee(self, page=1, date_begin=None, date_end=None,
                        sortby=None, filterby=None, search=None,
                        search_in='content', groupby=None, **kw):
        values = {}
        user = request.env['res.users'].sudo().browse(request.session.uid)
        # TODO: maybe use groups?
        if user.employee_id:
            if user.employee_id.is_manager:
                employee_list = user.employee_id.child_ids.ids
            else:
                employee_list = [user.employee_id.id]
            # Only allowed EPs
            domain = [
                ('employee_id', 'in', employee_list)
            ]
            # Date Filter
            if date_begin and date_end:
                domain += [('create_date', '>', date_begin),
                           ('create_date', '<=', date_end)]
            # Sort
            searchbar_sortings = {
                'date': {'label': _('Newest'),
                         'order': 'create_date desc, id desc'},
                'name': {'label': _('Name'), 'order': 'name asc, id asc'},
                'stage': {'label': _('Stage'), 'order': 'state'},
            }
            if not sortby:
                sortby = 'date'
            sort_order = searchbar_sortings[sortby]['order']
            # Filter
            searchbar_filters = {
                'all': {
                    'label': _('All'),
                    'domain':
                    [
                        ('state', 'in', ['draft', 'approved', 'rejected',
                                         'purchase in progress',
                                         'ready to pick-up', 'done']
                         )]},
                'draft': {
                    'label': _('Draft'),
                    'domain': [('state', '=', 'draft')]},
                'approved': {
                    'label': _('Approved'),
                    'domain': [('state', 'in', ['approved'])]},
                'rejected': {
                    'label': _('Rejected'),
                    'domain': [('state', '=', 'rejected')]},
                'purchase in progress': {
                    'label': _('Purchase in Progress'),
                    'domain': [('state', '=', 'purchase in progress')]},
                'ready to pick-up': {
                    'label': _('Ready to pick-up'),
                    'domain': [('state', '=', 'ready to pick-up')]},
                'done': {
                    'label': _('Done'),
                    'domain': [('state', '=', 'done')]},
            }
            if not filterby:
                filterby = 'all'
            domain += searchbar_filters[filterby]['domain']
            # search
            searchbar_inputs = {
                'name': {
                    'input': 'name',
                    'label': _('Search in Order Number')},
                'date': {
                    'input': 'date',
                    'label': _('Search in Date')},
                'state': {
                    'input': 'state',
                    'label': _('Search in State')},
                'all': {
                    'input': 'all',
                    'label': _('Search in All')},
            }
            # search
            if search and search_in:
                search_domain = []
                if search_in in ('name', 'all'):
                    search_domain = OR([search_domain,
                                       [('name', 'ilike', search)]])
                if search_in in ('date', 'all'):
                    search_domain = OR([search_domain,
                                       [('create_date', 'ilike', search)]])
                if search_in in ('state', 'all'):
                    search_domain = OR([search_domain,
                                       [('state', 'ilike', search)]])
                domain += search_domain

            # get Data

            EP = request.env['employee_purchase.employee_purchase'].sudo()

            ep_count = EP.search_count(domain)

            pager = portal_pager(
                url="/employee",
                url_args={
                    'date_begin': date_begin,
                    'date_end': date_end,
                    'sortby': sortby,
                    'filterby': filterby,
                    'search_in': search_in,
                    'search': search},
                total=ep_count,
                page=page,
                step=self._items_per_page
            )

            orders = EP.search(
                domain,
                order=sort_order,
                limit=self._items_per_page,
                offset=pager['offset']
            )
            values.update({
                'orders': orders.sudo(),
                'is_manager': user.employee_id.is_manager,
                'date': date_begin,
                'page_name': 'employee',
                'pager': pager,
                'searchbar_sortings': searchbar_sortings,
                'sortby': sortby,
                'searchbar_filters': OrderedDict(
                    sorted(searchbar_filters.items())),
                'filterby': filterby,
                'default_url': '/employee',
                'searchbar_inputs': searchbar_inputs,
                'search_in': search_in,
                'search': search,
            })
            request.session['my_ep_history'] = orders.ids[:100]

            def attachment_count(order):
                att_count = request.env['ir.attachment'].sudo()\
                    .search_count(
                        [
                            ('res_model', '=',
                             'employee_purchase.employee_purchase'),
                            ('res_id', '=',
                             order.id)
                        ]
                    )
                return att_count
            values.update({
                'attachment_count': attachment_count,
                })
            return http.request.render(
                'employee_purchase.employee_purchase_list',
                values)
        return request.redirect('/my')

    @http.route(['/employee/<int:order_id>'], type='http',
                auth="public", website=True)
    def portal_employee_purchase_order(self, order_id=None,
                                       access_token=None, **kw):
        values = {}
        user = request.env['res.users'].sudo().browse(request.session.uid)
        if user.employee_id:
            if user.employee_id.is_manager:
                employee_list = user.employee_id.child_ids.ids
            else:
                employee_list = [user.employee_id.id]
            hasAccess = 0
            try:
                if(request.env['employee_purchase.employee_purchase'].sudo()
                   .browse(order_id).employee_id.id in employee_list):
                    hasAccess = 1
            except (MissingError):
                return request.redirect('/my')
            if (hasAccess):
                order = request.env['employee_purchase.employee_purchase']\
                    .sudo().browse(order_id)
                values.update({
                    'order': order.sudo(),
                    'is_manager': user.employee_id.is_manager,
                    'approve_url': "/employee/action/approve/" + str(order_id),
                    'reject_url': "/employee/action/reject/" + str(order_id),
                    'buy_url': "/employee/action/buy/" + str(order_id),
                })

                def resize_to_48(b64source):
                    if not b64source:
                        b64source = base64.b64encode(Binary.placeholder())
                    return image_process(b64source, size=(48, 48))
                values.update({
                    'resize_to_48': resize_to_48,
                })
                return request.render(
                    "employee_purchase.employee_purchase_order",
                    values)
            else:
                return request.redirect('/my')
        else:
            return request.redirect('/my')

    @http.route(['/employee/action/<string:act>/<int:oid>'], type='http',
                auth="public", website=True)
    def action_order(self, act, oid, **kw):
        user = request.env['res.users'].sudo().browse(request.session.uid)
        if user.employee_id:
            if act == 'approve' or act == 'reject':
                if user.employee_id.is_manager:
                    # manager click Approve/Reject
                    employee_list = user.employee_id.child_ids.ids
                    ep = request.env['employee_purchase.employee_purchase']\
                        .sudo().browse(oid)
                    if ep.employee_id.id in employee_list\
                       and ep.state == "draft":
                        # Manager has access to this employee's orders
                        # and the state is 'draft'
                        if act == 'approve':
                            ep.write({
                                'state': 'approved',
                            })
                        else:
                            ep.write({
                                'state': 'rejected',
                            })
                        return request.redirect('/employee/%s' % (oid))
                return request.redirect('/employee')
            elif act == 'buy':
                if not user.employee_id.is_manager:
                    # employee clicked Buy Now
                    ep = request.env['employee_purchase.employee_purchase']\
                        .sudo().browse(oid)
                    if ep.employee_id.id == user.employee_id.id\
                       and ep.state == "approved":
                        # Employee has access to this order
                        # and the state is 'approved'
                        supplierInfo = ep.supplierinfo_id
                        poCreateVals = {
                            'user_id': user.id,
                            'partner_id': supplierInfo.name.id,
                            'ep_id': ep.id,
                        }
                        createdPO = request.env['purchase.order'].sudo()\
                            .create(poCreateVals)
                        if user.employee_id.tax_id:
                            tax_used = user.employee_id.tax_id
                        else:
                            tax_used = user.company_id.account_purchase_tax_id
                        polCreateVals = {
                            'order_id': createdPO.id,
                            'product_id': ep.product_id.id,
                            'price_unit': supplierInfo.price,
                            'taxes_id': [(6, 0, [tax_used.id])],
                            'product_qty': ep.purchase_qty,
                            'name': ep.product_id.display_name,
                        }
                        request.env['purchase.order.line'].sudo()\
                            .create(polCreateVals)
                        ep.write({
                            'purchase_id': createdPO.id,
                            'state': 'purchase in progress',
                        })
                        return request.redirect('/employee/%s' % (oid))
                return request.redirect('/employee')
            else:
                # Invalid action
                return request.redirect("/employee")
        return request.redirect('/my')

    @http.route('/employee/new_purchase', type="http", auth="user",
                website=True)
    def employee_new_purchase(self, redirect=None, **post):
        values = {}
        user = request.env['res.users'].sudo().browse(request.session.uid)
        if user.employee_id:
            if user.employee_id.is_manager:
                return request.redirect('/my')

            values.update({
                'error': {},
                'error_message': [],
            })
            if post and request.httprequest.method == 'POST':
                _logger.warning("Post Values" + str(post))
                # Validate and create Employee purchase
                error, error_message = self.details_form_validate(post)
                values.update({'error': error, 'error_message': error_message})
                values.update(post)
                if not error:
                    createVals = {
                        'product_id': int(post.get('product_id')),
                        'purchase_qty': int(post.get('purchase_qty')),
                        'supplierinfo_id': int(post.get('vendor_id')),
                        'employee_id': user.employee_id.id,
                    }
                    ep = request.env['employee_purchase.employee_purchase']\
                        .sudo().create(createVals)
                    if redirect:
                        return request.redirect(redirect)
                    return request.redirect('/employee/%s' % (ep.id))

            # collect data for the template
            products_domain = [(
                'product_tmpl_id.categ_id.id',
                'in',
                user.employee_id.allowed_categories.ids)]
            products = request.env['product.product'].sudo()\
                .search(products_domain)
            values.update({
                'products': products,
                'allowed_quantities': list(
                    range(
                            1, int(user.employee_id.max_allowed_quantity) + 1)
                        ),
            })
            return http.request.render(
                'employee_purchase.employee_purchase_create',
                values)
        return request.redirect('/my')

    @http.route(['/employee/vendor_infos/<int:pid>'], type='json',
                auth="public", methods=['POST'], website=True)
    def vendor_infos(self, pid, **kw):
        allSupplierInfo = request.env['product.supplierinfo'].sudo().search([])
        try:
            selectedProduct = request.env['product.product'].sudo().browse(pid)
        except MissingError:
            return dict(
                vendors=[]
            )
        supplierInfo = []
        for si in allSupplierInfo:
            if si.product_id:
                if si.product_id.id == pid:
                    supplierInfo.append(si)
            elif si.product_tmpl_id:
                if si.product_tmpl_id.id == selectedProduct.product_tmpl_id.id:
                    supplierInfo.append(si)
        return dict(
            vendors=[
                (si.id, si.name.name + ' - ' + str(si.price))
                for si in supplierInfo],
        )

    def _pricingDetails(self, user, supplierinfo_id, amount, product_id):
        if user.employee_id.tax_id:
            tax_used = user.employee_id.tax_id
        else:
            tax_used = user.company_id.account_purchase_tax_id
        unit_price = request.env['product.supplierinfo'].sudo()\
            .browse(supplierinfo_id).price
        net_price = unit_price * float(amount)
        if tax_used.amount_type == 'percent':
            product_tax = net_price * tax_used.amount / 100
        elif tax_used.amount_type == 'fixed':
            product_tax == tax_used.amount
        else:
            # TODO: handle other tax types
            # for this test case assuming amount_type=percentage
            return dict(
                net_price=net_price,
                product_tax="Tax type not handled",
                gross_price="N/A",
            )
        gross_price = net_price + product_tax
        product = request.env['product.product'].sudo().browse(product_id)
        return dict(
            product_name=product.display_name,
            product_categ_name=product.product_tmpl_id.categ_id.complete_name,
            unit_price=unit_price,
            qty=amount,
            net_price=net_price,
            product_tax=product_tax,
            gross_price=gross_price,
        )

    @http.route(['/employee/pricingDetails/'], type='json',
                auth="public", methods=['POST'], website=True)
    def pricingDetails(self, **kw):
        product_id = int(kw.get('product'))
        vendor_id = int(kw.get('vendor'))
        amount = float(kw.get('amount'))
        user = request.env['res.users'].sudo().browse(request.session.uid)
        if user.employee_id:
            if user.employee_id.tax_id:
                tax_used = user.employee_id.tax_id
            else:
                tax_used = user.company_id.account_purchase_tax_id
            unit_price = request.env['product.supplierinfo'].sudo()\
                .browse(vendor_id).price
            net_price = unit_price * float(amount)
            if tax_used.amount_type == 'percent':
                product_tax = net_price * tax_used.amount / 100
            elif tax_used.amount_type == 'fixed':
                product_tax == tax_used.amount
            else:
                # TODO: handle other tax types
                # for this test case assuming amount_type=percentage
                return dict(
                    net_price=net_price,
                    product_tax="Tax type not handled",
                    gross_price="N/A",
                )
            gross_price = net_price + product_tax
            product = request.env['product.product'].sudo().browse(product_id)
            return dict(
                product_name=product.display_name,
                product_categ_name=product.product_tmpl_id
                                    .categ_id.complete_name,
                unit_price=unit_price,
                qty=amount,
                net_price=net_price,
                product_tax=product_tax,
                gross_price=gross_price,
            )
        return

    def details_form_validate(self, data):
        error = dict()
        error_message = []
        for field_name in self.MANDATORY_FIELDS:
            if not data.get(field_name):
                error[field_name] = 'missing'

        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))

        unknown = [k for k in data if k not in self.MANDATORY_FIELDS
                   + self.OPTIONAL_FIELDS]
        if unknown:
            error['common'] = 'Unknown field'
            error_message.append("Unknown field '%s'" % ','.join(unknown))

        return error, error_message
