# To be imported
import logging
import urllib
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from decimal import Decimal
from flask_sqlalchemy import SQLAlchemy
from functions import *
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, Integer, String, ForeignKey, Float, DateTime

# Create the flask instance
app = Flask(__name__)


# Assign a secret key
app.secret_key = 'JuHeEVaRmA'


# Connect to mssql database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc:///?odbc_connect={}'.format(urllib.parse.quote_plus('DRIVER={ODBC Driver 17 for SQL Server};SERVER=APINP-ELPT30975;DATABASE=net_banking;UID=sa;PWD=tap2024'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy()


# Initialize the database once
db.init_app(app)


# Create a logger 
logging.basicConfig(filename='login.log', level=logging.DEBUG, format='%(asctime)s %(name)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)


# Customer Model
class User(db.Model):
    __tablename__ = 'customers_accounts'
    user_id = db.Column(db.String(10),primary_key=True)
    user_name = db.Column(db.String(20),nullable=False)   
    user_email = db.Column(db.String(50),nullable=False, unique=True)
    user_mobile = db.Column(db.String(10), nullable=False, unique=True)
    user_password = db.Column(db.String(10),nullable=False)
    account_number = db.Column(db.Integer, nullable=False, unique=True)
    account_balance = db.Column(db.Float, nullable=False)
    relationship_manager = db.Column(db.String(20))
    status = db.Column(db.Integer, nullable=False)   

    def __init__(self,user_id, user_name,user_email,user_mobile,user_password,account_number,account_balance,relationship_manager):        
        self.user_id = user_id
        self.user_name = user_name
        self.user_email = user_email
        self.user_mobile = user_mobile
        self.user_password = user_password
        self.account_number = account_number
        self.account_balance = account_balance
        self.relationship_manager = relationship_manager        
  

# Transaction Management Model
class UserTransactions(db.Model):
    __tablename__ = 'customers_transactions'
    transaction_id = db.Column(Integer, primary_key=True)
    user_id = db.Column(String(10), ForeignKey('customers_accounts.user_id'), nullable=False)
    transaction_type = db.Column(String(20), nullable=False)
    amount = db.Column(Float, nullable=False)
    balance = db.Column(Float, nullable=False)
    receiver_account = db.Column(Integer, nullable=False)
    time_stamp = db.Column(DateTime, nullable=False) 

    def __init__(self,transaction_id,user_id,transaction_type,amount,balance,receiver_account,time_stamp):
        self.transaction_id = transaction_id
        self.user_id = user_id   
        self.transaction_type = transaction_type    
        self.amount=amount    
        self.balance = balance 
        self.receiver_account=receiver_account    
        self.time_stamp=time_stamp


# Admin Model 
class Admin(db.Model):
    __tablename__ = 'admins_accounts'
    admin_id = db.Column(db.String(10),primary_key=True)
    admin_name = db.Column(db.String(20),nullable=False) 
    admin_mail = db.Column(db.String(20),nullable=False,unique=True)
    admin_mobile = db.Column(db.String(10),nullable=False,unique=True)
    admin_password = db.Column(db.String(10),nullable=False)  

    def __init__(self, admin_id, admin_name, admin_mail, admin_mobile, admin_password):
        self.admin_id = admin_id
        self.admin_name = admin_name
        self.admin_mail = admin_mail
        self.admin_mobile = admin_mobile
        self.admin_password = admin_password


# Base HTML
@app.route("/")
def base():
    return render_template("base.html")


# User Sign In
@app.route('/signin', methods=['GET', 'POST'])
def login():
    try:
        # Form returns a POST method
        if request.method == 'POST':
            user_id = request.form['user_id']
            password = request.form['password']
            # User ID or Password are blank
            if not user_id or not password:
                flash('Please enter a user ID and password.')
                logger.error(f"Invalid login attempt, User ID or Password not filled'")
                return redirect(url_for('login'))
            
            # Fetch the user with those credentials
            user = User.query.filter_by(user_id=user_id).first()

            # No results are fetched
            if user is None:
                flash('Account does not exist! Please create an account.')
                logger.warning(f"Login attempt for invalid account'")
                return redirect(url_for('register'))
            # User is inactive
            elif user.status==0:
                flash('Inactive Account. Please create a new account.')
                logger.warning(f"Invalid login attempt with user_id='{user_id}'")
                return redirect(url_for('login'))
            # User exists but password is wrong
            elif user.user_password != password:
                flash('Wrong Password. Please try again.')
                logger.warning(f"Invalid login attempt with user_id='{user_id}'")
                return redirect(url_for('register'))
            # User exists and is active 
            else:
                session['user_id'] = user_id
                logger.info(f"User logged in with user_id='{user_id}'")
                return redirect(url_for('profile', user_id=user_id))
        # Form does not return a POST method
        else:
            if 'user_id' in session:
                return redirect(url_for('profile', user_id=session['user_id']))
        return render_template('base.html')
    
    except Exception as e:
        logger.error(f"An error occurred while logging in user_id='{user_id}'. Error message: {str(e)}")
        error_message = "An error occurred while logging in. Please try again later."
        return f"<h1>{error_message}</h1>"


# User Profile
@app.route('/profile/<user_id>')
@login_required
def profile(user_id):
    try:
        # User in session 
        if 'user_id' in session:
            current_user_id = session['user_id']
            if current_user_id == user_id:
                # Fetch user details from database
                user = User.query.filter_by(user_id=user_id).first()

                # No results are fetched
                if user is None:
                    return redirect(url_for('login'))
                # Results are fetched
                else:
                    # Fetch user transactions from database
                    transactions = UserTransactions.query.filter(UserTransactions.user_id.in_([user_id, UserTransactions.receiver_account]))
                    return render_template('new_profile.html', username=user.user_name, current_bank_balance=user.account_balance, relationship_manager=user.relationship_manager, user_transactions=transactions, user_id=user_id)
            # Unauthorized access
            else:
                logger.warning(f"Unauthorized attempt to view profile.")
                return "You are not authorized to access this profile."
        else:
            return redirect(url_for('login'))
        
    except Exception as e:
        logger.error(f"An error occurred while fetching or rendering the user profile for user_id='{user_id}'. Error message: {str(e)}")
        error_message = "An error occurred while fetching or rendering the user profile. Please try again later."
        return f"<h1>{error_message}</h1>"


# User Dashboard
@app.route('/dashboard/<user_id>', methods=['GET', 'POST'])
@login_required
def dashboard(user_id):
    logger = logging.getLogger(__name__)
    try:
        if 'user_id' in session:
            user_id = session['user_id']
            user = User.query.filter_by(user_id=user_id).first()
            # Form returns a POST method
            if request.method == 'POST': 
                # Fetch user details
                updated_email = request.form['email']
                updated_mobile = request.form['mobile']
                            
                # Email is updated
                if updated_email != user.user_email:
                    # Check updated email not in databse
                    is_existing = User.query.filter_by(user_email = updated_email).first()

                    # Email not in databse
                    if not is_existing:
                        # Updated EMail is valid
                        if validate_email(updated_email):
                            user.user_email = updated_email

                            # Add transaction to the session and commit the changes
                            db.session.commit()

                            flash("Successfully updated email!")
                            logger.info(f"User {user.user_id} updated mail to {updated_email}")
                            return redirect(url_for('profile', user_id=user.user_id))
                        else:
                            flash("Invalid Email Format. Please enter valid one.")
                            logger.error(f"User {user.user_id} failed at updating email")
                            return redirect(url_for('dashboard', user_id=user.user_id))
                    else:
                        flash("Invalid Email. User already exists.")
                        logger.error(f"User {user.user_id} entered exsiting email")
                        return redirect(url_for('dashboard', user_id=user.user_id))   

                # Mobile is updated
                if updated_mobile != user.user_mobile:
                    # Check updated email not in databse
                    is_existing = User.query.filter_by(user_mobile = updated_mobile).first()

                    # Email not in databse
                    if not is_existing:
                        # Updated EMail is valid
                        if validate_mobile(updated_mobile):
                            user.user_mobile = updated_mobile

                            # Add transaction to the session and commit the changes
                            db.session.commit()

                            flash("Successfully updated mobile!")
                            logger.info(f"User {user.user_id} updated mobile to {updated_mobile}")
                            return redirect(url_for('profile', user_id=user.user_id))
                        else:
                            flash("Invalid Mobile Format. Please enter valid one.")
                            logger.error(f"User {user.user_id} failed at updating mobile")
                            return redirect(url_for('dashboard', user_id=user.user_id))
                    else:
                        flash("Invalid Mobile. User already exists.")
                        logger.error(f"User {user.user_id} entered exsiting mobile")
                        return redirect(url_for('dashboard', user_id=user.user_id))  
        return render_template('user_update.html',user_id=user.user_id,username=user.user_name, account_num=user.account_number,email=user.user_email,mobile=user.user_mobile) 
    
    except Exception as e:
        logger.error(f"An error occurred while updating user details for user_id='{user_id}'. Error message: {str(e)}")
        error_message = "An error occurred while updating user details. Please try again later."
        return f"<h1>{error_message}</h1>"

# New Account Generation
@app.route('/new_account_generation/<user_id>', methods=['GET','POST'])
def new_account_generation(user_id):
    try:
        # User in session 
        if 'user_id' in session:
            current_user_id = session['user_id']
            if current_user_id == user_id:
                # Fetch user details from database
                user = User.query.filter_by(user_id=user_id).first()

                # No results are fetched
                if user is None:
                    return redirect(url_for('login'))
                # Results are fetched
                else:
                    max_account_number = db.session.query(func.max(User.account_number)).scalar()
                    user.account_number = max_account_number + 1
                    db.session.commit()
                    # Fetch user transactions from database
                    transactions = UserTransactions.query.filter(UserTransactions.user_id.in_([user_id, UserTransactions.receiver_account]))
                    return render_template('new_profile.html', username=user.user_name, current_bank_balance=user.account_balance, relationship_manager=user.relationship_manager, user_transactions=transactions, user_id=user_id)
            # Unauthorized access
            else:
                logger.warning(f"Unauthorized attempt to view profile.")
                return "You are not authorized to access this profile."
        else:
            return redirect(url_for('login'))
        
    except Exception as e:
        logger.error(f"An error occurred while generating a new account for user_id='{user_id}'. Error message: {str(e)}")
        error_message = "An error occurred while generating a new account. Please try again later."
        return f"<h1>{error_message}</h1>"
        
        
# User Registration
@app.route('/register',methods=['GET', 'POST'])
def register():
    try:
        # Form returns a POST method
        if request.method == 'POST':
            # Take user input from form
            new_name = request.form['name']
            new_email = request.form['email']
            new_mobile = request.form['number']
            new_password = request.form['password']

            # Check if user is already existing
            is_existing=User.query.filter_by(user_email=new_email).first()
            print(new_email, new_mobile, new_password, new_name)

            if is_existing:
                flash('Account existing. Please Sign in!')
                logger.info(f'Registration unsuccessful! user_id={is_existing.user_id} already existing')
                return redirect(url_for('login'))
            else:
                # Check if password, email and mobile are valid 
                if validate_password(new_password) and validate_email(new_email) and validate_mobile(new_mobile):
                    
                    # Generate new User ID value
                    count = User.query.count() + 1
                    # Assign new User ID
                    new_id = f'U{count:03}'
                    # Generate new Account Number
                    new_account_num = User.query.order_by(User.account_number.desc()).first().account_number + 1
                    
                    # Create a new user object
                    new_user = User(
                        user_id=new_id,
                        user_name=new_name,
                        user_email=new_email,
                        user_mobile=new_mobile,
                        user_password=new_password,
                        account_number=new_account_num,
                        account_balance=0.00,
                        relationship_manager=None
                    )
                    
                    # Add user to the session and commit the changes
                    db.session.add(new_user)
                    db.session.commit()

                    logger.info(f'Registration successful: user_id={new_id}, user_name={new_name}, user_email={new_email}')
                    flash('User registration successful! Sign in')

                    # Subject, E-Mail body and Receiver's E-Mail address
                    subject= 'User ID, Verification for Gio & Banks'
                    msg_body=f'Welcome, {new_name}! Please find your Gio & Banks Net Banking User ID: { new_id }. Sign in to your account now! Thank you for choosing Gio & Banks. Cheers!'
                    to_addr = new_email 
                    # Send the mail
                    sendmail(subject, msg_body, to_addr)

                    return redirect(url_for('login'))
                else:
                    # Password or Email or Mobile have invalid patterns
                    if not validate_password(new_password):
                        flash('Password must contain at 8 to 10 characters, including one uppercase, one special character and one number.')
                        logger.error(f'Registration unsuccessful! Password format incorrect')
                    elif not validate_email(new_email):
                        flash('Please check email format.')
                        logger.info(f'Registration unsuccessful! Email format incorrect')
                    elif not validate_mobile(new_mobile):
                        flash('Please enter a valid mobile number')
                        logger.error(f'Registration unsuccessful! Mobile format incorrect')
                    db.session.rollback()
                    return redirect(url_for('register'))
        else:
            return render_template('base.html')
    except Exception as e:
        logger.error(f"Error: {e}")
        flash('Error occurred! Please try again later.')
        return redirect(url_for('register'))
    
    
# Transfer To Another Account
@app.route('/transfer/<user_id>', methods=['GET', 'POST'])
@login_required
def another_account(user_id):
    logger = logging.getLogger(__name__)
    try:
        # Form returns a POST method
        if request.method == 'POST':
            # User in session already
            if 'user_id' in session:
                user_id = session['user_id'] 
                # Fetch user details
                user = User.query.filter_by(user_id=user_id).first()
                receiver_num = request.form['receiver_num']
                amount = request.form['amount']
                password = request.form['password']

                # Check if any of the required keys are missing
                if not receiver_num:
                    flash("Receiver's Account Number is required! Please try again.")
                    logger.error(f"User with user_id='{user.user_id}' did not enter receiver A/C number")
                    return redirect(url_for('profile', user_id=user.user_id))
                if not amount:
                    flash("Amount is required! Please try again.")
                    logger.error(f"User with user_id='{user.user_id}' did not enter transfer amount")
                    return redirect(url_for('profile', user_id=user.user_id))
                if not password:
                    flash("Password is required! Please try again.")
                    logger.warning(f"User with user_id='{user.user_id}' entered wrong password")
                    return redirect(url_for('profile', user_id=user.user_id))
                
                if receiver_num and amount and password:
                    user = User.query.filter_by(user_id=user.user_id).first()
                    if user.user_password != password:
                        flash("Incorrect password! Please try again.")
                        logger.warning(f"User with user_id='{user.user_id}' entered wrong password during transfer")
                        return redirect(url_for('profile', user_id=user.user_id))
                    else:
                        # Fetch receiver details
                        receiver = User.query.filter_by(account_number=receiver_num).first()
                        if not receiver:
                            flash("Invalid account number! Please try again.")
                            logger.error(f"User with user_id='{user.user_id}' entered invalid A/C number")
                            return redirect(url_for('profile', user_id=user.user_id))
                        else:
                            # Amount sent is more than Account Balance
                            if Decimal(amount) >= user.account_balance:
                                flash("Could not process payment! Insufficient balance")
                                logger.warning(f"User with user_id='{user.user_id}' entered invalid amount")
                                return redirect(url_for('profile', user_id=user.user_id))
                            # Amount exceeds limit of 50000
                            elif Decimal(amount) > 50000.00:
                                flash("Could not process payment! Amount exceeds daily limit")
                                logger.warning(f"User with user_id='{user.user_id}' attempted transferring amount exceeding daily limit.")
                                return redirect(url_for('profile', user_id=user.user_id))
                            else:
                                # Deduct user account balance
                                user.account_balance -= float(amount)
                                # Set transaction ID
                                count = UserTransactions.query.count() + 1
                                new_transaction = count+1
                                # Set current date
                                dt = datetime.now()
                                
                                # Create User Transaction Object
                                user_transaction = UserTransactions(
                                    transaction_id=new_transaction,
                                    user_id=user.user_id,
                                    transaction_type='TR',
                                    amount=float(amount),
                                    balance=float(user.account_balance),
                                    receiver_account=receiver.account_number,
                                    time_stamp=dt)
                                
                                # Add transaction to the session and commit the changes
                                db.session.add(user_transaction)
                                db.session.commit()

                                # Subject, E-Mail body and Receiver's E-Mail address
                                subject= 'Gio & Banks: Amount transferred'
                                msg_body=f'Dear {user.user_name}, Rs. {amount} transferred to A/C No. {receiver.account_number} on {dt}. Transaction id no. {new_transaction}. Thank you for choosing Gio & Banks. Cheers!'
                                to_addr = user.user_email 
                                # Send the mail
                                sendmail(subject, msg_body, to_addr)


                                flash("Successful Transfer!")
                                logger.info(f"User {user.user_id} transferred {amount} to account {receiver_num}")
                                return redirect(url_for('profile', user_id=user.user_id))
            else:
                return redirect(url_for('login'))
        else:
            return render_template('base.html')
        
    except Exception as e:
        logger.error(f"An error occurred while transferring to the account'. Error message: {str(e)}")
        error_message = "An error occurred while transferring to the account. Please try again later."
        return f"<h1>{error_message}</h1>"

# Deposit Amount To Self
@app.route('/deposit/<user_id>', methods=['GET', 'POST'])
@login_required
def deposit_amount(user_id):
    logger = logging.getLogger(__name__)

    try:
        # Form returns a POST method
        if request.method == 'POST':
            # User in session already
            if 'user_id' in session:
                user_id = session['user_id'] 
                # Fetch user details
                user = User.query.filter_by(user_id=user_id).first()
                amount = request.form['amount']
                password = request.form['password']

                # Check if any of the required keys are missing
                if not amount:
                    flash("Amount is required! Please try again.")
                    logger.error(f"User with user_id='{user.user_id}' did not enter transfer amount")
                    return redirect(url_for('profile', user_id=user.user_id))
                if not password:
                    flash("Password is required! Please try again.")
                    logger.warning(f"User with user_id='{user.user_id}' did not enter password")
                    return redirect(url_for('profile', user_id=user.user_id))
                
                if amount and password:
                    user = User.query.filter_by(user_id=user.user_id).first()
                    if user.user_password != password:
                        flash("Incorrect password! Please try again.")
                        logger.warning(f"User with user_id='{user.user_id}' entered wrong password")
                        return redirect(url_for('profile', user_id=user.user_id))
                    else:
                        # Amount exceeds limit of 50000
                        if float(amount) > 50000.00:
                            flash("Amount exceeds bank limit! Please enter valid amount.")
                            logger.warning(f"User with user_id='{user.user_id}' tried depositing amount more than 50000")
                        else:
                            # Increase user account balance
                            user.account_balance += float(amount)
                            # Set transaction ID
                            count = UserTransactions.query.count() + 1
                            new_transaction = count+1
                            # Set current date
                            dt = datetime.now()

                            # Create User Transaction Object
                            user_transaction = UserTransactions(
                                transaction_id=new_transaction,
                                user_id=user.user_id,
                                transaction_type='DE-SELF',
                                amount=float(amount),
                                balance=float(user.account_balance),
                                receiver_account=user.account_number,
                                time_stamp=dt)
                            
                            # Add transaction to the session and commit the changes
                            db.session.add(user_transaction)
                            db.session.commit()

                            # Subject, E-Mail body and Receiver's E-Mail address
                            subject= 'Gio & Banks: Amount Deposited'
                            msg_body=f'Dear {user.user_name}, Rs. {amount} deposited to your account, A/C No. {user.account_number} on {dt}. Transaction id no. {new_transaction}. Thank you for choosing Gio & Banks. Cheers!'
                            to_addr = user.user_email 
                            # Send the mail
                            sendmail(subject, msg_body, to_addr)

                            flash("Successful Deposit!")
                            logger.info(f"User {user.user_id} deposited {amount}")
                            return redirect(url_for('profile', user_id=user.user_id))
            else:
                return redirect(url_for('login'))
        else:
            return render_template('base.html')
    
    except Exception as e:
        logger.error(f"An error occurred while depositing to the account'. Error message: {str(e)}")
        error_message = "An error occurred while depositing to the account. Please try again later."
        return f"<h1>{error_message}</h1>"


# Withdraw Amount From Account
@app.route('/withdraw/<user_id>', methods=['GET', 'POST'])
@login_required
def withdraw_amount(user_id):
    logger = logging.getLogger(__name__)

    try:    
        # Form returns a POST method
        if request.method == 'POST':
            # User in session already
            if 'user_id' in session:
                user_id = session['user_id'] 
                # Fetch user details
                user = User.query.filter_by(user_id=user_id).first()
                amount = request.form['amount']
                password = request.form['password']
                
                # Check if any of the required keys are missing
                if not amount:
                    flash("Amount is required! Please try again.")
                    logger.error(f"User with user_id='{user.user_id}' did not enter transfer amount")
                    return redirect(url_for('profile', user_id=user.user_id))
                if not password:
                    flash("Password is required! Please try again.")
                    logger.error(f"User with user_id='{user.user_id}' did not enter password")
                    return redirect(url_for('profile', user_id=user.user_id))
                
                if amount and password:
                    user = User.query.filter_by(user_id=user.user_id).first()
                    # Passwords not matched
                    if user.user_password != password:
                        flash("Incorrect password! Please try again.")
                        logger.warning(f"User with user_id='{user.user_id}' entered wrong password")
                        return redirect(url_for('profile', user_id=user.user_id))
                    else:
                        # Amount exceeds bank limit
                        if float(amount) > 50000.00:
                            flash("Amount exceeds bank limit! Please enter valid amount.")
                            logger.warning(f"User with user_id='{user.user_id}' tried withdrawing amount more than 50000")
                            return redirect(url_for('profile', user_id=user.user_id))
                        # Amount withdrawn makes bank balance less than 5000
                        elif user.account_balance - float(amount) <= 5000.00:
                            flash("Amount exceeds minimum bank balance requirement! Please enter valid amount.")
                            logger.warning(f"User with user_id='{user.user_id}' tried withdrawing amount exceeding minimum account balance requirement")
                            return redirect(url_for('profile', user_id=user.user_id))
                        else:
                            # Decrease user bank balance
                            user.account_balance -= float(amount)
                            # Set transaction ID
                            count = UserTransactions.query.count() + 1
                            new_transaction = count+1
                            # Set current date
                            dt = datetime.now()

                            # Create User Transactions Object
                            user_transaction = UserTransactions(
                                transaction_id=new_transaction,
                                user_id=user.user_id,
                                transaction_type='WI',
                                amount=float(amount),
                                balance=float(user.account_balance),
                                receiver_account=user.account_number,
                                time_stamp=dt)
                            
                            # Add transaction to the session and commit the changes
                            db.session.add(user_transaction)
                            db.session.commit()

                            # Subject, E-Mail body and Receiver's E-Mail address
                            subject= 'Gio & Banks: Amount Withdrawl'
                            msg_body=f'Dear {user.user_name}, Rs. {amount} withdrawn from your account, A/C No. {user.account_number} on {dt}. Transaction id no. {new_transaction}. Thank you for choosing Gio & Banks. Cheers!'
                            to_addr = user.user_email 
                            # Send the mail
                            sendmail(subject, msg_body, to_addr)

                            flash("Successful Withdrawl!")
                            logger.info(f"User {user.user_id} withdrew {amount}")
                            return redirect(url_for('profile', user_id=user.user_id))
        else:
            return render_template('base.html')
    
    except Exception as e:
        logger.error(f"An error occurred while withdrawing from the account'. Error message: {str(e)}")
        error_message = "An error occurred while withdrawing from the account. Please try again later."
        return f"<h1>{error_message}</h1>"
    

# Admin Signin
@app.route('/adminsignin', methods=['GET', 'POST'])
def admin_signin():
    logger = logging.getLogger(__name__)
    
    try:
        # Form returns a POST method
        if request.method == 'POST':
            user_id = request.form['admin_id']
            password = request.form['password']
            session["userId"] = user_id
            if not user_id or not password:
                flash('Please enter a user ID and password.')
                logger.error(f"Admin details not entered'")
                return redirect(url_for('admin_signin'))
            
            # Fetch Admin Details    
            user = Admin.query.filter_by(admin_id=user_id, admin_password=password).first()
            # Admin not found
            if user is None:
                flash('Invalid Credentials. Please try again.')
                logger.warning(f"Invalid admin login attempt with admin_id='{user_id}'")
            else:
                session['user_id'] = user_id
                logger.info(f"Admin logged in with admin_id='{user_id}'")
                return redirect(url_for('admin_profile', user_id=user_id))
        else:
            return render_template('admin.html')
        return render_template('admin.html')
    
    except Exception as e:
        logger.error(f"An error occurred while signing admin into the account'. Error message: {str(e)}")
        error_message = "An error occurred while signing admin into the account. Please try again later."
        return f"<h1>{error_message}</h1>"


# Admin Profile
@app.route('/adminprofile/<user_id>')
@login_required
def admin_profile(user_id):
    logger = logging.getLogger(__name__)
    try:
        # User already in session
        if 'user_id' in session:
            current_user_id = session['user_id']
            # Fetch user details
            if current_user_id == user_id:
                user = Admin.query.filter_by(admin_id=user_id).first()
                # User not found
                if user is None:
                    logger.warning(f"Invalid admin profile attempt")
                    return redirect(url_for('admin_signin'))
                else:
                    # Fetch transactions table
                    transactions = UserTransactions.query.all()
                    logger.info(f"Admin with admin_id ={user.admin_id} signed in")
                    return render_template('admin_profile.html', username=user.admin_name, user_transactions=transactions)
            else:
                logger.warning(f"Invalid admin profile attempt")
                return "You are not authorized to access this profile."
        else:
            return redirect(url_for('admin_signin'))
    
    except Exception as e:
        logger.error(f"An error occurred while viewing admin profile'. Error message: {str(e)}")
        error_message = "An error occurred while viewing admin profile. Please try again later."
        return f"<h1>{error_message}</h1>"    


# Allow Admin to search for a customer
@app.route('/search_customer')
@login_required
def search_customer():
    q = request.args.get('query')
    try:
        cust = User.query.filter_by(user_id=q).all()
        logger.info(f"Customer fetched into admin profile!")
        user = Admin.query.filter_by(admin_id = session["userId"]).first()
        userName = user.admin_name
        transactions = UserTransactions.query.all()
        return render_template('admin_profile.html', customer=cust, username = userName, user_transactions=transactions)
    
    except Exception as e:
        logger.warning(f"admin tried fetching non existent profile")
        return render_template('admin_profile.html', customer=None)
    

# Allow admin to delete a customer    
@app.route('/delete_user', methods=['POST'])
@login_required
def delete_user():
    user_id = request.form['user_id']
    try:
        user = User.query.filter_by(user_id=user_id).first()
        user.status=0
        userRec = Admin.query.filter_by(admin_id = session["userId"]).first()
        userName = userRec.admin_name
        transactions = UserTransactions.query.all()
        logger.info(f"Admin deleted user id={user_id}")
        db.session.commit()

    except Exception as e:
        logger.info(f"Admin could not delete user with user id={user_id}")
        return f"<h1>{e}</h1>"
    return render_template('admin_profile.html', username = userName, user_transactions = transactions)


# Allow admin to update the manager
@app.route("/update_manager", methods=['POST', 'GET'])
@login_required
def update_manager():
    try:
        dropdown_value = request.form['dropdown']
        user_id = request.form['user_id']
        user = User.query.filter_by(user_id=user_id).first()
        user.relationship_manager = dropdown_value
        userRec = Admin.query.filter_by(admin_id=session["userId"]).first()
        userName = userRec.admin_name
        transactions = UserTransactions.query.all()
        db.session.commit()
        logger.info(f"Admin updated manager of user id={user_id} to {user.relationship_manager}")
        return render_template('admin_profile.html', username=userName, user_transactions=transactions)

    except Exception as e:
        logger.error(f"An error occurred while updating the user's relationship manager. Error message: {str(e)}")
        error_message = "An error occurred while updating the user's relationship manager. Please try again later."
        return f"<h1>{error_message}</h1>"


# Logout of the session
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


if __name__ == "__main__":
    # db.create_all()
    app.run(debug=True)