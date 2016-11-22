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
			for active_id in context['active_ids']:
				product = self.env['product.product'].browse(active_id)
				#lot_stock_id
				#import pdb;pdb.set_trace()
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
		return None		

