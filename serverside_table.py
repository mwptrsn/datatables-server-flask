"""Testing serverside tables

"""
from flask import Flask, render_template, request, jsonify

import json
import random
import sqlite3

db = None
app = Flask(__name__)

def get_db():
	"""Creates the in-memory database for testing.
	"""
	global db
	
	data_rows = []
	for _ in range(1000):
		data_rows.append([random.choice('abcdefghij'), random.random(), 
					     random.randint(1,1500)])
	
	if db is None:
		db = sqlite3.connect(":memory:")
		with open("schema.sql") as file_handle:
			db.execute(file_handle.read())
		
		db.executemany("INSERT INTO test_data (first, second, third) VALUES (?,?,?)", 
		               data_rows)
	
	return db

@app.route('/')
def hello_world():
    return render_template('index.html')
    
def build_query(offset, length, ordering):
	"""Builds the query for the database. Processes ordering and pagination; Does
	not yet handle search.
	
	"""
	# We should have the column names defined by the table
	columns = [
		"first",
		"second",
		"third"
	]
	
	table_name = "test_data"
	
	select = f"SELECT {','.join(columns)} FROM {table_name} "
	limit = f"LIMIT {length} OFFSET {offset} "
	
	order_list = []
	for order_dict in ordering:
		column_name = columns[order_dict['column']]
		column_dir = 'ASC' if order_dict['dir'] == 'asc' else 'DESC'
		
		order_list.append(f"{column_name} {column_dir}")
	
	order_by = f"ORDER BY {','.join(order_list)}"
	
	query = f"{select} {order_by} {limit}"
	
	print(query)
	return query

@app.route('/table_api', methods=["POST"])
def table_data():
	db = get_db()
	
	args = json.loads(request.values.get("args"))
	print(args)
		
	# Get the total number of records
	total = db.execute("SELECT COUNT(*) from test_data").fetchone()[0]
	
	output = {}
	output["draw"] = int(args["draw"])
	output["recordsTotal"] = total
	
	
	order = args["order"]
	start = args["start"]
	length = args["length"]
	
	print(order, start, length)
	
	
	query = build_query(start, length, order)
	
	output["data"] = db.execute(query).fetchall()
	output["recordsFiltered"] = len(output["data"])
	
	return jsonify(output)