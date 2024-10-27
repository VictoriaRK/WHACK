from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for

from flask import make_response, render_template_string
from flask import session
from flask import request

from werkzeug import security
from flask_login import UserMixin, LoginManager, login_user, current_user, logout_user, login_required 
from flask import flash
import datetime
from sqlalchemy.exc import IntegrityError

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from flask_mail import Mail, Message

import os

from db_schema import db, Users, Incomes, Debts, Expenses, dbinit

from barcode import EAN13
from barcode.writer import ImageWriter 

from datetime import datetime


app = Flask(__name__)
app.secret_key="secret"
app.config['MAIL_SUPPRESS_SEND'] = False 
# make the mail handler
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


#db = SQLAlchemy(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///debts.sqlite'

app.config['SQL_TRACK_MODIFICATIONS'] = True

db.init_app(app)
# with app.app_context():
#     dbinit()


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))





resetdb = False # won't reset the database every time it is closed
if resetdb:
    with app.app_context():
        # drop everything, create all the tables, then put some data into the tables
        db.drop_all()
        db.create_all()
        dbinit()


# for creating tables by visiting a page
@app.route('/resetdb')
def resetdb():
    db.drop_all()
    dbinit()
    return redirect('/')


#route to the log-in page as the default
@app.route('/')
def index():
  return redirect('/log-in')
    


#sends an email 
def sendemail(recipients, subject, body):
    sender = f"{os.getlogin()}@dcs.warwick.ac.uk"
    mail.send_message(sender=("NOREPLY",sender),subject=subject,body=body,recipients=recipients)
    #return make_response(f"<html><body><p>Sending your message to {recipients}</p></body></html>",200)
