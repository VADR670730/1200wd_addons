# -*- coding: utf-8 -*-
# Copyright 2018 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class StockPickingWave(models.Model):
    _inherit = "stock.picking.wave"

    transsmart_confirmed = fields.Boolean(
        "Transsmart Confirmed",
        compute="_compute_transsmart_confirmed",
        store=False,
    )

    @api.depends('picking_ids')
    def _compute_transsmart_confirmed(self):
        for rec in self:
            if rec.picking_ids:
                rec.transsmart_confirmed = all(
                    rec.picking_ids.mapped('carrier_tracking_ref'))
            else:
                rec.transsmart_confirmed = False

    @api.multi
    def action_create_transsmart_document(self):
        for rec in self:
            rec.picking_ids.action_create_transsmart_document()