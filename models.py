from openerp import models, fields, api, _
from openerp.osv import osv
from openerp.exceptions import except_orm, ValidationError
from StringIO import StringIO
import urllib2, httplib, urlparse, gzip, requests, json
import openerp.addons.decimal_precision as dp
import logging
import datetime
from openerp.fields import Date as newdate
from datetime import datetime, timedelta, date
from dateutil import relativedelta
#Get the logger
_logger = logging.getLogger(__name__)

class product_history(models.Model):
	_name = 'product.history'
	_description = 'Historial de ventas del producto'

	@api.multi
	def _update_product_history(self):
		history_ids = self.search([])
		for record in history_ids:
			record.unlink()
		period_ids = self.env['account.period'].search([])
		for period_id in period_ids:
			_logger.debug('Logging period %s '%(period_id.name))
			dict_data = {}
			invoices = self.env['account.invoice'].search([('state','in',['open','paid']),('period_id','=',period_id.id),\
						('type','=','out_invoice')])
			for invoice in invoices:
				_logger.debug('Processing invoice %s '%(invoice.internal_number))
				for invoice_line in invoice.invoice_line:
					if invoice_line.product_id.id not in dict_data.keys():
						dict_data[invoice_line.product_id.id] = [invoice_line.quantity,invoice_line.price_subtotal]
					else:
						dict_data[invoice_line.product_id.id][0] = dict_data[invoice_line.product_id.id][0] + \
							invoice_line.quantity
						dict_data[invoice_line.product_id.id][1] = dict_data[invoice_line.product_id.id][1] + \
							invoice_line.price_subtotal
			for key in dict_data.keys():
				product = self.env['product.product'].browse(key)
				vals = {
					'period_id': period_id.id,
					'product_id': key,
					'categ_id': product.categ_id.id,
					'cantidad': dict_data[key][0],
					'monto_vendido': dict_data[key][1],
					}	
				return_id = self.create(vals)

	product_id = fields.Many2one('product.product',string='Producto')
	categ_id = fields.Many2one('product.category',string='Categoria')
	period_id = fields.Many2one('account.period',string='Periodo')
	cantidad = fields.Integer('Cantidad vendida')
	monto_vendido = fields.Float('Monto vendido')