'''
#an event is added. Only the super user can add an event. They set the Event attributes as those from the form (validated via the HTML)
#The event is emailed to the super user as confirmation
@app.route('/add-event', methods=['GET', 'POST'])
@login_required
def add_event():
  if request.method == 'POST':
    if current_user.is_super:
      event_name = request.form['event_name']
      event_info = request.form['event_info']
      date_time = request.form['date_time']
      duration = int(request.form['duration'])
      max_capacity = int(request.form['max_capacity'])
      location = request.form['location']
      cancellable = bool(request.form['cancellable'])
      if not event_name or not event_info or not date_time or not duration or not max_capacity or not location or not cancellable:
        return redirect(request.url)
      date, time = date_time.split('T')
      event = Events(event_name, event_info, date, time, duration, max_capacity, location, cancellable)
      db.session.add(event)
      db.session.commit()
      log = Logs(user_id=current_user.id, action=f"Added event: {event.event_name} ({event.id})")
      db.session.add(log)
      db.session.commit()
      #either use datetime inflask or use javascript to store the date and time
      sendemail(recipients=[current_user.email], subject=f"You Created {event.event_name}", body=f'Hello {current_user.fname}, \nHere is the up to date information on your newly created event: \n - Event Name: {event.event_name} \n Event Info: {event.event_info} \n - Maximum capacity: {event.max_capacity} \n - Duration: {event.duration} \n - Time: {event.time} \n - Date: {event.date} \n - Location: {event.location} \n - Cancellable: {event.cancellable} \nFrom The EventByte Team')
      return redirect('/all-events')
    return redirect('/home')
  return render_template('add-event.html')

#Renders a template with all the events
@app.route('/all-events', methods=['GET'])
def all_events():
  events = Events.query.all()
  return render_template('all-events.html', events=events)

#Returns the user has booked, and the events they have previously booked and then cancelled.
@app.route('/my-events', methods=['GET'])
@login_required
def my_events():
  tickets = Tickets.query.filter_by(user_id=current_user.id).all()
  booked_events = []
  cancelled_events = []
  for ticket in tickets:
    event = Events.query.filter_by(id=ticket.event_id).first()
    if ticket.cancelled:
      cancelled_events.append(event)
    else:
      booked_events.append(event)
  return render_template('my-events.html', booked_events=booked_events, cancelled_events=cancelled_events)


#They can book an event.
#If remaining capacity is 0, it can't be booked. If remaining capacity is below 5%, it shows the remaining spaces.
#If they booked, they can view their ticket or cancel the booking (if the event is cancellable).
@app.route('/view-event', methods=['GET'])
def view_event():
  eventId = int(request.args.get('eventId'))
  event = Events.query.filter_by(id=eventId).first()
  print(event.current_capacity)
  remaining_capacity = event.max_capacity - event.current_capacity
  full = False
  limit = False
  if remaining_capacity == 0:
    full = True
  elif (remaining_capacity / event.max_capacity) * 100 <= 5:
    limit = True
  if current_user.is_authenticated:
    tickets = Tickets.query.filter_by(user_id=current_user.id, event_id=eventId, cancelled=False).first()
    if tickets is None:
      booked = False
    else:
      booked = True
  else:
    booked = False
  return render_template("view-event.html", 
    event_name = event.event_name,
    eventId=eventId,
    event_info = event.event_info,
    date = event.date,
    time = event.time,
    duration = event.duration,
    max_capacity = event.max_capacity,
    location = event.location,
    cancellable = event.cancellable,
    remaining_capacity = remaining_capacity,
    limit = limit,
    full = full,
    booked = booked)


#TODO
#get a qr code up
#Returns all the relevant information for the ticket, with the QR code
@app.route('/view-ticket')
@login_required
def view_ticket():
  event_id = int(request.args.get('event_id'))
  user_id = current_user.id
  event = Events.query.filter_by(id=event_id).first()
  user = Users.query.filter_by(id=user_id).first()
  ticket = Tickets.query.filter_by(event_id=event_id, user_id=user_id).first()
  ticket_id = str(ticket.id)
  while(len(ticket_id) < 12):
    ticket_id = "0" + ticket_id 
  barcode_filename = barcode_file_path(ticket_id) + ".svg"
  return render_template( 'view-ticket.html',
    event_name = event.event_name,
    fname = user.fname,
    lname = user.lname,
    date = event.date,
    start_time = event.time,
    duration = event.duration,
    location = event.location,
    ticket_code = ticket.id,
    barcode_filename=barcode_filename
    #ticket_code = user_id * event_id + ticket.id
  )














    



#The user can book an event. A ticket will be created for them, or if they had previously cancelled the event, their old ticket will become available again.
# A confirmation email will be sent to the user.
#If bookings are near capacity, the superuser is notified via email.
@app.route('/book-event')
@login_required
def book_event():
  event_id = request.args.get('event_id')
  prev_ticket = Tickets.query.filter_by(event_id=event_id, user_id=current_user.id).first()
  if prev_ticket:
    prev_ticket.cancelled=False
  else:
    new_ticket = Tickets(user_id=current_user.id, event_id=event_id)
    db.session.add(new_ticket)
    db.session.commit()
    #id = new_ticket.id #nonetype
    id = Tickets.query.filter_by(user_id=current_user.id, event_id=event_id).first().id
    ticket_id = str(id)
    while(len(ticket_id) < 12):
      ticket_id = "0" + ticket_id 
    make_barcode(ticket_id)
  event = Events.query.filter_by(id=event_id).first()
  new_capacity = event.current_capacity + 1
  event.current_capacity = new_capacity
  log = Logs(user_id=current_user.id, action=f"Booked event: {event.event_name} ({event.id})")
  db.session.add(log)
  db.session.commit()
  sendemail(recipients=[current_user.email], subject=f"You Signed Up for {event.event_name}", body=f'Hello {current_user.fname}, \nHere is the up to date information on your newly booked event: \n - Event Name: {event.event_name} \n Event Info: {event.event_info} \n - Maximum capacity: {event.max_capacity} \n - Duration: {event.duration} \n - Time: {event.time} \n - Date: {event.date} \n - Location: {event.location} \n - Cancellable: {event.cancellable} \nFrom The EventByte Team')
  if event.max_capacity == event.current_capacity:
    sendemail(recipients=[Users.query.filter_by(is_super=True).first().email], subject=f"{event.event_name} is Fully Booked", body=f'Hello, \nYou\'re event, {event.event_name} has been fully booked! \nFrom The EventByte Team' )
  elif ((event.max_capacity - new_capacity) / event.max_capacity) * 100 < 5:
    sendemail(recipients=[Users.query.filter_by(is_super=True).first().email], subject=f"{event.event_name} is Reaching Capacity", body=f'Hello, \nYou\'re event, {event.event_name} is reaching capacity and currently has {event.max_capacity - event.current_capacity} spaces remaining. \nFrom The EventByte Team' )
  return redirect(f'/view-event?eventId={event_id}')


#The ticket is not deleted from the database sine the user should be able to see their cancelled bookings so the cancelled attribute is set to True.
#The event current capacity is decremented.
#A confirmation email is sent.
@app.route('/cancel-booking')
@login_required
def cancel_booking():
  event_id = request.args.get('event_id')
  user_id = current_user.id
  event = Events.query.filter_by(id=event_id).first()
  if event.cancellable:
    ticket = Tickets.query.filter_by(event_id=event_id, user_id=user_id).first()
    ticket.cancelled = True
    new_capacity = event.current_capacity - 1
    event.current_capacity = new_capacity
    log = Logs(user_id=current_user.id, action=f"Cancelled booking: {event.event_name} ({event.id})")
    db.session.add(log)
    db.session.commit()
    sendemail(recipients=[current_user.email], subject=f"Cancelled Booking for {event.event_name}", body=f'Hello {current_user.fname}, \nYou have cancelled you\'re booking for the {event.event_name} event.  \nFrom The EventByte Team')
  return redirect(f'/view-event?eventId={event_id}')



#The super user can remove the event from the database and all the associated tickets
#The superuser and event attendees are informed via email.
@app.route('/cancel-event')
@login_required
def cancel_event():
  if current_user.is_super:
    event_id = request.args.get('event_id')
    event = Events.query.filter_by(id=event_id).first()
    tickets = Tickets.query.filter_by(event_id=event_id).all()
    db.session.delete(event)
    users = []
    for ticket in tickets:
      if not ticket.cancelled:
        users.append(Users.query.filter_by(id=ticket.user_id).first().email)
      db.session.delete(ticket)
    log = Logs(user_id=current_user.id, action=f"Cancelled event: {event.event_name} ({event.id})")
    sendemail(recipients=users, subject=f"Event Cancellation", body=f"The {event.event_name} has been cancelled.\nFrom the EventByte team.")
    sendemail(recipients=[current_user.email], subject=f"Event Cancellation", body=f"The {event.event_name} has been cancelled.\nFrom the EventByte team.")
    db.session.add(log)
    db.session.commit()
  return redirect('/home')


# Edit Limitations: Can't edit date or time, can only increase or decrese capacity while not filled
# Check if there actually were any changes in the form, which must be filled due to HTML validation.
# Changes are saved.
# Email the attendees and the super user about the changes.
@app.route('/edit-event', methods=['GET', 'POST'])
@login_required
def editevent():
  event_id = request.args.get('event_id')
  event = Events.query.filter_by(id=event_id).first()
  if request.method=='POST':
    if current_user.is_super:
      max_capacity = int(request.form['max_capacity'])
      if (max_capacity >= event.current_capacity):
        event_name = request.form['event_name']
        event_info = request.form['event_info']
        duration = int(request.form['duration'])
        location = request.form['location']
        cancellable = bool(request.form['cancellable'])
        if not (event.max_capacity == max_capacity and event.event_name == event_name and event.event_info == event_info and event.duration == duration and event.location == location and event.cancellable == cancellable):
          event.max_capacity = max_capacity
          event.event_name = event_name
          event.event_info = event_info
          event.duration = duration
          event.location = location
          event.cancellable = cancellable
          log = Logs(user_id=current_user.id, action=f"Edit to event: {event.event_name} ({event.id})")
          db.session.add(log)
          db.session.commit()
          #email user and superuser
          tickets = Tickets.query.filter_by(event_id=event_id).all()
          recipients = []
          for ticket in tickets:
            if not ticket.cancelled:
              user = Users.query.filter_by(id = ticket.user_id).first()
              recipients.append(user.email)

          sendemail(recipients=[current_user.email], subject=f"Your Changes To {event.event_name}", body=f'Hello {current_user.fname}, \nYou have made changes to the {event.event_name} event. \nHere is the up to date information on this event: \n - Event Name: {event.event_name} \n Event Info: {event.event_info} \n - Maximum capacity: {event.max_capacity} \n - Duration: {event.duration} \n - Location: {event.location} \n - Cancellable: {event.cancellable} \nFrom The EventByte Team')
          sendemail(recipients=recipients, subject=f"Changes To {event.event_name}", body=f'Hello, \nChanges have been made to the {event.event_name} event. \nHere is the up to date information on this event: \n - Event Name: {event.event_name} \n Event Info: {event.event_info} \n - Maximum capacity: {event.max_capacity} \n - Duration: {event.duration} \n - Location: {event.location} \n - Cancellable: {event.cancellable} \nFrom The EventByte Team')
        return redirect('/home') 
      return redirect('/home')
    return redirect('/home')
  return render_template('edit-event.html',
    event_name = event.event_name,
    event_id=event_id, 
    event_info = event.event_info,
    # date = event.date,
    # start_time = event.time,
    # date_time = event.date_time,
    duration = event.duration,
    max_capacity=event.max_capacity,
    location = event.location,
    cancellable=event.cancellable
  )'''

