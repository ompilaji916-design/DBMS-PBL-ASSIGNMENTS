"""Basic API integration test; run with backend dependencies installed."""
import os, tempfile
import sys; from pathlib import Path; sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
fd,path=tempfile.mkstemp(suffix='.db'); os.close(fd)
os.environ['DATABASE_URL']='sqlite:///'+path
from fastapi.testclient import TestClient
from backend.main import app
c=TestClient(app)
def create(k, payload):
 r=c.post('/api/'+k,json=payload);assert r.status_code==201,(k,r.text);return r.json()
assert c.get('/api/health').status_code==200
customer=create('customers',{'name':'Demo Test'})
mat=create('materials',{'name':'Paper','stock':10,'reorder_level':2,'unit_cost':5})
machine=create('machines',{'name':'Press 1'})
quote=create('quotations',{'customer_id':customer['id'],'description':'Flyer','quantity':100,'unit_price':3})
job=create('jobs',{'customer_id':customer['id'],'quotation_id':quote['id'],'title':'Flyers','quantity':100})
create('issues',{'job_id':job['id'],'material_id':mat['id'],'quantity':4})
assert c.post('/api/issues',json={'job_id':job['id'],'material_id':mat['id'],'quantity':50}).status_code==400
create('schedules',{'job_id':job['id'],'machine_id':machine['id'],'start_at':'2026-11-01T10:00:00','end_at':'2026-11-01T12:00:00'})
assert c.post('/api/schedules',json={'job_id':job['id'],'machine_id':machine['id'],'start_at':'2026-11-01T11:00:00','end_at':'2026-11-01T13:00:00'}).status_code==400
for name in ['DESIGN','PREPRESS','PRINTING','FINISHING','PACKING']:
 create('stages',{'job_id':job['id'],'stage_name':name,'status':'DONE'})
create('deliveries',{'job_id':job['id'],'quantity':80})
assert c.post('/api/deliveries',json={'job_id':job['id'],'quantity':40}).status_code==400
invoice=create('invoices',{'job_id':job['id'],'total':300})
create('payments',{'invoice_id':invoice['id'],'amount':130,'method':'UPI'})
assert c.post('/api/payments',json={'invoice_id':invoice['id'],'amount':200}).status_code==400
summary=c.get('/api/reports/summary');assert summary.status_code==200
assert summary.json()['revenue']=='130.00'
assert c.get('/api/jobs').json()[0]['job_number'].startswith('JOB-')
print('PASS: 15 endpoint, integrity and workflow assertions')
