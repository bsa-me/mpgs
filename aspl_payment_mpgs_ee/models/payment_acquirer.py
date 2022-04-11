# -*- coding: utf-8 -*-
import hashlib
import logging
from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare
from odoo.http import request

_logger = logging.getLogger(__name__)


class AcquirerMasterCard(models.Model):
    _inherit = 'payment.acquirer'
    
    provider = fields.Selection(selection_add=[('mpgs', 'MPGS')], ondelete={'mpgs': 'set default'})
    merchant_id = fields.Char(string = 'Merchant Id',required_if_provider='mpgs', groups='base.group_user')
    merchant_name = fields.Char(string = 'Merchant Name',required_if_provider='mpgs', groups='base.group_user')
    operation = fields.Selection([('AUTHORIZE', 'AUTHORIZE'), ('PURCHASE', 'PURCHASE')], default='AUTHORIZE', string='Operation')
    mpgs_secret_key = fields.Char(string = 'MPGS Secret Key', required_if_provider='mpgs', groups='base.group_user')
    address1 = fields.Char(string = "Address1",required_if_provider='mpgs', groups='base.group_user')
    address2 = fields.Char(string = "Address2",required_if_provider='mpgs', groups='base.group_user')

    
    def _get_mpgs_urls(self): #environment
        """ mpgs URLs"""
        return {'mpgs_form_url': 'https://ap-gateway.mastercard.com/api/nvp/version/58'}
        
    
    def _mpgs_generate_sign(self, inout, values):
        """ Generate the shasign for incoming or outgoing communications.
        :param self: the self browse record. It should have a shakey in shakey out
        :param string inout: 'in' (odoo contacting MPGS) or 'out' (MPGS
                             contacting odoo).
        :param dict values: transaction values

        :return string: shasign
        """
        
        if inout not in ('in', 'out'):
            raise Exception("Type must be 'in' or 'out'")

        if inout == 'in':
            keys = "key|txnid|amount|productinfo|firstname|email|udf1|||||||||".split('|')
            sign = ''.join('%s|' % (values.get(k) or '') for k in keys)
            sign += self.mpgs_secret_key or ''
        else:
            keys = "|status||||||||||udf1|email|firstname|productinfo|amount|txnid".split('|')
            sign = ''.join('%s|' % (values.get(k) or '') for k in keys)
            sign = self.mpgs_secret_key + sign + self.merchant_id
        shasign = hashlib.sha512(sign.encode('utf-8')).hexdigest()
        return shasign
    
    def mpgs_form_generate_values(self, values):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        
        mpgs_values = dict(values,
                                key=self.mpgs_secret_key,
                                txnid=values['reference'],
                                reference = values['reference'],
                                amount=values['amount'],
                                productinfo=values['reference'],
                                firstname=values.get('partner_name'),
                                email=values.get('partner_email'),
                                phone=values.get('partner_phone'),
                                service_provider='mpgs',
                                )
        mpgs_values['udf1'] = mpgs_values.pop('return_url', '/')
        mpgs_values['hash'] = self._mpgs_generate_sign('in', mpgs_values)
        return mpgs_values
        
        
    def mpgs_get_form_action_url(self):
        self.ensure_one()
        return self._get_mpgs_urls()['mpgs_form_url'] #self.environment
    

class PaymentTxmpgs(models.Model):
    _inherit = 'payment.transaction'
    
    @api.model
    def _mpgs_form_get_tx_from_data(self, data):
        """ Given a data dict coming from mpgs, verify it and find the related
        transaction record. """
        reference = request.website.sale_get_order().name
        pay_id = data.get('mihpayid')
        shasign = data.get('hash')
        transaction = self.sudo().search([('reference', '=', reference)])
        if not transaction:
            error_msg = (_('MPGS: received data for reference %s; no order found') % (reference))
            raise ValidationError(error_msg)
        elif len(transaction) > 1:
            error_msg = (_('MPGS: received data for reference %s; multiple orders found') % (reference))
            raise ValidationError(error_msg)
        return transaction

    def _mpgs_form_get_invalid_parameters(self, data):
        invalid_parameters = []

        if self.acquirer_reference and data.get('mihpayid') != self.acquirer_reference:
            invalid_parameters.append(
                ('Transaction Id', data.get('mihpayid'), self.acquirer_reference))
        #check what is buyed
        if float_compare(float(data.get('amount', '0.0')), self.amount, 2) != 0:
            invalid_parameters.append(
                ('Amount', data.get('amount'), '%.2f' % self.amount))
        return invalid_parameters
    
#     
    def _mpgs_form_validate(self, data):
        status = data.get('status')
        transaction_status = {
            'success': {
                'state': 'done',
                'acquirer_reference': data.get('acquirer_id'),
                'date_validate': fields.Datetime.now(),
            },
            'pending': {
                'state': 'pending',
                'acquirer_reference': data.get('acquirer_id'),
                'date_validate': fields.Datetime.now(),
            },
            'failure': {
                'state': 'cancel',
                'acquirer_reference': data.get('acquirer_id'),
                'date_validate': fields.Datetime.now(),
            },
            'error': {
                'state': 'error',
                'state_message': data.get('error_Message') or _('acquirer_id: feedback error'),
                'acquirer_reference': data.get('acquirer_id'),
                'date_validate': fields.Datetime.now(),
            }
        }
        vals = transaction_status.get(status, False)
        if not vals:
            vals = transaction_status['error']
            _logger.info(vals['state_message'])
        return self.write(vals)