# show some of their events and some of the events they haven't booked
# There is a button to see more events
@app.route('/home')
@login_required
def home():
  '''events = Events.query.all()
  count = 0
  booked_events = []
  new_events = []
  if current_user.is_authenticated and not current_user.is_super:
    countb = 0
    for event in events:
      ticket = Tickets.query.filter_by(event_id=event.id, user_id=current_user.id, cancelled=False).all()
      if ticket and countb < 5:
        booked_events.append(event)
        countb += 1
      elif count < 5:
        count += 1
        new_events.append(event)
      if count + countb == 8:
        break
  else:
    for event in events:
      if count == 4:
        break
      else:
        new_events.append(event)
        count += 1
  return render_template("home.html", new_events=new_events, booked_events=booked_events)'''
  return render_template("debt-dashboard.html")



s = Serializer(app.config['SECRET_KEY'], expires_in=1800)

# The email of the forgotten password is sent a link with a token if the email is in the database.
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_request():
  if request.method == 'POST':
    email=request.form['email']
    user = Users.query.filter_by(email=email).first()
    if user:
      token = s.dumps({'user_id': user.id}).decode('utf-8')
      print(token)
      sendemail(recipients=[email], subject="Eventbyte Password Reset", body=f"To reset your password, access the following link: {url_for('reset_password', token=token, _external=True)}. \nYou have half an hour.\nIf you did not request a password reset, ignore this message.\nFrom the EventByte team")
      return redirect('/log-in') #does this
  return render_template('reset-request.html')

