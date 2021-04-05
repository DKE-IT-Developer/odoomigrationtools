import csv
import os
import sys
import odoorpc
import psycopg2
import requests

# set source directory of mapped object csv file
# read file of object in file format 'object.csv'
# read file csv of format no,field1,type1,relation1,field2,type2,relation2,default
# read object's field in sql table and find inherited object table's field
# read relational fields record data as set type
# insert to inherited object's table
# insert to related object's table
# insert to object's table

transport_protocol = 'https://'

host1 = sys.argv[1]
port1 = sys.argv[2]
db1 = sys.argv[3]
username1 = sys.argv[4]
password1 = sys.argv[5]

host2 = sys.argv[6]
port2 = sys.argv[7]
db2 = sys.argv[8]
username2 = sys.argv[9]
password2 = sys.argv[10]

print('Odoo Source')
odoo1 = odoorpc.ODOO(host1, port=port1)
odoo1.login(db1, username1, password1)
print('====================================================================')
print('Odoo Target')
odoo2 = odoorpc.ODOO(host2, port=port2)
odoo2.login(db2, username2, password2)
print('====================================================================')

file_consumed = []
directory = 'csv_mapped'
listdir = os.listdir(directory)

try:
	requests.get(transport_protocol+host2+':'+port2)
except:
	transport_protocol = 'http://'
	requests.get(transport_protocol+host2+':'+port2)

def send_request(values):
	response = requests.post(transport_protocol+host2+':'+port2+'/base_import/json', json=values)
	return response.text

def migrate_csv(file_name):
	if not os.path.exists(directory+'/'+file_name):
		return False
	csv_file = open(directory+'/'+file_name)
	csv_read = csv.reader(csv_file, delimiter=';')
	model_source_target = csv_read.next()
	source_model = model_source_target[1]
	target_model = model_source_target[3]
	file_consumed.append(file_name)
	csv_read.next()
	# dictionary format
	# [{field_name: values}] payload format values
	# {fields_name: {convert: False, default: False}} fields_info
	fields_convert = []
	fields_info = {}
	fields_list = []
	fields_many2one = []
	for row in csv_read:
		field1 = row[1]
		type1 = row[2]
		relation1 = row[3]
		field2 = row[4]
		type2 = row[5]
		relation2 = row[6]
		default = row[7]
		if type2 == 'one2many' or type2 == 'many2many':
			continue
		if not field1 and not field2:
			continue
		
		if default:
			if type2 == 'integer':
				default = int(default)
			elif type2 == 'float':
				default = float(default)
			elif type2 == 'boolean':
				if default.lower() == 'true':
					default = True
				elif default.lower() == 'false':
					default = False
		
		if field1:
			if type1 == type2:
				if type2 == 'many2one' and relation2+'.csv' not in file_consumed:
					# is_relation_called = 
					migrate_csv(relation2+'.csv')
				fields_info.update({field2: {'convert': False, 'default': default or None, 'type': type2}})
			else:
				fields_info.update({field2: {'convert': True, 'default': default or None, 'type': type2}})
		elif not field1 and field2:
			fields_info.update({field2: {'convert': False, 'default': default or None, 'type': type2}})

		fields_list.append(field2)
		if type2 == 'many2one' and field1:
			fields_many2one.append(field2)
	domain = []
	if 'active' in odoo1.env[source_model].fields_get():
		domain = ['|', ('active', '=', False), ('active', '=', True)]
	values = odoo1.env[source_model].search_read(domain, fields_list, order='id')
	not_existed_fields = set(fields_list).difference(set(values[0].keys()))
	i = 0
	values_len = len(values)
	odoo2_user_id = odoo2.env.user.id
	while i < values_len:
		val = values[i]
		for field_many2one in fields_many2one:
			val[field_many2one] = val[field_many2one] and val[field_many2one][0] or False
		del val['__last_update']
		del val['display_name']
		for k,v in val.items():
			if type(v) == bool and fields_info[k]['type'] != 'boolean':
				default = fields_info[k]['default']
				val[k] = default
		for not_existed_field in not_existed_fields:
			val.update({not_existed_field: fields_info[not_existed_field]['default']})
		val['create_uid'] = val['write_uid'] = odoo2_user_id
		i+=1
	payload = {'username': username2, 'password': password2, 'model': target_model, 'fields_info': fields_info, 'values': values}
	print('Sending values of %s to target.....' %target_model)
	print('====================================================================')
	print(send_request(payload))
	return True

for file_name in listdir:
	if file_name in file_consumed or os.path.isdir(directory+'/'+file_name):
		continue
	migrate_csv(file_name)

import pdb;pdb.set_trace()