"""PrintFlow - Project 69 working reference backend.
SQLite out of the box; set DATABASE_URL for PostgreSQL.
"""
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Numeric, DateTime, CheckConstraint, UniqueConstraint, event, select, func
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from sqlalchemy.exc import IntegrityError

DB_URL = os.getenv('DATABASE_URL', 'sqlite:///./printflow.db')
engine = create_engine(DB_URL, connect_args={'check_same_thread': False} if DB_URL.startswith('sqlite') else {}, pool_pre_ping=True)
if DB_URL.startswith('sqlite'):
    @event.listens_for(engine, 'connect')
    def _sqlite_fk(dbapi_conn, _): dbapi_conn.execute('PRAGMA foreign_keys=ON')
Session = sessionmaker(engine, expire_on_commit=False)
class Base(DeclarativeBase): pass
class Customer(Base):
    __tablename__='customers'
    id=Column(Integer,primary_key=True); name=Column(String(150),nullable=False); email=Column(String(150)); phone=Column(String(25))
class Material(Base):
    __tablename__='materials'
    id=Column(Integer,primary_key=True); name=Column(String(120),nullable=False,unique=True); unit=Column(String(20),nullable=False,default='kg'); stock=Column(Numeric(12,2),nullable=False,default=0); reorder_level=Column(Numeric(12,2),nullable=False,default=10); unit_cost=Column(Numeric(12,2),nullable=False,default=0)
    __table_args__=(CheckConstraint('stock>=0'),CheckConstraint('unit_cost>=0'),)
class Machine(Base):
    __tablename__='machines'
    id=Column(Integer,primary_key=True); name=Column(String(120),nullable=False,unique=True); status=Column(String(20),nullable=False,default='AVAILABLE')
class Quotation(Base):
    __tablename__='quotations'
    id=Column(Integer,primary_key=True); customer_id=Column(Integer,ForeignKey('customers.id'),nullable=False); description=Column(String(250),nullable=False); quantity=Column(Integer,nullable=False); unit_price=Column(Numeric(12,2),nullable=False); status=Column(String(20),nullable=False,default='DRAFT')
    __table_args__=(CheckConstraint('quantity>0'),CheckConstraint('unit_price>=0'),)
class Job(Base):
    __tablename__='jobs'
    id=Column(Integer,primary_key=True); job_number=Column(String(30),nullable=False,unique=True); customer_id=Column(Integer,ForeignKey('customers.id'),nullable=False); quotation_id=Column(Integer,ForeignKey('quotations.id')); title=Column(String(180),nullable=False); quantity=Column(Integer,nullable=False); delivered_qty=Column(Integer,nullable=False,default=0); status=Column(String(25),nullable=False,default='NEW'); created_at=Column(DateTime,default=lambda:datetime.now(timezone.utc).replace(tzinfo=None))
    __table_args__=(CheckConstraint('quantity>0'),CheckConstraint('delivered_qty>=0 AND delivered_qty<=quantity'),)
class Issue(Base):
    __tablename__='material_issues'
    id=Column(Integer,primary_key=True); job_id=Column(Integer,ForeignKey('jobs.id'),nullable=False); material_id=Column(Integer,ForeignKey('materials.id'),nullable=False); quantity=Column(Numeric(12,2),nullable=False); issued_at=Column(DateTime,default=lambda:datetime.now(timezone.utc).replace(tzinfo=None));
    __table_args__=(CheckConstraint('quantity>0'),)
class Schedule(Base):
    __tablename__='schedules'
    id=Column(Integer,primary_key=True); job_id=Column(Integer,ForeignKey('jobs.id'),nullable=False); machine_id=Column(Integer,ForeignKey('machines.id'),nullable=False); start_at=Column(DateTime,nullable=False); end_at=Column(DateTime,nullable=False)
    __table_args__=(CheckConstraint('end_at>start_at'),)
class Stage(Base):
    __tablename__='stages'
    id=Column(Integer,primary_key=True); job_id=Column(Integer,ForeignKey('jobs.id'),nullable=False); stage_name=Column(String(30),nullable=False); status=Column(String(20),nullable=False,default='PENDING'); notes=Column(String(300));
    __table_args__=(UniqueConstraint('job_id','stage_name'),)
class Delivery(Base):
    __tablename__='deliveries'
    id=Column(Integer,primary_key=True); job_id=Column(Integer,ForeignKey('jobs.id'),nullable=False); quantity=Column(Integer,nullable=False); delivered_at=Column(DateTime,default=lambda:datetime.now(timezone.utc).replace(tzinfo=None));
    __table_args__=(CheckConstraint('quantity>0'),)
class Invoice(Base):
    __tablename__='invoices'
    id=Column(Integer,primary_key=True); job_id=Column(Integer,ForeignKey('jobs.id'),nullable=False,unique=True); total=Column(Numeric(12,2),nullable=False); created_at=Column(DateTime,default=lambda:datetime.now(timezone.utc).replace(tzinfo=None))
    __table_args__=(CheckConstraint('total>=0'),)