# The link with the token loads the user id.
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
  try:
    user_id = str(s.loads(token)['user_id'])
  except:
    return redirect('/all-events') 
  return render_template('reset-password.html', user_id=user_id)

# The new password is saved to the correct user id.
@app.route('/reset-password/save-reset', methods=['GET', 'POST'])
def save_password_reset():
  user_id = int(request.form['user_id'])
  user = Users.query.filter_by(id=int(user_id)).first()
  if user is None:
    return redirect('/home')
  prev = user.password_hash
  user.password_hash = security.generate_password_hash(request.form['password']) 
  db.session.commit()
  new = user.password_hash
  return redirect('/log-in')



# Check if the username is already there, same with email.
# If they already exist, redirect to log-in.
# If they do not, the details are saved, and an email is sent.
@app.route('/register', methods=["GET", "POST"])
def register():
  #if current_user.is_authenticated:
    #return redirect('/home')

  if request.method=="GET":
    return render_template("register.html")

  if request.method=="POST":
    username = request.form['username']
    email = request.form['email']
    fname = request.form['fname']
    lname = request.form['lname']
    hashed_password = security.generate_password_hash(request.form['password'], method='pbkdf2:sha256', salt_length=16)

    tryusername = Users.query.filter_by(username=username).first()
    tryemail = Users.query.filter_by(username=email).first()

    if tryusername is None and tryemail is None:
      new_user = Users(username=username, email=email, fname=fname, lname=lname, password_hash=hashed_password)
      db.session.add(new_user)
      db.session.commit()
      login_user(new_user)
      sendemail(recipients=[email], subject="Welcome to Bollox United!", body=f'Hello {fname}, \nWe\'re so happy you\'ve joined the EventByte family!\nStart exploring new events today to find your next adventure.\nFrom The Bollox Team')
      return redirect('/home')
    return render_template("log-in.html")

