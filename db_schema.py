from flask_sqlalchemy import SQLAlchemy #, ForeignKey
from flask_login import UserMixin

from werkzeug import security
import datetime
from sqlalchemy.inspection import inspect

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


# create the database interface
db = SQLAlchemy()


class Users(db.Model, UserMixin):
    __tablename__='users'
    id = db.Column(db.Integer, primary_key=True)#, autoincrement=True, default=0)
    username = db.Column(db.String(20), unique=True)
    password_hash = db.Column(db.String())
    fname = db.Column(db.String())
    lname = db.Column(db.String())
    email = db.Column(db.String(), unique=True)
    debt_budget = db.Column(db.Numeric(10,2))
                         
    def __init__(self, username, password_hash, fname, lname, email):
        self.username=username
        self.password_hash=password_hash
        self.fname=fname
        self.lname=lname
        self.email=email


class Incomes(db.Model):
    __tablename__='incomes'
    id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    # name = db.Column(db.String(20), primary_key=True)
    amount = db.Column(db.Numeric(10,2))
    # iclass = db.Column(db.String()) #weekly / monthly / yearly
    # ranges = db.Column(db.String()) #used to store range when user receives income e.g. if on months 1-3, 5-7, ranges would be "1-3,5-7" or something

    def __init__(self, id, name, amount, iclass, ranges):
        self.id=id
        # self.name=name
        self.amount=amount
        # self.iclass=iclass
        # self.ranges=ranges
        
#name is name of each thing

class Debts(db.Model):
    __tablename__='debts'
    id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    name = db.Column(db.String(20), primary_key=True)
    amount = db.Column(db.Numeric(10,2))
    minPayment = db.Column(db.Numeric(10,2))
    interest = db.Column(db.Numeric(5,2))
    startDate = db.Column(db.String(), default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    dueDate = db.Column(db.String(), default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) # user input
    chosenDueDate = db.Column(db.String(), default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) # user input
    # accruedAnnualInterest = db.Column(db.Numeric(10,2), default=0.0)
    # dclass = db.Column(db.String()) #weekly, monthly etc


    def __init__(self, id, name, amount, minPayment, interest, startDate, dueDate, chosenDueDate):#, accruedAnnualInterest, dclass):
        self.id=id
        self.name=name
        self.amount=amount
        self.minPayment=minPayment
        self.interest=interest
        self.startDate=startDate
        self.dueDate=dueDate
        self.chosenDueDate=chosenDueDate
        #self.accruedAnnualInterest=accruedAnnualInterest
        #self.dclass=dclass

class Expenses(db.Model):
    __tablename__='expenses'
    id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    # name = db.Column(db.String(20), primary_key=True)
    amount = db.Column(db.Numeric(10,2))
    # eclass = db.Column(db.String()) #weekly / monthly / yearly

    def __init__(self, id, name, amount, eclass):
        self.id=id
        self.name=name
        # self.amount=amount
        # self.eclass=eclass


def dbinit():
    db.create_all()
    # Create a new user
    user = Users(username='user1', 
                 password_hash='hashed_password_example', 
                 email='user1@example.com', fname="bleh", lname='blah')

    # Add the user to the session
    db.session.add(user)

    # Add debt_budget to user
    record = Users.query.filter_by(username='user1').first()
    record.debt_budget = 50000
    db.session.commit()

    # Create different debts for the user
    debts = [
        Debts(id=0, name='Car Loan', amount=20000.00, minPayment=500.00, interest=5.00, 
               startDate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
               dueDate=datetime.datetime.now() + datetime.timedelta(days=365), 
               chosenDueDate=datetime.datetime.now() + datetime.timedelta(days=365)),#, 
               #accruedAnnualInterest=0.00, dclass='Auto'),
        
        Debts(id=0, name='Student Loan', amount=15000.00, minPayment=300.00, interest=4.50, 
               startDate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
               dueDate=datetime.datetime.now() + datetime.timedelta(days=5*365), 
               chosenDueDate=datetime.datetime.now() + datetime.timedelta(days=5*365)),#, 
               #accruedAnnualInterest=0.00, dclass='Education'),
        
        Debts(id=0, name='Credit Card', amount=5000.00, minPayment=150.00, interest=18.00, 
               startDate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
               dueDate=datetime.datetime.now() + datetime.timedelta(days=30), 
               chosenDueDate=datetime.datetime.now() + datetime.timedelta(days=30)),#, 
               #accruedAnnualInterest=0.00, dclass='Credit'),
        
        Debts(id=0, name='Personal Loan', amount=10000.00, minPayment=250.00, interest=6.00, 
               startDate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
               dueDate=datetime.datetime.now() + datetime.timedelta(days=3*365), 
               chosenDueDate=datetime.datetime.now() + datetime.timedelta(days=3*365)),#, 
               #accruedAnnualInterest=0.00, dclass='Personal'),
        
        Debts(id=0, name='Mortgage', amount=250000.00, minPayment=1200.00, interest=3.75, 
               startDate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
               dueDate=datetime.datetime.now() + datetime.timedelta(days=30*365), 
               chosenDueDate=datetime.datetime.now() + datetime.timedelta(days=30*365)),#, 
               #accruedAnnualInterest=0.00, dclass='Real Estate'),
    ]

    # Add each debt to the session
    for debt in debts:
        db.session.add(debt)

    # Commit the session to save the user and debts in the database
    db.session.commit()

    # tables = inspect(db.engine).get_table_names()
    # if len(tables) > 0:
    #     print(f"The database contains these tables already\n{tables}" )
    #     return