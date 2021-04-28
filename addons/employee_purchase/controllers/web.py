from odoo import http
from odoo.addons.portal.controllers.web import Home
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class EmployeePurchaseHome(Home):
    @http.route()
    def index(self, *args, **kw):
        if request.session.uid and not request.env['res.users'].sudo()\
                .browse(request.session.uid).has_group('base.group_user'):
            # See if this is linked with any employee
            if(request.env['res.users'].sudo()
                    .browse(request.session.uid).employee_id):
                return http.local_redirect(
                    '/employee',
                    query=request.params,
                    keep_hash=True)
            else:
                return http.local_redirect(
                    '/my', query=request.params,
                    keep_hash=True)
        return super(Home, self).index(*args, **kw)

    def _login_redirect(self, uid, redirect=None):
        if not redirect and not request.env['res.users'].sudo()\
                .browse(uid).has_group('base.group_user'):
            # See if this is linked with any employee
            if(request.env['res.users'].sudo().browse(request.session.uid)
                    .employee_id):
                redirect = '/employee'
            else:
                redirect = '/my'
        return super(Home, self)._login_redirect(uid, redirect=redirect)

    @http.route('/web', type='http', auth="none")
    def web_client(self, s_action=None, **kw):
        if request.session.uid and not request.env['res.users'].sudo()\
                .browse(request.session.uid).has_group('base.group_user'):
            # See if this is linked with any employee
            if(request.env['res.users'].sudo()
                    .browse(request.session.uid).employee_id):
                return http.local_redirect(
                    '/employee',
                    query=request.params,
                    keep_hash=True)
            else:
                return http.local_redirect(
                    '/my',
                    query=request.params,
                    keep_hash=True)
        return super(Home, self).web_client(s_action, **kw)


class EmployeeCutomerPortal(CustomerPortal):
    @http.route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        if(request.env['res.users'].sudo().browse(request.session.uid)
           .employee_id):
            return http.local_redirect('/employee')
        else:
            values = self._prepare_portal_layout_values()
            return request.render("portal.portal_my_home", values)