class Payment(Base):
    __tablename__='payments'
    id=Column(Integer,primary_key=True); invoice_id=Column(Integer,ForeignKey('invoices.id'),nullable=False); amount=Column(Numeric(12,2),nullable=False); method=Column(String(30),nullable=False,default='UPI'); paid_at=Column(DateTime,default=lambda:datetime.now(timezone.utc).replace(tzinfo=None))
    __table_args__=(CheckConstraint('amount>0'),)
Base.metadata.create_all(engine)
app=FastAPI(title='PrintFlow | Project 69',version='1.0.0')
app.add_middleware(CORSMiddleware,allow_origins=os.getenv('CORS_ORIGINS','http://localhost:5173,http://127.0.0.1:5173').split(','),allow_methods=['*'],allow_headers=['*'])
class CustomerIn(BaseModel): name:str=Field(min_length=1,max_length=150); email:str=''; phone:str=''
class MaterialIn(BaseModel): name:str; unit:str='kg'; stock:float=Field(ge=0); reorder_level:float=Field(ge=0,default=10); unit_cost:float=Field(ge=0,default=0)
class MachineIn(BaseModel): name:str
class QuotationIn(BaseModel): customer_id:int; description:str; quantity:int=Field(gt=0); unit_price:float=Field(ge=0)
class JobIn(BaseModel): customer_id:int; title:str; quantity:int=Field(gt=0); quotation_id:int|None=None
class IssueIn(BaseModel): job_id:int; material_id:int; quantity:float=Field(gt=0)
class ScheduleIn(BaseModel): job_id:int; machine_id:int; start_at:datetime; end_at:datetime
class StageIn(BaseModel): job_id:int; stage_name:str; status:str='PENDING'; notes:str=''
class DeliveryIn(BaseModel): job_id:int; quantity:int=Field(gt=0)
class InvoiceIn(BaseModel): job_id:int; total:float=Field(ge=0)
class PaymentIn(BaseModel): invoice_id:int; amount:float=Field(gt=0); method:str='UPI'
MODELS={'customers':Customer,'materials':Material,'machines':Machine,'quotations':Quotation,'jobs':Job,'issues':Issue,'schedules':Schedule,'stages':Stage,'deliveries':Delivery,'invoices':Invoice,'payments':Payment}
SCHEMAS={'customers':CustomerIn,'materials':MaterialIn,'machines':MachineIn,'quotations':QuotationIn,'jobs':JobIn,'issues':IssueIn,'schedules':ScheduleIn,'stages':StageIn,'deliveries':DeliveryIn,'invoices':InvoiceIn,'payments':PaymentIn}
EDITABLE={'customers','materials','machines','quotations'}
def output(obj):
    return {c.name:(str(getattr(obj,c.name)) if isinstance(getattr(obj,c.name),Decimal) else getattr(obj,c.name).isoformat() if isinstance(getattr(obj,c.name),datetime) else getattr(obj,c.name)) for c in obj.__table__.columns}
def get(db, model,id):
    x=db.get(model,id)
    if x is None: raise HTTPException(404,f'{model.__tablename__} item not found')
    return x
def fail(ex):
    raise HTTPException(400,'Invalid input or database constraint violated: '+str(ex.orig)[:160])
@app.get('/api/health')
def health(): return {'status':'ok','database':'postgresql' if DB_URL.startswith('postgres') else 'sqlite'}
@app.get('/api/{resource}')
def list_resources(resource:str, q:str=''):
    if resource not in MODELS: raise HTTPException(404,'Unknown resource')
    m=MODELS[resource]
    with Session() as db:
        rows=db.scalars(select(m).order_by(m.id.desc()).limit(300)).all()
        if q: rows=[r for r in rows if q.casefold() in str(output(r)).casefold()]
        return [output(r) for r in rows]
