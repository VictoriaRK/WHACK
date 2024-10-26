from flask_sqlalchemy import SQLAlchemy #, ForeignKey
from flask_login import UserMixin

from werkzeug import security
import datetime
from sqlalchemy.inspection import inspect

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


# create the database interface
db = SQLAlchemy()


class Users(db.Model):
    __tablename__='users'
    username = db.Column(db.String(20), primary_key=True)
    password_hash = db.Column(db.String())
    salt = db.Column(db.String())
    email = db.Column(db.String(), unique=True)
    debt_budget=db.Column(db.Numeric(10,2))

    def __init__(self, username, password, salt, email):
        self.username=username
        self.password=password
        self.salt=salt
        self.email=email


class Incomes(db.Model):
    __tablename__='incomes'
    username = db.Column(db.String(20), db.ForeignKey("users.username"), primary_key=True)
    name = db.Column(db.String(20), primary_key=True)
    amount = db.Column(db.Numeric(10,2))
    iclass = db.Column(db.String())          #monthly, yearly
    ranges = db.Column(db.ARRAY(db.Integer)) #

    def __init__(self, username, name, amount, iclass, ranges):
        self.username=username
        self.name=name
        self.amount=amount
        self.iclass=iclass
        self.ranges=ranges
        
#name is name of each thing

class Debts(db.Model):
    __tablename__='debts'
    username = db.Column(db.String(20), db.ForeignKey("users.username"), primary_key=True)
    name = db.Column(db.String(20), primary_key=True)
    amount = db.Column(db.Numeric(10,2))
    minPayment = db.Column(db.Numeric(10,2))
    interest = db.Column(db.Numeric(5,2))
    startDate = db.Column(db.String(), default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    dueDate = db.Column(db.String(), default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) # user input - 
    chosenDueDate = db.Column(db.String(), default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) # user input
    #accruedAnnualInterest = db.Column(db.Numeric(10,2), default=0.0)
    dclass = db.Column(db.String()) #weekly, monthly etc


    def __init__(self, username, name, amount, minPayment, interest, startDate, dueDate, chosenDueDate, accruedAnnualInterest, dclass):
        self.username=username
        self.name=name
        self.amount=amount
        self.minPayment=minPayment
        self.interest=interest
        self.startDate=startDate
        self.dueDate=dueDate
        self.chosenDueDate=chosenDueDate
        self.accruedAnnualInterest=accruedAnnualInterest
        self.dclass=dclass

class Expenses(db.Model):
    __tablename__='expenses'
    username = db.Column(db.String(20), db.ForeignKey("users.username"), primary_key=True)
    name = db.Column(db.String(20), primary_key=True)
    amount = db.Column(db.Numeric(10,2))
    eclass = db.Column(db.String())

    def __init__(self, username, name, amount, eclass):
        self.username=username
        self.name=name
        self.amount=amount
        self.eclass=eclass


def dbinit():
    
    db.drop_all()
    # Create a new user
    user = Users(username='user1', 
                 password_hash='hashed_password_example', 
                 salt='salt_value_example', 
                 email='user1@example.com')

    # Add the user to the session
    db.session.add(user)

    # Create different debts for the user
    debts = [
        Debts(username='user1', name='Car Loan', amount=20000.00, minPayment=500.00, interest=5.00, 
               startDate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
               dueDate=datetime.datetime.now() + datetime.timedelta(days=365), 
               chosenDueDate=datetime.datetime.now() + datetime.timedelta(days=365), 
               accruedAnnualInterest=0.00, dclass='Auto'),
        
        Debts(username='user1', name='Student Loan', amount=15000.00, minPayment=300.00, interest=4.50, 
               startDate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
               dueDate=datetime.datetime.now() + datetime.timedelta(days=5*365), 
               chosenDueDate=datetime.datetime.now() + datetime.timedelta(days=5*365), 
               accruedAnnualInterest=0.00, dclass='Education'),
        
        Debts(username='user1', name='Credit Card', amount=5000.00, minPayment=150.00, interest=18.00, 
               startDate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
               dueDate=datetime.datetime.now() + datetime.timedelta(days=30), 
               chosenDueDate=datetime.datetime.now() + datetime.timedelta(days=30), 
               accruedAnnualInterest=0.00, dclass='Credit'),
        
        Debts(username='user1', name='Personal Loan', amount=10000.00, minPayment=250.00, interest=6.00, 
               startDate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
               dueDate=datetime.datetime.now() + datetime.timedelta(days=3*365), 
               chosenDueDate=datetime.datetime.now() + datetime.timedelta(days=3*365), 
               accruedAnnualInterest=0.00, dclass='Personal'),
        
        Debts(username='user1', name='Mortgage', amount=250000.00, minPayment=1200.00, interest=3.75, 
               startDate=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
               dueDate=datetime.datetime.now() + datetime.timedelta(days=30*365), 
               chosenDueDate=datetime.datetime.now() + datetime.timedelta(days=30*365), 
               accruedAnnualInterest=0.00, dclass='Real Estate'),
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

    db.create_all()
    '''user_list = [
        Users(username="thesuperhumanpear", email="Victoria.Krushovska@warwick.ac.uk", fname="Victoria", lname="Krushovska", password_hash=security.generate_password_hash("securityWOW234"), is_super=True), 
        Users(username="thehumanpear", email="vkrushovska@gmail.com", fname="Vicky", lname="Krusha", password_hash=security.generate_password_hash("sucha_gooDPassword"), is_super=False)
        ]
    db.session.add_all(user_list)

    all_events = [
        Events(event_name="The future of Web Dev", event_info="With AI usage on the rise, how will this impact the way we view web development? What tools should we expect from the future? Why is this important?", date="2025-08-20", time="15:30", duration=120, max_capacity=100, location="L4", cancellable=False),
        Events(event_name="Graphs: What are they and why do we care?", event_info="A deepdive into graph theory and its practical applications.", date="2024-05-24", time="10:30", duration=240, max_capacity=300, location="MS02", cancellable=True)
        ]
    db.session.add_all(all_events)


    all_bookings = [
        #Tickets(user_id=Users.query.filter_by(username="thehumanpear").first().id, event_id=Events.query.filter_by(event_name="Intro to Absurdism in Computer Science").first().id)
        Tickets(user_id=2, event_id=2)
        ]
    db.session.add_all(all_bookings)

    # commit all the changes to the database file
    db.session.commit()'''