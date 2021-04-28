# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from collections import OrderedDict
import io
from PIL import Image

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, Form, tagged
import logging

_logger = logging.getLogger(__name__)


@tagged('employee_purchase')
class TestEmployeePurchase(TransactionCase):

    def _get_product_template_attribute_value(self, product_attribute_value, template):
        """
            Return the `product.template.attribute.value` matching
                `product_attribute_value` for self.

            :param: recordset of one product.attribute.value
            :return: recordset of one product.template.attribute.value if found
                else empty
        """
        return template.valid_product_template_attribute_line_ids.filtered(
            lambda l: l.attribute_id == product_attribute_value.attribute_id
        ).product_template_value_ids.filtered(
            lambda v: v.product_attribute_value_id == product_attribute_value
        )

    def setUp(self):
        res = super(TestEmployeePurchase, self).setUp()

        self.ofc_tshrt = self.env['product.template'].sudo().browse(self.ref('employee_purchase.product_delivery_offc_tshirt'))
        self.plain_jacket = self.env['product.template'].sudo().browse(self.ref('employee_purchase.product_delivery_plain_jacket'))

        self.color_red = self.env['product.attribute.value'].sudo().browse(self.ref('employee_purchase.product_attribute_color_1'))
        self.size_small = self.env['product.attribute.value'].sudo().browse(self.ref('employee_purchase.product_attribute_size_1'))

        ofc_tshirt_color_red = self._get_product_template_attribute_value(self.color_red, self.ofc_tshrt)
        ofc_tshirt_size_small = self._get_product_template_attribute_value(self.size_small, self.ofc_tshrt)

        plain_jacket_color_red = self._get_product_template_attribute_value(self.color_red, self.plain_jacket)
        plain_jacket_size_small = self._get_product_template_attribute_value(self.size_small, self.plain_jacket)

        combination = ofc_tshirt_color_red + ofc_tshirt_size_small
        self.ofc_tshirt_red_small = self.ofc_tshrt._get_variant_for_combination(combination)

        combination = plain_jacket_color_red + plain_jacket_size_small
        self.plain_jacket_red_small = self.plain_jacket._get_variant_for_combination(combination)

        return res

    def test_01_create_EmployeePurchase(self):
        # Test successful creation
        self.assertIsNotNone(
            self.env['employee_purchase.employee_purchase'].create({
                'employee_id': self.ref('employee_purchase.employee_saurav'),
                'product_id': self.ofc_tshirt_red_small.id,
                'supplierinfo_id': self.ref('employee_purchase.product_supplierinfo_ofc_tshrt_pkr'),
                'purchase_qty': 2,
            }), "Employee Purchase not created."
        )

    def test_02_EmployeePurchase_constraints(self):
        # Test max quantity restriction
        with self.assertRaises(
            ValidationError,
            msg="Order quantity must not be greater than\
                 the defined threshold."):
            self.env['employee_purchase.employee_purchase'].create({
                'employee_id': self.ref('employee_purchase.employee_saurav'),
                'product_id': self.ofc_tshirt_red_small.id,
                'supplierinfo_id': self.ref('employee_purchase.product_supplierinfo_ofc_tshrt_pkr'),
                'purchase_qty': 3,
            })

        # Test if product and Supplier info matches
        with self.assertRaises(
                ValidationError,
                msg="Product must match with Supplier Info"):
            self.env['employee_purchase.employee_purchase'].create({
                'employee_id': self.ref('employee_purchase.employee_saurav'),
                'product_id': self.plain_jacket_red_small.id,
                'supplierinfo_id': self.ref('employee_purchase.product_supplierinfo_ofc_tshrt_pkr'),
                'purchase_qty': 2,
            })

        # Create one order and reject it
        self.env['employee_purchase.employee_purchase'].create({
                'employee_id': self.ref('employee_purchase.employee_saurav'),
                'product_id': self.ofc_tshirt_red_small.id,
                'supplierinfo_id': self.ref(
                    'employee_purchase.product_supplierinfo_ofc_tshrt_pkr'),
                'purchase_qty': 2,
                'state': 'rejected',
            })
        # Assert that the user is no longer able to create EPs for this month
        with self.assertRaises(
                ValidationError,
                msg="Employee Purchase is created even when there is \
                    a rejected order on the same month"):
            self.env['employee_purchase.employee_purchase'].create({
                'employee_id': self.ref('employee_purchase.employee_saurav'),
                'product_id': self.ofc_tshirt_red_small.id,
                'supplierinfo_id': self.ref('employee_purchase.product_supplierinfo_ofc_tshrt_pkr'),
                'purchase_qty': 2,
            })

    def test_03_Computed_Values(self):
        # Test if the computed fields are working as expected
        ep1 = self.env['employee_purchase.employee_purchase'].create({
                'employee_id': self.ref('employee_purchase.employee_saurav'),
                'product_id': self.ofc_tshirt_red_small.id,
                'supplierinfo_id': self.ref(
                    'employee_purchase.product_supplierinfo_ofc_tshrt_pkr'),
                'purchase_qty': 2,
                'state': 'rejected',
            })
        ep1._compute_prices()

        net_price = ep1.purchase_qty * ep1.supplierinfo_id.price
        product_tax = net_price * self.env['account.tax'].sudo()\
            .browse(self.ref('employee_purchase.tax_10_percentage')).amount/100
        gross_price = net_price + product_tax

        self.assertEqual(ep1.net_price, net_price)
        self.assertEqual(ep1.tax_amount, product_tax)
        self.assertEqual(ep1.gross_price, gross_price)
