# coding: utf8
import csv
import os
import sys
from odoo_object_xmlrpc import OdooObject

os.environ["PYTHONIOENCODING"] = "utf-8"
if not os.path.exists('csv'):
    os.mkdir('csv')

url1 = sys.argv[1]
db1 = sys.argv[2]
username1 = sys.argv[3]
password1 = sys.argv[4]

url2 = sys.argv[5]
db2 = sys.argv[6]
username2 = sys.argv[7]
password2 = sys.argv[8]

current_path = os.getcwd()

print('Odoo Source')
object1 = OdooObject(url1, db1, username1, password1)
print('====================================================================')
print('Odoo Target')
object2 = OdooObject(url2, db2, username2, password2)
print('====================================================================')

module1_lst = object1.search_read('ir.module.module', [['state', '=', 'installed']], ['name', 'shortdesc'])
module2_lst = object2.search_read('ir.module.module', [['state', '=', 'installed']], ['name', 'shortdesc'])

module2_name_dict = {module['name']: module['shortdesc'] for module in module2_lst}

module1_name_set = set([module['name'] for module in module1_lst])
module2_name_set = set([module['name'] for module in module2_lst])

modules_intersection = module2_name_set.intersection(module1_name_set)
modules_difference = module2_name_set.difference(module1_name_set)

with open(current_path+'\\csv\\'+'modules_list.csv', mode='w') as module_list_file:
    model_writer = csv.writer(module_list_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
    model_writer.writerow(['no', 'technical_name', 'name'])
    no=1
    for module_name in modules_intersection:
        name = module2_name_dict[module_name]
        model_writer.writerow([no, module_name, name])
        no+=1
    model_writer.writerow(['', ''])
    for module_name in modules_difference:
        module = module2_name_dict[module_name]
        model_writer.writerow([no, module_name, name])
        no+=1

import pdb;pdb.set_trace()