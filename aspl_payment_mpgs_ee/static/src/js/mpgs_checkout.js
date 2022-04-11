odoo.define('aspl_payment_mpgs_ee.mpgs_checkout', function(require) {
	'use strict';
	$(document).ready(function(e) {
		var new_data = null
		var ajax = require('web.ajax');
		ajax.jsonRpc("/get_mpgs_data", 'call', {}, {
			'async' : false
		}).then(function(data) {
			new_data = data
			Checkout.configure({
                merchant: new_data.merchant_id,
                order: {
                    amount: new_data.amount,
                    currency: new_data.currency,
                    description: new_data.order_name,
                    id: new_data.order_id
                },
                session: {
                    id : new_data.session_id
                    },
                interaction: {
                    operation: new_data.operation,
                    merchant: {
                        name: new_data.merchant_name,
                    },
                    displayControl: {
                        billingAddress : "HIDE"
                    },
                }
            });

//			Checkout.configure({
//                merchant : new_data.merchant_id,
//                order : {
//                    amount : new_data.amount,
//                    currency : new_data.currency,
//                    description : new_data.order_name,
//                    id: new_data.order_id,
//                },
//                billing : {
//                    address : {
//                        street : new_data.cust_street,
//                        city : new_data.cust_city,
//                        postcodeZip : new_data.cust_zip,
//                        stateProvince : new_data.cust_state_code,
//                        country : new_data.cust_country,
//                    }
//                },
//                customer : {
//                    email :new_data.cust_email,
//                    phone : new_data.cust_phone
//                },
//                interaction : {
//                    merchant : {
//                        name : new_data.merchant_name,
//                        address : {
//                            line1 : new_data.address1,
//                            line2 : new_data.address2
//                        }
//                    },
//                    operation : 'AUTHORIZE',
//                },
//                 session:
//                    {
//                     id: new_data.session_id,
//                     version: new_data.session_version
//                    },
//            });

            setTimeout(function(){
                    Checkout.showPaymentPage();
            }, 4000)
			
		});
	});
});