class product_product(models.Model):
	_inherit = 'product.product'

	@api.multi
	def _update_product_rank(self):
		previous_date = date.today() - timedelta(days=365)
		invoices = self.env['account.invoice'].search([('date_invoice','>=',previous_date),
			('state','in',['open','paid'])])
		product_amount = {}
		for invoice in invoices:
			for invoice_line in invoice.invoice_line:
				if invoice_line.product_id:
					if invoice_line.product_id.id not in product_amount.keys():
						product_amount[invoice_line.product_id.id] = invoice_line.price_subtotal
					else:
						product_amount[invoice_line.product_id.id] += invoice_line.price_subtotal
		list_products = sorted(product_amount, key=product_amount.__getitem__, reverse=True)
		index = 0
		for product_id in list_products:
			index += 1
			vals = {
				'product_rank': index
				}
			product = self.env['product.product'].browse(product_id)
			product.write(vals)


	@api.multi
	def _update_product_abc(self):
		products = self.env['product.product'].search([('porcentaje_del_total','>',0)],order='porcentaje_del_total desc')
		running_total = 0
		for product in products:
			running_total += product.porcentaje_del_total
			if running_total <= 70:
				classification_value = 'A'
			else:
				if running_total <= 90:
					classification_value = 'B'
				else:
					classification_value = 'C'
			product.write({'product_abc': classification_value})

	@api.multi
	def _update_porcentaje_total_ventas(self):
		previous_date = date.today() - timedelta(days=365)
		invoices = self.env['account.invoice'].search([('date_invoice','>=',previous_date),
			('state','in',['open','paid'])])
		product_amount = {}
		for invoice in invoices:
			for invoice_line in invoice.invoice_line:
				if invoice_line.product_id:
					if invoice_line.product_id.id not in product_amount.keys():
						product_amount[invoice_line.product_id.id] = invoice_line.price_subtotal
					else:
						product_amount[invoice_line.product_id.id] += invoice_line.price_subtotal
		total_amount = 0
		for amount in product_amount.values():
			total_amount = total_amount + amount
		if total_amount > 0:
			for product in product_amount.keys():
				amount = product_amount[product]
				percentaje = (amount / total_amount) * 100
				vals = {
					'porcentaje_del_total': percentaje,
					}
				product = self.env['product.product'].browse(product)
				product.write(vals)
				

	@api.model
	def _compute_sobrantes_faltantes(self):
		products = self.env['product.product'].search([('product_rank','>',0)])
		for product in products:
			faltante = 0
			faltante_valorizado = 0
			sobrante = 0
			sobrante_valorizado = 0
			if product.qty_available > product.punto_pedido:
				sobrante = product.qty_available - product.punto_pedido
				sobrante_valorizado = sobrante * product.standard_price
			if product.punto_pedido > product.qty_available:
				faltante = product.punto_pedido - product.qty_available
				faltante_valorizado = faltante * product.standard_price
			vals = {
				'faltante': faltante,
				'faltante_valorizado': faltante_valorizado,
				'sobrante': sobrante,
				'sobrante_valorizado': sobrante_valorizado,
				}
			try:
				product.write(vals)
			except:
				pass

	@api.model
	def _compute_puntos_pedidos(self):
		# products = self.env['product.product'].search([('type','=','product'),('product_rank','>',0)])
		products = self.env['product.product'].search([('product_rank','>',0)])
		for product in products:
			history_ids = self.env['product.history'].search([('product_id','=',product.id)])
			if history_ids:
				product.update_punto_pedido()

	@api.one
	def update_punto_pedido(self):
		fecha_anterior = str(date.today() - timedelta(days=365))
		period_ids = self.env['account.period'].search([('date_start','>=',fecha_anterior)],limit=12)
		periods = str([x.id for x in period_ids])
		periods = periods.replace('[','(')
		periods = periods.replace(']',')')
		if self.product_abc == 'A':
			servicio = '0.8'
		else:
			if self.product_abc == 'B':
				servicio = '0.6'
			else:
				servicio = '0.5'
		norminv_str = ',norminv('+servicio
		sql = "select avg(cantidad) as promedio,stddev(cantidad) as desvio " + \
			"from product_history where product_id = "+str(self.id) + \
			" and period_id in " + str(periods)
		self.env.cr.execute(sql)
		for promedio,desvio in self.env.cr.fetchall():
			pass
		if desvio:
			sql_norminv = "select pgnumerics.norminv(" + servicio + ","+str(promedio)+","+str(desvio)+")"
			self.env.cr.execute(sql_norminv)
			for pto_pedido in self.env.cr.fetchall():
				pass
		else:
			pto_pedido = promedio
		if pto_pedido:
			if type(pto_pedido) == float:
				pto_pedido = pto_pedido
			else:
				pto_pedido = pto_pedido[0]
			vals = {
				'punto_pedido': pto_pedido,
				'promedio': promedio,
				'desvio': desvio or 0,
				}
			#try:
			self.write(vals)
			#except:
			#	pass	

	@api.one
	def _compute_stock_seguridad(self):
		if self.punto_pedido:
			if (self.punto_pedido - self.promedio) > 0:
				self.stock_seguridad = self.punto_pedido - self.promedio

	@api.one
	def _compute_pedido(self):
		if self.promedio:
			self.order_size = self.promedio

	"""
	@api.one
	def _compute_sobrante(self):
		if self.punto_pedido < self.qty_available:
			self.sobrante = self.qty_available - self.punto_pedido

	@api.one
	def _compute_faltante(self):
		if self.punto_pedido > self.qty_available:
			self.faltante = self.punto_pedido - self.qty_available

	@api.one
	def _compute_sobrante_valorizado(self):
		self.sobrante_valorizado = self.sobrante * self.standard_price

	@api.one
	def _compute_faltante_valorizado(self):
		self.faltante_valorizado = self.faltante * self.standard_price
	"""

	@api.one
	def _compute_internal_category(self):
		if self.product_tmpl_id.categ_id:
			self.internal_category = self.product_templ_id.categ_id.id

	@api.one
	def _compute_internal_supplier(self):
		if self.product_tmpl_id.supplier_id:
			self.internal_supplier = self.product_tmpl_id.supplier_id.id

	internal_supplier = fields.Many2one('res.partner',compute=_compute_internal_supplier,store=True)
	internal_category = fields.Many2one('product.category',compute=_compute_internal_category,store=True)
	product_rank = fields.Integer('Ranking')
	porcentaje_del_total = fields.Float('Porcentaje del Total de Ventas')
	product_abc = fields.Selection(selection=[('A','A'),('B','B'),('C','C')],string='Clasificacion ABC')
	product_history = fields.Many2one(comodel_name='product.history',inverse_name='product_id')
	punto_pedido = fields.Integer(string='Punto de pedido')
	stock_seguridad = fields.Integer(string='Stock Seguridad',compute=_compute_stock_seguridad)
	order_size = fields.Integer(string='Pedido',compute=_compute_pedido)
	promedio = fields.Integer(string='Promedio')
	desvio = fields.Integer(string='Desvio')
	#sobrante = fields.Integer(string='Sobrante',compute=_compute_sobrante)
	#faltante = fields.Integer(string='Faltante',compute=_compute_faltante)
	#sobrante_valorizado = fields.Integer(string='Sobrante Valorizado',compute=_compute_sobrante_valorizado)
	#faltante_valorizado = fields.Integer(string='Faltante Valorizado',compute=_compute_faltante_valorizado)
	sobrante = fields.Integer(string='Sobrante')
	faltante = fields.Integer(string='Faltante')
	sobrante_valorizado = fields.Integer(string='Sobrante Valorizado')
	faltante_valorizado = fields.Integer(string='Faltante Valorizado')
