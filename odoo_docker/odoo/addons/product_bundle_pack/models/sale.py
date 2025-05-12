# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
##############################################################################

from odoo import api, models, _
from datetime import timedelta
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID
from collections import defaultdict
from odoo.addons.stock.models.stock_rule import ProcurementException


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('move_ids.state', 'move_ids.scrapped', 'move_ids.product_uom_qty', 'move_ids.product_uom')
    def _compute_qty_delivered(self):
        super(SaleOrderLine, self)._compute_qty_delivered()
        for line in self:  # TODO: maybe one day, this should be done in SQL for performance sake
            def check_product(x):
                for rec in line.product_id.pack_ids:
                    if x == rec.product_id:
                        return x

            if line.product_id.is_pack:
                if line.qty_delivered_method == 'stock_move':
                    qty = 0.0
                    flag = False
                    count = 0
                    done_list = []
                    deliver_list = []
                    move_list = []
                    products = []
                    filtered = []
                    picking_ids = self.env['stock.picking'].search([('origin', '=', line.order_id.name)])
                    for pick in picking_ids:
                        for move_is in pick.move_ids_without_package:
                            if move_is.product_id not in products:
                                products.append(move_is.product_id)
                    pro = filter(check_product, products)
                    for product in pro:
                        filtered.append(product)
                    for pick in picking_ids:
                        for move_is in pick.move_ids_without_package:
                            if move_is.product_id in filtered:
                                if move_is.pack_id in line.product_id.pack_ids:
                                    move_list.append(move_is.product_uom_qty)
                                    done_list.append(move_is.quantity)

                    stock_move = self.env['stock.move'].search([('origin', '=', line.order_id.name)])
                    list_of_sub_product = []
                    for product_item in line.product_id.pack_ids:
                        list_of_sub_product.append(product_item.product_id)
                    for move in stock_move:
                        if count == 0:
                            if move.state == 'done' and move.product_uom_qty == move.quantity:
                                flag = True
                                for picking in picking_ids:
                                    for move_is in picking.move_ids_without_package:
                                        if sum(move_list) == 0:
                                            pass
                                        else:
                                            deliver_qty = (line.product_uom_qty * sum(done_list)) / sum(move_list)
                                            line.qty_delivered = int(deliver_qty)
                                            deliver_list.append(line.qty_delivered)
                            elif move.state == 'confirmed':
                                flag = 'confirmed'
                                count = count + 1
                                if move.quantity:
                                    done_list.append(move.quantity)
                                for picking in picking_ids:
                                    for move_is in picking.move_ids_without_package:
                                        if sum(move_list) == 0:
                                            pass
                                        else:
                                            deliver_qty = (line.product_uom_qty * sum(done_list)) / sum(move_list)
                                            line.qty_delivered = int(deliver_qty)
                                            deliver_list.append(line.qty_delivered)
                else:
                    if line.qty_delivered_method == 'stock_move':
                        qty = 0.0
                        outgoing_moves, incoming_moves = line._get_outgoing_incoming_moves()
                        for move in outgoing_moves:
                            if move.state != 'done':
                                continue
                            qty += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom,
                                                                      rounding_method='HALF-UP')
                        for move in incoming_moves:
                            if move.state != 'done':
                                continue
                            qty -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom,
                                                                      rounding_method='HALF-UP')
                        line.qty_delivered = qty

    @api.onchange('product_id', 'product_uom_qty')
    def _compute_qty_to_deliver(self):
        res = super(SaleOrderLine, self)._compute_qty_to_deliver()
        for i in self:
            if i.product_id.is_pack:
                if i.product_id.type == 'product':
                    warning_mess = {}
                    for pack_product in i.product_id.pack_ids:
                        qty = i.product_uom_qty
                        if qty * pack_product.qty_uom > pack_product.product_id.virtual_available:
                            warning_mess = {
                                'title': _('Not enough inventory!'),
                                'message': (
                                        'You plan to sell %s but you only have %s %s available, and the total quantity to sell is %s !' % (
                                    qty, pack_product.product_id.virtual_available, pack_product.product_id.name,
                                    qty * pack_product.qty_uom))
                            }
                            return {'warning': warning_mess}
            else:
                return res

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
        Launch procurement group run method with required/custom fields genrated by a
        sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
        depending on the sale order line product rule.
        """
        if self._context.get("skip_procurement"):
            return True

        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        procurements = []
        errors = []
        for line in self:
            line = line.with_company(line.company_id)
            if line.state != 'sale' or not line.product_id.type in ('consu', 'product'):
                if line.product_id.is_pack:
                    if line.product_id.type == 'service':
                        pass
                else:
                    continue
            qty = line._get_qty_procurement(previous_product_uom_qty)
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) == 0:
                continue

            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id
            else:
                if line.product_id.pack_ids:
                    values = line._prepare_procurement_values(group_id=line.order_id.procurement_group_id)
                    for pack_id, proc_data in values.items():
                        try:
                            pro_id = self.env['product.product'].browse(proc_data.get('product_id'))
                            stock_id = self.env['stock.location'].browse(proc_data.get('partner_dest_id'))
                            product_uom_obj = self.env['uom.uom'].browse(proc_data.get('product_uom'))

                            procurements.append(self.env['procurement.group'].Procurement(
                                pro_id,
                                0,
                                product_uom_obj,
                                line.order_id.partner_shipping_id.property_stock_customer,
                                proc_data.get('name'),
                                proc_data.get('origin'),
                                line.order_id.company_id,
                                proc_data
                            ))
                        except UserError as error:
                            errors.append(error.name)
                else:
                    updated_vals = {}
                    if group_id.partner_id != line.order_id.partner_shipping_id:
                        updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                    if group_id.move_type != line.order_id.picking_policy:
                        updated_vals.update({'move_type': line.order_id.picking_policy})
                    if updated_vals:
                        group_id.write(updated_vals)

            if line.product_id.pack_ids:
                values = line._prepare_procurement_values(group_id=line.order_id.procurement_group_id)
                for pack_id, proc_data in values.items():
                    try:
                        pro_id = self.env['product.product'].browse(proc_data.get('product_id'))
                        stock_id = self.env['stock.location'].browse(proc_data.get('partner_dest_id'))
                        product_uom_obj = self.env['uom.uom'].browse(proc_data.get('product_uom'))

                        procurements.append(self.env['procurement.group'].Procurement(
                            pro_id,
                            proc_data.get('product_qty'),
                            product_uom_obj,
                            line.order_id.partner_shipping_id.property_stock_customer,
                            proc_data.get('name'),
                            proc_data.get('origin'),
                            line.order_id.company_id,
                            proc_data
                        ))

                    except UserError as error:
                        errors.append(error.name)
            else:
                values = line._prepare_procurement_values(group_id=group_id)
                product_qty = line.product_uom_qty - qty
                line_uom = line.product_uom
                quant_uom = line.product_id.uom_id
                product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
                procurements.append(self.env['procurement.group'].Procurement(
                    line.product_id, product_qty, procurement_uom,
                    line.order_id.partner_shipping_id.property_stock_customer,
                    line.product_id.display_name, line.order_id.name, line.order_id.company_id, values))

        if procurements:
            procurement_group = self.env['procurement.group']
            if self.env.context.get('import_file'):
                procurement_group = procurement_group.with_context(import_file=False)
            procurement_group.run(procurements)

        module = self.env['ir.module.module'].sudo().search(
            [('state', '=', 'installed'), ('name', '=', 'procurement_jit')], limit=1)

        if module:
            orders = list(set(x.order_id for x in self))
            for order in orders:
                reassign = order.picking_ids.filtered(
                    lambda x: x.state == 'confirmed' or (x.state in ['waiting', 'assigned'] and not x.printed))
                if reassign:
                    reassign.action_assign()

        orders = self.mapped('order_id')
        for order in orders:
            pickings_to_confirm = order.picking_ids.filtered(lambda p: p.state not in ['cancel', 'done'])
            if pickings_to_confirm:
                pickings_to_confirm.action_confirm()
        return True

    def _prepare_procurement_values(self, group_id=False):
        res = super(SaleOrderLine, self)._prepare_procurement_values(group_id)

        procurement_values = {}

        date_deadline = self.order_id.commitment_date or self._expected_date()
        date_planned = date_deadline - timedelta(days=self.order_id.company_id.security_lead)

        if self.product_id.pack_ids:
            for item in self.product_id.pack_ids:
                line_route_ids = self.env['stock.location'].browse(self.route_id.id)

                procurement_values[item.id] = {
                    'name': item.product_id.name,
                    'origin': self.order_id.name,
                    'date_planned': date_planned,
                    'product_id': item.product_id.id,
                    'product_qty': item.qty_uom * abs(self.product_uom_qty),
                    'product_uom': item.uom_id and item.uom_id.id,
                    'company_id': self.order_id.company_id,
                    'group_id': group_id,
                    'sale_line_id': self.id,
                    'warehouse_id': self.order_id.warehouse_id and self.order_id.warehouse_id,
                    'location_id': self.order_id.partner_shipping_id.property_stock_customer.id,
                    'route_ids': self.route_id and line_route_ids or [],
                    'partner_dest_id': self.order_id.partner_shipping_id,
                    'partner_id': self.order_id.partner_shipping_id.id,
                    'pack_id': item.id,
                }
            return procurement_values
        else:
            res.update({
                'company_id': self.order_id.company_id,
                'group_id': group_id,
                'sale_line_id': self.id,
                'date_planned': date_planned,
                'route_ids': self.route_id,
                'warehouse_id': self.order_id.warehouse_id or False,
                'partner_dest_id': self.order_id.partner_shipping_id,
                'partner_id': self.order_id.partner_shipping_id.id,
            })
        return res


class ProcurementRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _run_pull(self, procurements):
        moves_values_by_company = defaultdict(list)
        mtso_products_by_locations = defaultdict(list)

        for procurement, rule in procurements:
            if not rule.location_src_id:
                msg = _('No source location defined on stock rule: %s!') % (rule.name,)
                raise ProcurementException([(procurement, msg)])

            if rule.procure_method == 'mts_else_mto':
                mtso_products_by_locations[rule.location_src_id].append(procurement.product_id.id)

        forecasted_qties_by_loc = {}
        for location, product_ids in mtso_products_by_locations.items():
            products = self.env['product.product'].browse(product_ids).with_context(location=location.id)
            forecasted_qties_by_loc[location] = {product.id: product.free_qty for product in products}

        procurements = sorted(procurements, key=lambda proc: float_compare(proc[0].product_qty, 0.0,
                                                                           precision_rounding=proc[
                                                                               0].product_uom.rounding) > 0)
        for procurement, rule in procurements:
            procure_method = rule.procure_method
            if rule.procure_method == 'mts_else_mto':
                qty_needed = procurement.product_uom._compute_quantity(procurement.product_qty,
                                                                       procurement.product_id.uom_id)
                if float_compare(qty_needed, 0, precision_rounding=procurement.product_id.uom_id.rounding) <= 0:
                    procure_method = 'make_to_order'
                    for move in procurement.values.get('group_id', self.env['procurement.group']).stock_move_ids:
                        if move.rule_id == rule and float_compare(move.product_uom_qty, 0,
                                                                  precision_rounding=move.product_uom.rounding) > 0:
                            procure_method = move.procure_method
                            break
                    forecasted_qties_by_loc[rule.location_src_id][procurement.product_id.id] -= qty_needed

                elif float_compare(qty_needed, forecasted_qties_by_loc[rule.location_src_id][procurement.product_id.id],
                                   precision_rounding=procurement.product_id.uom_id.rounding) > 0:
                    procure_method = 'make_to_order'
                else:
                    forecasted_qties_by_loc[rule.location_src_id][procurement.product_id.id] -= qty_needed
                    procure_method = 'make_to_stock'

            move_values = rule._get_stock_move_values(*procurement)
            if procurement[-1].get('pack_id'):
                move_values.update({'pack_id': procurement[-1].get('pack_id')})
            move_values['procure_method'] = procure_method
            moves_values_by_company[procurement.company_id.id].append(move_values)

        for company_id, moves_values in moves_values_by_company.items():
            moves = self.env['stock.move'].with_user(SUPERUSER_ID).sudo().with_company(company_id).create(moves_values)
            moves._action_confirm()
        return True

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, company_id,
                               values):
        result = super(ProcurementRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id,
                                                                     name, origin, company_id, values)

        if product_id.pack_ids:
            for item in product_id.pack_ids:
                result.update({
                    'product_id': item.product_id.id,
                    'product_uom': item.uom_id and item.uom_id.id,
                    'product_uom_qty': item.qty_uom,
                    'origin': origin,
                    'pack_id': item.id,
                })
        return result


class AccountMoveLineInherit(models.Model):
    _inherit = 'account.move.line'

    def _stock_account_get_anglo_saxon_price_unit(self):
        res = super(AccountMoveLineInherit, self)._stock_account_get_anglo_saxon_price_unit()

        if not self.product_id.is_pack:
            return res

        so_line = self.sale_line_ids and self.sale_line_ids[-1] or False
        price_unit = prc_unit = cal_prd_price = 0
        if so_line:
            qty_to_invoice = self.product_uom_id._compute_quantity(self.quantity, self.product_id.uom_id)
            qty_invoiced = sum(
                [x.product_uom_id._compute_quantity(x.quantity, x.product_id.uom_id) for x in so_line.invoice_lines if
                 x.move_id.state == 'posted'])

            for prd in self.product_id.pack_ids:
                average_price_unit = prd.product_id._compute_average_price(qty_invoiced, qty_to_invoice,
                                                                           so_line.move_ids.filtered(lambda
                                                                                                         s: s.product_id.id == prd.product_id.id))
                prc_unit += (average_price_unit * prd.qty_uom)

            if not self.product_id:
                cal_prd_price = self.price_unit
            else:
                cal_prd_price = self.product_id._stock_account_get_anglo_saxon_price_unit(uom=self.product_uom_id)

            price_unit = prc_unit or cal_prd_price
            res = self.product_id.uom_id._compute_price(price_unit, self.product_uom_id)
        return res


class InheritStockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        draft_picking = self.filtered(lambda p: p.state == 'draft')
        draft_picking.action_confirm()
        for move in draft_picking.move_ids:
            if float_is_zero(move.quantity, precision_rounding=move.product_uom.rounding) and\
               not float_is_zero(move.product_uom_qty, precision_rounding=move.product_uom.rounding):
                move.quantity = move.product_uom_qty

        # Sanity checks.
        if not self.env.context.get('skip_sanity_check', False):
            self._sanity_check()
        self.message_subscribe([self.env.user.partner_id.id])

        # Run the pre-validation wizards. Processing a pre-validation wizard should work on the
        # moves and/or the context and never call `_action_done`.
        if not self.env.context.get('button_validate_picking_ids'):
            self = self.with_context(button_validate_picking_ids=self.ids)
        if self.picking_type_id.code == "outgoing":
            find_pack_moves = self.move_ids_without_package.filtered(lambda p: p.product_id.is_pack)
            if find_pack_moves:
                for move in find_pack_moves:
                    move.sudo().update({'quantity': move.product_uom_qty})
        res = self._pre_action_done_hook()
        if res is not True:
            return res

        # Call `_action_done`.
        pickings_not_to_backorder = self.filtered(lambda p: p.picking_type_id.create_backorder == 'never')
        if self.env.context.get('picking_ids_not_to_backorder'):
            pickings_not_to_backorder |= self.browse(self.env.context['picking_ids_not_to_backorder']).filtered(
                lambda p: p.picking_type_id.create_backorder != 'always'
            )
        pickings_to_backorder = self - pickings_not_to_backorder
        pickings_not_to_backorder.with_context(cancel_backorder=True)._action_done()
        pickings_to_backorder.with_context(cancel_backorder=False)._action_done()
        final_moves = self.move_ids_without_package.filtered(lambda p: p.product_id.is_pack)
        report_actions = self._get_autoprint_report_actions()
        another_action = False
        if self.env.user.has_group('stock.group_reception_report'):
            pickings_show_report = self.filtered(lambda p: p.picking_type_id.auto_show_reception_report)
            lines = pickings_show_report.move_ids.filtered(lambda m: m.product_id.type == 'product' and m.state != 'cancel' and m.quantity and not m.move_dest_ids)
            if lines:
                # don't show reception report if all already assigned/nothing to assign
                wh_location_ids = self.env['stock.location']._search([('id', 'child_of', pickings_show_report.picking_type_id.warehouse_id.view_location_id.ids), ('usage', '!=', 'supplier')])
                if self.env['stock.move'].search([
                        ('state', 'in', ['confirmed', 'partially_available', 'waiting', 'assigned']),
                        ('product_qty', '>', 0),
                        ('location_id', 'in', wh_location_ids),
                        ('move_orig_ids', '=', False),
                        ('picking_id', 'not in', pickings_show_report.ids),
                        ('product_id', 'in', lines.product_id.ids)], limit=1):
                    action = pickings_show_report.action_view_reception_report()
                    action['context'] = {'default_picking_ids': pickings_show_report.ids}
                    if not report_actions:
                        return action
                    another_action = action
        if report_actions:
            return {
                'type': 'ir.actions.client',
                'tag': 'do_multi_print',
                'params': {
                    'reports': report_actions,
                    'anotherAction': another_action,
                }
            }
        return True
