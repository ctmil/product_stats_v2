# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from lxml import etree
import time
from datetime import datetime, date

from openerp.tools.translate import _
from openerp.osv import fields, osv
from openerp.addons.base_status.base_stage import base_stage

class product_product(osv.osv):
	_inherit = "project.project"

	def show_treemap(self, cr, uid, product_id, context=None):
	        product = self.browse(cr, uid, product_id[0], context=context)
        	return {
	            'type': 'ir.actions.act_url',
        	    # 'target': 'self',
	            'target': '_blank',
        	    'url': '/product/%s' % (product.id)
	        }