# The user can log in via email or username so they are both checked.
@app.route('/log-in', methods=["GET", "POST"])
def login():
  #if current_user.is_authenticated:
    #return redirect('/home')

  if request.method == "POST":
    name = request.form['name']
    password = request.form['password']
    userbyname = Users.query.filter_by(username=name).first()
    userbymail = Users.query.filter_by(email=name).first()
    if (userbyname is None) and (userbymail is None):
      return render_template('log-in.html', failedlogin=True)
    if userbyname:
      if not security.check_password_hash(userbyname.password_hash, password):
        return render_template('log-in.html', failedlogin=True)
      login_user(userbyname)
    if userbymail:
      if not security.check_password_hash(userbymail.password_hash, password):
        return render_template('log-in.html', failedlogin=True)
      login_user(userbymail)

    return redirect('/home')

  if request.method=="GET":
    return render_template('log-in.html', failedlogin=False)


#logs out the user
@app.route('/log-out')
@login_required
def logout():
    #log = Logs(user_id=current_user.id, action=f"Logged Out")
    #db.session.add(log)
    #db.session.commit()
    logout_user()
    return redirect('/home')


'''#update logs in all other functions
#they are shown here
@app.route('/show-logs')
@login_required
def showlogs():
  if current_user.is_super:
    logs = Logs.query.all()
    return render_template('show-logs.html', logs=logs)
  return render_template('/home')'''

@app.route('/debt-dashboard')
@login_required
def dept_dash():
  debts = Debts.query.filter_by(username=current_user.username).all()
  expense = Expenses.query.filter_by(username = current_user.username).first()
  income = Incomes.query.filter_by(username = current_user.username).first()
  return render_template('debt-dashboard.html', debts=debts, expense=expense, income=income)



#TODO: 
#forall, adds algorithm to run to find duedate

#adds the debt as a debt in the Debts db

@app.route('/add-debt', methods=['GET', 'POST'])
@login_required
def add_debt():
  if request.method == 'POST':
    type = request.form['type']
    amount = float(request.form['amount'])
    interest = float(request.form['interest'])
    min_monthly_pay = float(request.form['minimum-monthly-payment'])
    chosen_due_date = request.form['chosen-due-date']
    start_date = request.form['start-date']
    due_date=request.form['due-date']
    debt = Debts(id=current_user.id, name=type, amount=amount, minPayment=min_monthly_pay, interest=interest, dueDate=due_date, chosenDueDate=chosen_due_date, startDate=start_date)#max_capacity, location, cancellable) #TODO: properly populate
    db.session.add(debt)
    db.session.commit()
    return redirect('/debt-dashboard')
  return render_template('add-debt.html')


