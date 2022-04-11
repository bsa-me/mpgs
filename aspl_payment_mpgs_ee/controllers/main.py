# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
import pycountry
import requests
from datetime import  datetime
import werkzeug
from requests.auth import HTTPBasicAuth


class WebsiteSale(WebsiteSale):
    
    @http.route(['/get_mpgs_data'], type='json', auth="public", website=True)
    def get_mpgs_data(self, **kw):
        res = {}
        mpgs_id = request.env['payment.acquirer'].sudo().search([('provider', '=', 'mpgs')], limit=1)
        # payment_transaction = request.env['payment.transaction'].sudo().search([], limit=1)
        base_url = request.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        order = request.website.sale_get_order()
        if order:
            res['cust_email'] = order.partner_id.email
            res['cust_phone'] = order.partner_id.phone 
            res['cust_street'] = order.partner_id.street
            res['cust_city'] = order.partner_id.city
            res['cust_zip'] = order.partner_id.zip
            res['cust_state_code'] = order.partner_id.state_id.name
            if len(order.partner_id.country_id.code) == 2:
                try:
                    country = pycountry.countries.get(alpha_2=(order.partner_id.country_id.code).upper())
                    res['cust_country'] = country.alpha_3
                except Exception as e:
                    raise ValueError("Exception-", e)
            else:
                res['cust_country'] = (order.partner_id.country_id.code).upper()
            
            res['amount'] = order.amount_total
            res['currency'] = 'USD'
        
        for line in order.order_line:
            res['product_name'] = line.product_id.name
            res['order_name'] = order.name
            res['order_id'] = str(order.name) + '-' + str(order.id)
            res['order_ref'] = order.name

        if mpgs_id:
            res['merchant_id'] = mpgs_id.merchant_id
            res['merchant_name'] = mpgs_id.merchant_name
            res['address1'] = mpgs_id.address1
            res['address2'] = mpgs_id.address2
            res['operation'] = mpgs_id.operation

        ### referance code as per old API
        # data = [('apiOperation', 'CREATE_CHECKOUT_SESSION'),
        #           ('apiPassword', mpgs_id.mpgs_secret_key),
        #           ('apiUsername', 'merchant.'+mpgs_id.merchant_id),
        #           ('merchant', mpgs_id.merchant_id),
        #           ('order.id', str(order.id)+''+order.name),
        #           ('order.amount', res['amount']),
        #           ('order.currency', res['currency']),
        #           ('interaction.operation','AUTHORIZE')]
        # url = "https://credimax.gateway.mastercard.com/api/rest/version/52/merchant/%s/session"%(mpgs_id.merchant_id)
        # f = requests.post(url, data=data)
        # https: // credimax.gateway.mastercard.com / api / nvp / version / 52

        # New API

        # url = "https://credimax.gateway.mastercard.com/api/rest/version/57/merchant/%s/session"%(mpgs_id.merchant_id)
        url = "https://ap-gateway.mastercard.com/api/rest/version/58/merchant/%s/session"%(mpgs_id.merchant_id)
        cancel_url = base_url + '/shop/payment'
        return_url = base_url + '/shop/completeCallback'
        currency = res['currency']
        # currency = 'USD'
        payload = "{\n      \"apiOperation\" : \"%s\",\n    \"order\": {\n            \"amount\" : \"%s\",\n            \"currency\" : \"%s\",\n            \"id\" : \"%s\"\n        },\n        \"interaction\":{\n        \"operation\":\"%s\",\n        \"returnUrl\":\"%s\",\n        \"cancelUrl\":\"%s\",\n        \"merchant\": {\n        \"name\": \"%s\" },\n        }\n}"%('CREATE_CHECKOUT_SESSION', res['amount'], currency, str(order.id)+''+order.name, res['operation'], return_url, cancel_url, res['merchant_name'])
        user_name = 'merchant.' + mpgs_id.merchant_id
        r = requests.request(
            "POST", url, auth=HTTPBasicAuth(str(user_name), mpgs_id.mpgs_secret_key), data=payload)

        response = eval(r.text)
        if response.get('result') == 'SUCCESS' and 'session' in response:
            res['session_id'] = response['session'].get('id', '')
            res['session_version'] = response['session'].get('version', '')
        return res

    @http.route(['/shop/completeCallback'], type='http', auth="public", website=True)
    def confirm_order_new(self, **post):
        """update success payment"""
        payment_transaction = request.env['payment.transaction'].sudo().search([], limit=1)
        payment_transaction.update({
            'state': 'done',
            'date': datetime.now(),
        })
        return werkzeug.utils.redirect("/payment/process")