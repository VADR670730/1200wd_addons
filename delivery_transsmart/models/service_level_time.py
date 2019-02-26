# -*- coding: utf-8 -*-
# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class ServiceLevelTime(models.Model):
    """
    Used for keeping the Service Level Time records.
    https://devdocs.transsmart.com/#_service_level_time_retrieval
    """
    _name = 'service.level.time'

    name = fields.Char(related='code')
    nr = fields.Integer('Identifier')
    code = fields.Char()
    description = fields.Char()
    is_default = fields.Boolean()
    carrier_id = fields.Many2one('delivery.carrier', string='Carrier')

    _sql_constraints = [
        ('nr_unique', 'unique(nr)', 'Identifier field should be unique.')]