#adds the expense to the user account
@app.route('/add-expenses', methods=['GET', 'POST'])
@login_required
def add_expenses():
  if request.method == 'POST':
    old = Expenses.query.filter_by(username = current_user.username).first()
    db.session.delete(old)
    amount = float(request.form['amount'])
    debt = Expenses(current_user.id, name, amount, eclass) #TODO: properly populate
    db.session.add(debt)
    db.session.commit()
    db.session.commit()
    return redirect('/debt-dashboard')
  return render_template('add-expenses.html')

#adds the expense to the user account
@app.route('/add-income', methods=['GET', 'POST'])
@login_required
def add_income():
  if request.method == 'POST':
    old = Incomes.query.filter_by(username = current_user.username).first()
    db.session.delete(old) 
    amount = float(request.form['income'])
    debt = Incomes(current_user.id, name, amount, iclass, ranges) #TODO: properly populate
    db.session.add(debt)
    db.session.commit()
    db.session.commit()
    return redirect('/debt-dashboard')
  return render_template('add-income.html')



@app.route('/test', methods=['GET', 'POST'])
def create_user_with_debts():
    # Create a new user
    '''user = Users(username='user1', 
                 password_hash='chachachachachachacha', 
                 fname='bleh', 
                 lname='bleeeeh', 
                 email='user1@example.com')

    # Add the user to the session
    db.session.add(user)'''

    # Add debt_budget to user
    record = Users.query.filter_by(username='user1').first()
    record.debt_budget = 50000
    db.session.commit()

    '''# Create different debts for the user
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
        db.session.add(debt)'''

    # Commit the session to save the user and debts in the database
    #db.session.commit()
    return "bleh :)"


@app.route('/timeline', methods=['GET', 'POST'])
@login_required
def findToPayOff():
  debts = Debts.query.filter_by(username="user1").order_by(Debts.accruedAnnualInterest.asc())
  # Fetch  current user's budget directly from the User table
  monthly_budget = Users.query.filter_by(username="user1").first().debt_budget
  noMonthsNeeded=calculate_months_to_pay_off(debts, monthly_budget)
  return str(noMonthsNeeded)





  """
    Calculates the number of months required to pay off all debts --> without changing values in the database.

    Parameters:
    - debts: all user debts
    - monthly_budget (float): The amount available to pay off debts each month.

    Returns:
    - int: The number of months required to pay off all debts.
     """
def calculate_months_to_pay_off(debts, monthly_budget):

    months = 0
    # Retrieve debts from the database and make an in-memory copy of their balances and interest rates
    
    debt_data = [
        {
            #'id': debt.id,
            'balance': debt.amount,
            'interest': debt.interest,
            'effective_interest': debt.amount * debt.interest/100
        }
        for debt in debts
    ]

    # Loop until all debts are paid off
    while any(debt['balance'] > 0 for debt in debt_data):
        # Sort debts by the highest effective interest first
        debt_data.sort(key=lambda x: x['effective_interest'], reverse=True)

        # Start with the monthly budget for this month
        budget = monthly_budget

        # Pay off debts in order of highest effective interest
        for debt in debt_data:
            if debt['balance'] <= budget:
                # Fully pay off this debt
                budget -= debt['balance']
                debt['balance'] = 0
            else:
                # Partially pay this debt
                debt['balance'] -= budget
                budget = 0  # Budget exhausted
                break  # Exit loop if no budget is left
        # Apply interest to remaining debts for the next month
        '''for i in range (0,len(debt_data)):
           print()
           debt_data[i]['balance'] *= (1 + debt_data[i]['interest']/100)
           debt_data[i]['effective_interest'] = debt_data[i]['balance'] * debt_data[i]['interest']/100'''

        for debt in debt_data:
            debt['balance'] *= (1 + debt['interest']/100)
            debt['effective_interest'] = debt['balance'] * debt['interest']/100
        
        # Increment the month counter
        months += 1
        

    return months
