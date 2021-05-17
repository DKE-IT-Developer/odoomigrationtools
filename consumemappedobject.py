import csv
import os
import sys
import odoorpc
import psycopg2
import requests
import time

# set source directory of mapped object csv file
# read file of object in file format 'object.csv'
# read file csv of format no,field1,type1,relation1,field2,type2,relation2,default
# read object's field in sql table and find inherited object table's field
# read relational fields record data as set type
# insert to inherited object's table
# insert to related object's table
# insert to object's table

# To do
# Separate binary fields value if not use orm
# insert with orm
# update write date with sql

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
odoo1 = odoorpc.ODOO(host1, port=port1, timeout=9000)
odoo1.login(db1, username1, password1)
print('====================================================================')
print('Odoo Target')
odoo2 = odoorpc.ODOO(host2, port=port2, timeout=9000)
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
	csv_read.next()
	meta_info = csv_read.next()
	source_model = meta_info[0]
	target_model = meta_info[1]
	use_target_value = eval(meta_info[2].title()) if meta_info[2] else 0
	target_field_reference = meta_info[3].split(',')
	use_orm = eval(meta_info[4].title()) if meta_info[4] else 0
	skip_from_id = eval(meta_info[5]) if meta_info[5] else 0
	active_only = eval(meta_info[6].title()) if meta_info[6] else 0
	file_consumed.append(file_name)
	csv_read.next()
	# dictionary format
	# [{field_name: values}] payload format values
	# {fields_name: {convert: False, default: False}} fields_info
	fields_get1 = odoo1.env[source_model].fields_get()
	fields_get2 = odoo2.env[target_model].fields_get()
	fields_convert = []
	fields_info = {}
	fields_list1 = []
	fields_list2 = []
	fields_dict = {}
	fields_many2one = []
	target_value_many2one_fields = {}
	relation_target_value_included = []
	fields_binary = []
	not_existed_fields = []
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
		if type2 == 'binary' and not use_orm:
			fields_info.update({field2: {'convert': False, 'default': default or None, 'type': type2}})
			fields_binary.append(field2)
			fields_list1.append(field1)
			fields_list2.append(field2)
			fields_dict.update({field1: field2})
			continue
		if not fields_get2[field2]['store']:
			not_existed_fields.append(field2)
			continue
		if not field1 and not field2:
			continue
		fields_list1.append(field1)
		fields_dict.update({field1: field2})
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

		fields_list2.append(field2)
		if type2 == 'many2one' and field1:
			fields_many2one.append(field2)
	domain = []
	if 'active' in fields_get1:
		domain = ['|', ('active', '=', False), ('active', '=', True)]
	if not fields_list1:
		return

	if target_field_reference and target_field_reference[0] not in fields_list1:
		fields_list1.append(target_field_reference[0])
		type2 = fields_get2[target_field_reference[1]]['type']
		fields_info.update({target_field_reference[1]: {'convert': False, 'default': default or None, 'type': type2}})
		fields_dict.update({target_field_reference[0]: target_field_reference[1]})
	values = odoo1.env[source_model].search_read(domain, fields_list1, order='id')
	if not values:
		return
	
	i = 0
	values_len = len(values)
	odoo2_user_id = odoo2.env.user.id
	val_temp = values[0].copy()
	# sanitized binary fields
	binary_values = []
	while i < values_len:
		val = values[i]
		for field_many2one in fields_many2one:
			val[field_many2one] = val[field_many2one] and val[field_many2one][0] or False
		if '__last_update' in val:
			del val['__last_update']
		if 'display_name' in val:
			del val['display_name']
		binary_value = {}
		for k,v in val_temp.items():
			if k == 'id':
				continue
			v = val[k]
			field_name = fields_dict[k]
			if field_name in not_existed_fields:
				v.pop(k)
				continue
			if fields_info[field_name]['type'] == 'binary':
				field_value = val.pop(k)
				binary_value.update({'id': val['id'], field_name: field_value})
				continue
			elif type(v) == bool and fields_info[field_name]['type'] != 'boolean':
				default = fields_info[field_name]['default']
				val[field_name] = default
			if field_name != k:
				v = val.pop(k)
				val[field_name] = v
		if binary_value:
			binary_values.append(binary_value)
		if len(val) == 1:
			del values[i]
			values_len -= 1
			continue
		if val:
			val['create_uid'] = val['write_uid'] = odoo2_user_id
		i+=1
	# target_field_reference is required when using target values
	if use_target_value:
		domain2 = []
		if 'active' in fields_get2:
			domain2 = ['|', ('active', '=', False), ('active', '=', True)]
		fields_id_dict = {}
		values2 = odoo2.env[target_model].search_read(domain2, [target_field_reference[1]])
		for value in values:
			found = False
			fields_id_dict.update({value['id']: 0})
			for reference_value in values2:
				if reference_value[target_field_reference[1]] == value[target_field_reference[0]]:
					old_id = value['id']
					new_id = reference_value['id']
					fields_id_dict.update({old_id: new_id})
					found = True
				if found:
					break
			value['id'] = fields_id_dict[value['id']]
			value.pop(target_field_reference[1])
		
		for value in binary_values:
			new_id = fields_id_dict.get(value['id'], 0)
			value['id'] = new_id
		
		values_len = len(values)
		i = 0
		while i < values_len:
			val = values[i]
			if val['id'] == 0:
				del values[i]
				values_len -= 1
				continue
			i+=1

		values_len = len(binary_values)
		i = 0
		while i < values_len:
			val = binary_values[i]
			if val['id'] == 0:
				del binary_values[i]
				values_len -= 1
				continue
			i+=1

	if not use_orm:
		if values:
			payload = {'username': username2, 'password': password2, 'model': target_model, 'fields_info': fields_info, 'values': values}
			print('Sending values of %s to target.....' %target_model)
			print('====================================================================')
			print(send_request(payload))
		sleep_time = 1.0
		count = 0
		for value in binary_values:
			id = value.pop('id')
			count+=1
			print(count, "Sending binary of id %d" %(id))
			odoo2.env[target_model].write(id, value)
			time.sleep(sleep_time)
			sleep_time += 0.25
	else:
		for value in values:
			id = value.pop('id')
			odoo2.env[target_model].write(id, value)
	return True

for file_name in listdir:
	if file_name in file_consumed or os.path.isdir(directory+'/'+file_name):
		continue
	migrate_csv(file_name)