{
    'name': 'Informacion estadistica de productos v2.0',
    'category': 'Sale',
    'version': '0.1',
    #'depends': ['base','product','account','ba_sales'],
    'depends': ['base','product','account'],
    'data': [
	'product_view.xml',
	'website_product.xml',
	'wizard/wizard_view.xml'
    ],
    'demo': [
    ],
    'qweb': [],
    'installable': True,
}
