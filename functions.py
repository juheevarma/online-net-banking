# To be imported
import re
import smtplib
from datetime import datetime
from flask import redirect, url_for, session
from functools import wraps
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText 


# Validate mobile number 
def validate_mobile(mobile):
    regex_mobile = '^[6-9]\\d{9}'
    res = re.search(regex_mobile, mobile)
    return True if res else False

# Validate Email ID 
def validate_email(email):
    regex_email = '^[a-zA-Z0-9._]+@[a-zA-Z]+\\.[a-zA-Z]{2,}'
    res = re.search(regex_email, email)
    return True if res else False


# Validate user password : 8-10 characters with one capital letter, one number and one
# special character
def validate_password(password):
    regex_password = '^(?=.*[A-Za-z])(?=.*\\d)(?=.*[@$!%*#?&])[A-Za-z\\d@$!%*#?&]{8,10}'
    res = re.search(regex_password, password)
    return True if res else False


# Ensure a user is logged in before accessing any profile
def login_required(f):
    @wraps(f)
    def allow_only_valid(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return allow_only_valid


# Sending a mail to a user
def sendmail(subject, msg_body, to_adr, from_email=''):
    if from_email =='':
        from_adr = secrets['FROM_EMAIL']
    login_adr = secrets['LOGIN_EMAIL']
    smtpmsg = MIMEMultipart()
    smtpmsg['From']=from_adr
    smtpmsg['To']=to_adr
    smtpmsg['Subject']= subject
    msgbody = MIMEText(msg_body)
    server = smtplib.SMTP(secrets['EMAIL_HOST'], secrets['EMAIL_PORT'])
    server.starttls()
    server.login(login_adr, secrets['EMAIL_PASSWORD'])
    server.ehlo()
    smtpmsg.attach(msgbody)
    server.send_message(smtpmsg)
    server.quit()


secrets = {
    'FROM_EMAIL': 'juhee.varma@chubb.com',
    'LOGIN_EMAIL': 'juhee.varma@chubb.com',
    'EMAIL_PASSWORD': 'S@ndeepa1',
    'EMAIL_HOST': 'smtp-mail.outlook.com',
    'EMAIL_PORT': 587
}