@app.post('/api/{resource}',status_code=201)
def create_resource(resource:str, body:dict[str,Any]):
    if resource not in MODELS: raise HTTPException(404,'Unknown resource')
    try: data=SCHEMAS[resource].model_validate(body).model_dump()
    except Exception as ex: raise HTTPException(422,str(ex))
    with Session.begin() as db:
        if resource=='jobs':
            get(db,Customer,data['customer_id'])
            if data.get('quotation_id'):
                q=get(db,Quotation,data['quotation_id'])
                if q.customer_id!=data['customer_id']:raise HTTPException(400,'Quotation customer must match job customer')
            data['job_number']=f'JOB-{datetime.now().strftime("%Y%m%d%H%M%S%f")}'
        if resource=='quotations': get(db,Customer,data['customer_id'])
        if resource=='issues':
            get(db,Job,data['job_id']); mat=get(db,Material,data['material_id'])
            if Decimal(str(data['quantity']))>mat.stock:raise HTTPException(400,'Insufficient material stock')
            mat.stock-=Decimal(str(data['quantity']))
        if resource=='schedules':
            get(db,Job,data['job_id']);get(db,Machine,data['machine_id'])
            if data['end_at']<=data['start_at']:raise HTTPException(400,'End must be later than start')
            overlaps=db.scalar(select(func.count()).select_from(Schedule).where(Schedule.machine_id==data['machine_id'],Schedule.start_at<data['end_at'],Schedule.end_at>data['start_at']))
            if overlaps:raise HTTPException(400,'Machine has overlapping schedule')
            data['start_at']=data['start_at'].replace(tzinfo=None);data['end_at']=data['end_at'].replace(tzinfo=None)
        if resource=='stages':
            job=get(db,Job,data['job_id']); order=['DESIGN','PREPRESS','PRINTING','FINISHING','PACKING']
            name=data['stage_name'].upper(); status=data['status'].upper()
            if name not in order or status not in ('PENDING','IN_PROGRESS','DONE'):raise HTTPException(400,'Invalid production stage or status')
            data['stage_name']=name;data['status']=status
            if status=='DONE' and any(not db.scalar(select(Stage).where(Stage.job_id==job.id,Stage.stage_name==p,Stage.status=='DONE')) for p in order[:order.index(name)]): raise HTTPException(400,'Earlier stages must be DONE first')
        if resource=='deliveries':
            job=get(db,Job,data['job_id'])
            if job.delivered_qty+data['quantity']>job.quantity:raise HTTPException(400,'Delivery exceeds ordered quantity')
            job.delivered_qty+=data['quantity'];job.status='DELIVERED' if job.delivered_qty==job.quantity else 'PARTIAL'
        if resource=='invoices':get(db,Job,data['job_id'])
        if resource=='payments':
            inv=get(db,Invoice,data['invoice_id'])
            paid=db.scalar(select(func.coalesce(func.sum(Payment.amount),0)).where(Payment.invoice_id==inv.id))
            if paid+Decimal(str(data['amount']))>inv.total:raise HTTPException(400,'Payment exceeds invoice balance')
        obj=MODELS[resource](**data);db.add(obj)
        try:db.flush(); result=output(obj)
        except IntegrityError as ex:fail(ex)
    return result
@app.put('/api/{resource}/{item_id}')
def update_resource(resource:str,item_id:int,body:dict[str,Any]):
    if resource not in EDITABLE:raise HTTPException(405,'Updates restricted to master data')
    try:data=SCHEMAS[resource].model_validate(body).model_dump()
    except Exception as ex:raise HTTPException(422,str(ex))
    with Session.begin() as db:
        obj=get(db,MODELS[resource],item_id)
        if resource=='quotations' and obj.status!='DRAFT': raise HTTPException(400,'Only draft quotations editable')
        for k,v in data.items():setattr(obj,k,v)
        try:db.flush();result=output(obj)
        except IntegrityError as ex:fail(ex)
    return result
@app.delete('/api/{resource}/{item_id}')
def delete_resource(resource:str,item_id:int):
    if resource not in EDITABLE:raise HTTPException(405,'Historical transactions cannot be deleted')
    with Session.begin() as db:
        obj=get(db,MODELS[resource],item_id);db.delete(obj)
        try:db.flush()
        except IntegrityError as ex:fail(ex)
    return {'deleted':True}
@app.get('/api/reports/summary')
def report_summary():
    with Session() as db:
        def count(m):return db.scalar(select(func.count()).select_from(m)) or 0
        revenue=db.scalar(select(func.coalesce(func.sum(Payment.amount),0))) or 0
        pending=db.scalar(select(func.count()).select_from(Job).where(Job.status!='DELIVERED')) or 0
        low=[output(m) for m in db.scalars(select(Material).where(Material.stock<=Material.reorder_level)).all()]
        invoices=[output(i) for i in db.scalars(select(Invoice)).all()]
        for i in invoices:
            paid=db.scalar(select(func.coalesce(func.sum(Payment.amount),0)).where(Payment.invoice_id==i['id'])) or 0
            i['paid']=str(paid);i['balance']=str(Decimal(i['total'])-paid)
        return {'customers':count(Customer),'jobs':count(Job),'pending_jobs':pending,'machines':count(Machine),'revenue':str(revenue),'low_stock':low,'invoices':invoices}
@app.post('/api/demo-seed')
def seed_demo():
    with Session.begin() as db:
        if db.scalar(select(func.count()).select_from(Customer)):return {'message':'Seed skipped - customer records already exist'}
        db.add_all([Customer(name='Woxsen Events',email='events@example.edu',phone='9000000000'),Customer(name='City Books',email='orders@example.org',phone='9111111111')])
        db.add_all([Material(name='Art Paper',unit='sheets',stock=1500,reorder_level=250,unit_cost=3.5),Material(name='CMYK Ink',unit='litres',stock=70,reorder_level=15,unit_cost=400)])
        db.add_all([Machine(name='Offset Press A'),Machine(name='Digital Press B'),Machine(name='Binding Line')])
    return {'message':'Sample customers, materials and machines created'}
