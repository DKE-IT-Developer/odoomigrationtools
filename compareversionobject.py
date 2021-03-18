# Set one model to migrate
# Get csv file of mapped fields of model
# format of migration column
# source model, source_model, target model, target_model
# list of same fields name, version and label string
# list of difference version 1 fields name and label string
# list of difference version 2 fields name and label string
# coding: utf8
import csv
import os
import sys
import odoorpc

os.environ["PYTHONIOENCODING"] = "utf-8"
current_path = os.getcwd()
csv_dir = current_path+'/'+'csv_version_object'
csv_model_inter = csv_dir+'/'+'model_intersection'
csv_model_diff1 = csv_dir+'/'+'model_difference1'
csv_model_diff2 = csv_dir+'/'+'model_difference2'
if not os.path.exists(csv_dir):
    os.mkdir(csv_dir)
if not os.path.exists(csv_model_inter):
    os.mkdir(csv_model_inter)
if not os.path.exists(csv_model_diff1):
    os.mkdir(csv_model_diff1)
if not os.path.exists(csv_model_diff2):
    os.mkdir(csv_model_diff2)

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

object1_models = odoo2.env['ir.model'].search_read([], ['model', 'transient'])
object2_models = odoo2.env['ir.model'].search_read([], ['model', 'transient'])

model1_names = [model['model'] for model in object1_models]
model2_names = {model['model']:model['transient'] for model in object2_models}

model1_names_set = set(model1_names)
model2_names_set = set(model2_names.keys())

models_intersection = model2_names_set.intersection(model1_names_set)
models1_difference = model1_names_set.difference(model2_names_set)
models2_difference = model2_names_set.difference(model1_names_set)

for model_name in models_intersection:
    with open('%s/'%(csv_model_inter)+model_name+'.csv', mode='w') as model_file:
        model_writer = csv.writer(model_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        print('Writing %s structure' %model_name)
        print('====================================================================')
        no=1
        model_writer.writerow(['model', model_name, 'transient', model2_names[model_name]])
        try:
            fields1 = odoo1.env[model_name].fields_get()
            fields2 = odoo2.env[model_name].fields_get()
            fields1_dict = fields1
            fields2_dict = fields2
        except:
            failed_msg = 'failed to get fields list of %s' %model_name
            model_writer.writerow([failed_msg])
            model_writer.writerow(['', '', '', '', ''])
            print(failed_msg)
            continue
        fields_intersection = set(fields2.keys()).intersection(fields1.keys())
        fields1_difference = set(fields1.keys()).difference(fields2.keys())
        fields2_difference = set(fields2.keys()).difference(fields1.keys())
        model_writer.writerow(['no', 'field', 'type1', 'type2', 'relation', 'string1', 'string2', 'source'])
        for field in fields_intersection:
            field1_attr = fields1_dict[field]
            field2_attr = fields2_dict[field]
            model_writer.writerow([no, field, field1_attr['type'], field2_attr['type'], field2_attr.get('relation', ''), field1_attr['string'].encode('utf-8'), field2_attr['string'].encode('utf-8'), 'both'])
            no+=1
        model_writer.writerow(['', '', '', '', ''])
        for field in fields1_difference:
            field_attr = fields1[field]
            model_writer.writerow([no, field, field_attr['type'], '', field_attr.get('relation', ''), field_attr['string'].encode('utf-8'), '', 'version 1'])
            no+=1
        model_writer.writerow(['', '', '', '', ''])
        for field in fields2_difference:
            field_attr = fields2[field]
            model_writer.writerow([no, field, '', field_attr['type'], field_attr.get('relation', ''), '', field_attr['string'].encode('utf-8'), 'version 2'])
            no+=1
        model_writer.writerow(['', '', '', '', ''])
        model_writer.writerow(['', '', '', '', ''])

for model_name in models2_difference:
    with open('%s/'%(csv_model_diff1)+model_name+'.csv', mode='w') as model_file:
        model_writer = csv.writer(model_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        print('Writing %s structure' %model_name)
        print('====================================================================')
        no=1
        model_writer.writerow(['model', model_name, 'transient', model2_names[model_name]])
        try:
            fields1 = odoo1.env[model_name].fields_get()
            fields2 = odoo2.env[model_name].fields_get()
            fields1_dict = fields1
            fields2_dict = fields2
        except:
            failed_msg = 'failed to get fields list of %s' %model_name
            model_writer.writerow([failed_msg])
            model_writer.writerow(['', '', '', '', ''])
            print(failed_msg)
            continue
        fields_intersection = set(fields2.keys()).intersection(fields1.keys())
        model_writer.writerow(['no', 'field', 'type1', 'type2', 'relation', 'string1', 'string2', 'source'])
        for field in fields_intersection:
            field1_attr = fields1_dict[field]
            field2_attr = fields2_dict[field]
            model_writer.writerow([no, field, field1_attr['type'], field2_attr['type'], field_attr.get('relation', ''), field1_attr['string'].encode('utf-8'), field2_attr['string'].encode('utf-8'), 'both'])
            no+=1
        model_writer.writerow(['', '', '', '', ''])
        for field in fields1_difference:
            field_attr = fields2[field]
            model_writer.writerow([no, field, field_attr['type'], '', field_attr.get('relation', ''), field1_attr['string'].encode('utf-8'), '', 'version 1'])
            no+=1
        for field in fields2_difference:
            field_attr = fields2[field]
            model_writer.writerow([no, field, '', field_attr['type'], field_attr.get('relation', ''), '', field2_attr['string'].encode('utf-8'), 'version 2'])
            no+=1
        model_writer.writerow(['', '', '', '', ''])
        model_writer.writerow(['', '', '', '', ''])

import pdb;pdb.set_trace()