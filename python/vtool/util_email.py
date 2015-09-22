# Copyright (C) 2014 Louis Vottero louis.vot@gmail.com    All rights reserved.

import smtplib
import email
import os
from email.MIMEText import MIMEText


class Email(object):
    
    def __init__(self, user = None, password = None):
        self.user = user
        self.password = password

        self.list_of_emails = []
        self.server = None
        
        self._setup_message()

    def _setup_server(self):
        self.server = smtplib.SMTP()
        self.server.set_debuglevel(1)
    
    def _setup_message(self):
        self.message = email.MIMEMultipart.MIMEMultipart()
        self.message['From'] = self.user
        self.message['Subject'] = ''
        self.message['To'] = []
        
    def set_subject(self, subject):
        self.message['Subject'] = subject

    def add_message(self, text):
        self.message.attach(MIMEText(text))

    def send(self, list_of_emails):
        joined = email.Utils.COMMASPACE.join(list_of_emails)
        self.message['To'] = joined
        self._setup_server()
        
        
        self.server.sendmail(self.user, list_of_emails, self.message.as_string())
        
        self.server.quit()

class Gmail(Email):
    
    def _setup_server(self):
        super(Gmail, self)._setup_server()
        smtp_host = 'smtp.gmail.com'
        smtp_port = 587
        
        self.server.connect(smtp_host,smtp_port)
        self.server.ehlo()
        self.server.starttls()
        self.server.login(self.user, self.password)
        
        
class BeanfieldEmail(Email):
    
    def __init__(self, user):
        super(BeanfieldEmail, self).__init__(user, '')
                
    def _setup_server(self):
        self.server = smtplib.SMTP('smtp.beanfield.com')
        self.server.set_debuglevel(1)

class LocalHost(Email):
    
    def __init__(self, user):
        super(LocalHost, self).__init__(user, '')
        
    def _setup_server(self):
        self.server = smtplib.SMTP('localhost')
        