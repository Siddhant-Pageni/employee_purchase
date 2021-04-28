# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class employee_purchase(models.Model):
#     _name = 'employee_purchase.employee_purchase'
#     _description = 'employee_purchase.employee_purchase'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
