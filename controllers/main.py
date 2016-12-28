# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from openerp import SUPERUSER_ID
from openerp import http
from openerp.http import request
import werkzeug
import datetime
import time

from openerp.tools.translate import _

class product_product(http.Controller):
        @http.route("/product/<int:product_id>", type='http', auth="user", website=True)
        def view_product(self, *args, **kwargs):
                #return self.view(*args, **kwargs)
                product_id = kwargs.get('product_id',None)
                if product_id:
                        return self.view(product_id)




        @http.route("/product/<int:product_id>/<token>", type='http', auth="public", website=True)
        def view(self, product_id, pdf=None, token=None, message=False, **post):
                # use SUPERUSER_ID allow to access/view order for public user
                # only if he knows the private token
                classification = request.registry['product.classification'].browse(request.cr, SUPERUSER_ID, 1)
                values = {
                        'classification': classification
                }
                return request.website.render('product_stats_v2.product_stats', values)

