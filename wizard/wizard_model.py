# -*- coding: utf-8 -*-
from datetime import datetime
import logging
from openerp.exceptions import Warning
from openerp import SUPERUSER_ID
import openerp.addons.decimal_precision as dp
_logger = logging.getLogger(__name__)
from openerp import models, fields, api


class product_generate_abastecimiento_v2(models.TransientModel):
	_name= 'product.generate.abastecimiento.v2'

	warehouse_id = fields.Many2one('stock.warehouse',string='Almacen',required=True)
	#location_id = fields.Many2one('stock.location',string='Ubicacion',required=True,domain=[('usage','=','internal')])

	@api.multi
	def generate_abastecimiento_v2(self):
		context = self.env.context
		if context['active_model'] == 'product.product':
			suppliers = []
			for active_id in context['active_ids']:
				product = self.env['product.product'].browse(active_id)
				if product.punto_pedido_v2:
					vals = {
						'warehouse_id': self.warehouse_id.id,
						'location_id': self.warehouse_id.lot_stock_id.id,
						'product_id': active_id,
						'active': True,
						'product_min_qty': product.punto_pedido_v2,
						'qty_multiple': 1,
						'product_max_qty': product.punto_pedido_v2 + product.order_size_v2,
						}
					orderpoint_id = self.env['stock.warehouse.orderpoint'].search([('product_id','=',active_id),\
									('warehouse_id','=',self.warehouse_id.id),\
									('location_id','=',self.warehouse_id.lot_stock_id.id)])
					if not orderpoint_id:
						return_id = self.env['stock.warehouse.orderpoint'].create(vals)
					else:
						return_id = self.env['stock.warehouse.orderpoint'].write(vals)
				product = self.env['product.product'].browse(active_id)
				if product.internal_supplier_v2.id not in suppliers:
					suppliers.append(product.internal_supplier_v2.id)
			if len(suppliers) > 1:
				raise Warning('Se seleccionaron productos para mas de un proveedor')
			if not suppliers:
				raise Warning('Los productos no tienen proveedor asignado')
			supplier = self.env['res.partner'].browse(suppliers[0])
			vals_po = {
				'partner_id': suppliers[0],
				'location_id': self.warehouse_id.lot_stock_id.id,	
				'pricelist_id': supplier.property_product_pricelist_purchase.id,
				}	
			po = self.env['purchase.order'].create(vals_po)
			for active_id in context['active_ids']:
				product = self.env['product.product'].browse(active_id)
				# si hay menos que el pto de pedido...
				if product.punto_pedido_v2 > product.qty_available:
					if product.order_size_v2 > product.qty_available:
						product_qty = product.order_size_v2
					if product.stock_seguridad_v2 > product.qty_available:
						product_qty = product.stock_seguridad_v2 + product.order_size_v2
					vals_line = {
						'product_id': active_id,
						'order_id': po.id,
						'product_qty': product_qty,
						'price_unit': product.standard_price,
						}
					line_id = self.env['purchase.order.line'].create(vals_line)
	
		return None		

