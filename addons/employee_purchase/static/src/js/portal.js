odoo.define('employee_purchase.portal', function (require) {
    'use strict';
    
    var publicWidget = require('web.public.widget');
    const Dialog = require('web.Dialog');
    const {_t, qweb} = require('web.core');
    const ajax = require('web.ajax');
    
    publicWidget.registry.employeePurchaseCreate = publicWidget.Widget.extend({
        selector: '.o_employee_purchase_create',
        events: {
            'change select[name="product_id"]': '_onProductChange',
            'change select[name="vendor_id"]': '_updatePricing',
            'change select[name="purchase_qty"]': '_updatePricing'
        },
        /**
         * @override
         */
        start: function () {
            var def = this._super.apply(this, arguments);

            this.$vendor = this.$('select[name="vendor_id"]');
            this.$vendorOptions = this.$vendor.filter(':enabled').find('option:not(:first)');
            // this._adaptCreateForm();

            return def;
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * @private
         */
        _onProductChange: function () {
            $('select[name="purchase_qty"]').val('');
            $('#product_line_name').html('');
            $('#product_line_categ_name').html('');
            $('#product_line_price').html('');
            $('#product_line_product_qty').html('');
            $('#product_line_price_subtotal').html('');
            $('#product_net_price').html('');
            $('#product_taxes').html('');
            $('#gross_price').html('');
            if(!this.$('select[name="product_id"]')){
                return;
            }
            this._rpc({
                route: "/employee/vendor_infos/" + $('select[name="product_id"]').val(),
            }).then(function (data){
                var selectVendor = $('select[name="vendor_id"]');
                if (selectVendor.data('init')===0 || selectVendor.find('option').length===1) {
                    if (data.vendors.length) {
                        selectVendor.html('');
                        selectVendor.append($('<option>').text('').attr('value', ''))
                        _.each(data.vendors, function (x) {
                            var opt = $('<option>').text(x[1])
                                .attr('value', x[0]);
                            selectVendor.append(opt);
                        });
                        // Reset the value in purchase quantity
                    }
                    selectVendor.data('init', 0);
                } else {
                    selectVendor.data('init', 0);
                }
            });
            this._updatePricing();
        },

        _updatePricing: function(){
            if(!this.$('select[name="vendor_id"]')){
                return;
            }
            var productSelected = $('select[name="product_id"]').val();
            var vendorSelected = $('select[name="vendor_id"]').val();
            var amountSelected = $('select[name="purchase_qty"]').val();
            if(productSelected=='' || vendorSelected == '' || amountSelected == ''){
                return
            }
            this._rpc({
                route: "/employee/pricingDetails/",
                params: {
                    product: productSelected,
                    vendor: vendorSelected,
                    amount: amountSelected,
                },
            }).then(function (data){
                $('#product_line_name').html(data.product_name);
                $('#product_line_categ_name').html(data.product_categ_name);
                $('#product_line_price').html(data.unit_price);
                $('#product_line_product_qty').html(data.qty);
                $('#product_line_price_subtotal').html(data.net_price);
                $('#product_net_price').html(data.net_price);
                $('#product_taxes').html(data.product_tax);
                $('#gross_price').html(data.gross_price);
            });
        },
    })
})