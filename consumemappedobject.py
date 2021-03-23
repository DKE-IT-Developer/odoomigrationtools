import csv
import os
import sys
import odoorpc
import psycopg2

# set source directory of mapped object csv file
# read file of object in file format 'object.csv'
# read file csv of format no,field1,type1,relation1,field2,type2,relation2,default
# read object's field in sql table and find inherited object table's field
# read relational fields record data as set type
# insert to inherited object's table
# insert to related object's table
# insert to object's table

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
for file_name in listdir:
	csv_file = open(directory+'/'+file_name)
	csv_read = csv.reader(csv_file, delimiter=';')
	import pdb;pdb.set_trace()
	for row in csv_read:
		field1 = row[1]
		type1 = row[2]
		relation1 = row[3]
		field2 = row[4]
		type2 = row[5]
		relation2 = row[6]
		default = row[7]

import pdb;pdb.set_trace()