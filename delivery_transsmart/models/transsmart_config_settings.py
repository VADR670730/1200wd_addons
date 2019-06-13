# -*- coding: utf-8 -*-
# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from transsmart.connection import Connection
from requests import HTTPError
import json


class TranssmartConfigSettings(models.TransientModel):
    _name = 'transsmart.config.settings'
    _inherit = 'res.config.settings'

    demo = fields.Boolean(default=True)
    username = fields.Char()
    password = fields.Char()
    account_code = fields.Char()

    @api.multi
    def get_default_transsmart(self):
        ir_config_parameter = self.env['ir.config_parameter']
        demo = ir_config_parameter.get_param('transsmart_demo')
        username = ir_config_parameter.get_param('transsmart_username')
        password = ir_config_parameter.get_param('transsmart_password')
        account_code = ir_config_parameter.get_param('transsmart_account_code')
        return {
            'demo': demo,
            'username': username,
            'password': password,
            'account_code': account_code,
        }

    @api.multi
    def set_transsmart_defaults(self):
        """
        Save the settings *and* synchronize the tables.
        """
        self.ensure_one()
        ir_config_parameter = self.env['ir.config_parameter']
        ir_config_parameter.set_param('transsmart_demo', self.demo)
        ir_config_parameter.set_param('transsmart_username', self.username)
        ir_config_parameter.set_param('transsmart_password', self.password)
        ir_config_parameter.set_param(
            'transsmart_account_code',
            self.account_code,
        )
        try:
            self._synchronize_models()
        except HTTPError as e:
            raise ValidationError(
                _("Error: %s" % (e.response.json()['message'])))

    @api.multi
    def _synchronize_models(self):
        """
        This will be invoked when the user saves the settings and by the cron
        job.
        """
        cost_center = self.env['cost.center']
        service_level_other = self.env['service.level.other']
        service_level_time = self.env['service.level.time']
        product_template = self.env['product.template']
        res_partner = self.env['res.partner']
        booking_profile = self.env['booking.profile']
        connection = Connection().connect(
            self.username,
            self.password,
            self.demo,
        )
        response = connection.Account.retrieve_costcenter(self.account_code)

        def _assemble_common_values(value):
            return {
                'nr': value['nr'],
                'code': value['code'],
                'description': value['description'],
                'is_default': value['isDefault'],
                }

        for center in response.json():
            value = json.loads(center['value'])
            value.update({'nr': center['nr']})
            value = _assemble_common_values(value)
            cost_center = cost_center.search([('nr', '=', value['nr'])])
            if not cost_center:
                cost_center.create(value)
            else:
                cost_center.write(value)
        response = connection.Account.retrieve_servicelevel_others(
            self.account_code)
        for service_other in response.json():
            value = json.loads(service_other['value'])
            value.update({'nr': service_other['nr']})
            value = _assemble_common_values(value)
            service_level_other = service_level_other.search([
                ('nr', '=', value['nr'])])
            if not service_level_other:
                service_level_other.create(value)
            else:
                service_level_other.write(value)
        response = connection.Account.retrieve_servicelevel_time(
            self.account_code)
        for service_time in response.json():
            value = json.loads(service_time['value'])
            value.update({'nr': service_time['nr']})
            value = _assemble_common_values(value)
            service_level_time = service_level_time.search([
                ('nr', '=', value['nr'])])
            if not service_level_time:
                service_level_time.create(value)
            else:
                service_level_time.write(value)
        response = connection.Account.retrieve_packages(self.account_code)
        for package in response.json():
            value = json.loads(package['value'])
            value.update({'nr': package['nr']})
            _type = value['type']
            values = _assemble_common_values(value)
            values.update({
                'name': value['description'],
                'type': 'service',
                'package': True,
                '_type': _type,
                'sale_ok': False,
                'purchase_ok': False,
                'package': True,
                'length': value['length'],
                'width': value['width'],
                'height': value['height'],
                'weight': value['weight'],
                })
            product_template = product_template.search([
                ('nr', '=', values['nr'])])
            if not product_template:
                product_template.create(values)
            else:
                product_template.write(values)
        response = connection.Account.retrieve_carrier(self.account_code)
        for carrier in response.json():
            value = json.loads(carrier['value'])
            value = {
                'nr': carrier['nr'],
                'code': value['code'],
                'name': value['name'],
                'carrier': True,
                'customer': False,
                }
            res_partner_carrier = res_partner.search([
                ('nr', '=', carrier['nr'])])
            if not res_partner_carrier:
                res_partner_carrier.create(value)
            else:
                res_partner_carrier.write(value)
        response = connection.Account.retrieve_bookingprofiles(
            self.account_code)
        for profile in response.json():
            value = json.loads(profile['value'])
            value = {
                'nr': profile['nr'],
                'code': value['code'],
                'name': value['description'],
                'carrier_id': value['carrier'],
                'service_level_time_id': value['serviceLevelTime'],
                'service_level_other_id': value['serviceLevelOther'],
                'incoterms_id': value['incoterms'],
                'costcenter_id': value['costCenter'],
                'mailtype': value['mailType'],
                }
            booking_profile = booking_profile.search([
                ('nr', '=', carrier['nr'])])
            if not booking_profile:
                booking_profile.create(value)
            else:
                booking_profile.write(value)
