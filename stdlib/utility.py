import json
import time
import datetime
from xml.etree import ElementTree
import os
import logging
import requests
import sender
import mysql.connector
# from geocodeus import ZipCache
# from stdlib.creds import dbcred,email_cred
import imaplib
import sys
from datetime import date
from datetime import timedelta
# import pgeocode


# cache = ZipCache()
today = datetime.datetime.now()
email_creds=email_cred()

# #Velocity check with cache
# CACHE_FILE = "cache.json"
# if not os.path.isfile(CACHE_FILE):
#     with open('cache.json', 'w') as f:
#         print("The cache file is created")
# MAX_CACHE_AGE = 1800  # Maximum age of cached data in seconds (30 minutes)

def login_into_gmail(imap_user, imap_password):
    try:
        conn = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        (retcode, capabilities) = conn.login(imap_user, imap_password)
        return conn
    except Exception as e:
        logging.info(f'Exception : {e}')
        conn.logout()
        return None

def check_ordertype(ordertype,orderfee,common_db_data,client_data,portal_name):
    try:     
        ordertype=ordertype.strip()
        
        if ',' in ordertype:
            ordertype = ordertype.replace(',  ',' ').replace(', ',' ').replace(',',' ')
            logging.info(f'order type after removing comma is : {ordertype}')
        # ........Logic......
        else:
            return orderfee,ordertype,False
        
                             
    except Exception as ex:
        logging.info(ex)
        exception_mail_send(portal_name,client_data['Client_name'],ex)
        


def criteria_with_params(pricedb,zipcodedb,fee_portal,due_difference, zipcode, client_data,due,common_db_data,portal_name,address):
    try:
        #Logic......
    except Exception as ex:
        exception_mail_send(portal_name,client_data['Client_name'],ex)
        logging.info(ex)

def counter_accepted(client_data,address,portal,zipcode,ordertype,fee_portal):
    try:
        today = date.today()
        date_time = today.strftime('%Y-%m-%d')
        today_date=date_time+' 23:59:00'

        yesterday = today - timedelta(days=1)
        yesdate_time = yesterday.strftime('%Y-%m-%d')
        yesterday_date=yesdate_time+' 00:00:00'

        print(today_date)
        print(yesterday_date)
        logging.info('Connected to MySQL database...')
        
        data=cursorexec("order_updation","SELECT","SELECT * FROM `table_name` WHERE `ClientName` = '{}' and `Address` = '{}' AND AcceptedTime BETWEEN '{}' AND '{}' AND MailStatus = 'Countered'".format(client_data['Client_name'],address,yesterday_date,today_date))

        if data:
            counter_accepted_flag = True
            logging.info(f'Order is already countered {address}')   
            subject=f"Ignored Order!!! - {portal}-{'Already countered order'}"
        else:
            counter_accepted_flag = False
            logging.info(f'Order Is not countered Before {address}')
        return counter_accepted_flag
    except Exception as ex:
        logging.info(f"Exception in check_counter_accepted: {ex}")
        exception_mail_send(portal,client_data['Client_name'],ex)


def check_counter_accepted(client_data,address,portal,due_date):
    try:
        today = date.today()
        date_time = today.strftime('%Y-%m-%d')
        today_date=date_time+' 23:59:00'
        yesterday = today - timedelta(days=1)
        yesdate_time = yesterday.strftime('%Y-%m-%d')
        yesterday_date=yesdate_time+' 00:00:00'

        print(today_date)
        print(yesterday_date)
        logging.info('Connected to MySQL database...')
        
        data=cursorexec("order_updation","SELECT","SELECT * FROM `table_name` WHERE `ClientName` = '{}' and `Address` = '{}' AND AcceptedTime BETWEEN '{}' AND '{}' AND MailStatus = 'Countered'".format(client_data['Client_name'],address,yesterday_date,today_date))
    
        if data:
            counter_accepted_flag = True
            logging.info(f'Countered Order Accepted for Address: {address}')
            # cursorexec("order_updation","UPDATE","UPDATE `mainstreetaccepted` SET `MailStatus` = 'Countered Order Accepted' WHERE `ClientName` = '{}' AND `ProviderName` = '{}' and `Address` = '{}'".format(client_data['Client_name'],portal,address))
            cursorexec("order_updation","UPDATE","UPDATE `table_name` SET `DueDate` = '{}', `MailStatus` = 'Countered Order Accepted' WHERE `ClientName` = '{}' AND `ProviderName` = '{}' and `Address` = '{}'".format(due_date,client_data['Client_name'],portal,address))    
        else:
            counter_accepted_flag = False
            logging.info(f'Not a Countered Order for Address: {address}')
        return counter_accepted_flag
    except Exception as ex:
        logging.info(f"Exception in check_counter_accepted: {ex}")
        exception_mail_send(portal,client_data['Client_name'],ex)


def write_to_db(client_data,time_now,duedate,provider_name,order_fee,ordertype,order_address,mail_status,portal,order_id,subjectline,order_received_time):
    """This function writes the accepted order details to table_name database"""
    try:
        logging.info("Updating accepted order details to DB ...")
        order_zipcode = str(order_address).split(" ")[-1]
        if '-' in order_zipcode:order_zipcode = order_zipcode.split("-")[0]
                
            from_mail_id = client_data['from_mail']
            logging.info(f"from mail : {from_mail_id}")
            cursorexec("order_updation","INSERT",f"""INSERT INTO `table_name`(`ClientName`, `AcceptedTime`, `DueDate`, `ProviderName`, `OrderFee`, `Order Type`, `Address`, `to_ecesisMail`, `to_clientMail`, `from_mail`, `fromaddresspwd`, `MailStatus`,`order_id`,`subjectline`,`order_zipcode`,`order_received_time`,`client_type`)
                        VALUES ('{client_data['Client_name']}','{time_now}','{duedate}','{provider_name}','{order_fee}','{ordertype}','{order_address}','{client_data['to_ecesisMail']}','{client_data['to_clientMail']}','{client_data['from_mail']}','{email_creds[from_mail_id]}','{mail_status}','{order_id}','{subjectline}','{order_zipcode}','{order_received_time}','{client_data['client_type']}')""")
        
        else:
            logging.info(f"from mail from client data: {client_data['from_mail']}")
            cursorexec("order_updation","INSERT",f"""INSERT INTO `table_name`(`ClientName`, `AcceptedTime`, `DueDate`, `ProviderName`, `OrderFee`, `Order Type`, `Address`, `to_ecesisMail`, `to_clientMail`, `from_mail`, `fromaddresspwd`, `MailStatus`,`order_id`,`subjectline`,`order_zipcode`,`order_received_time`,`client_type`)
                        VALUES ('{client_data['Client_name']}','{time_now}','{duedate}','{provider_name}','{order_fee}','{ordertype}','{order_address}','{client_data['to_ecesisMail']}','{client_data['to_clientMail']}','{from_mail_id}','{email_creds[from_mail_id]}','{mail_status}','{order_id}','{subjectline}','{order_zipcode}','{order_received_time}','{client_data['client_type']}')""")

    except Exception as ex:
        logging.info('Exception arrises : %s',ex)
        exception_mail_send(portal,client_data['Client_name'],ex)

def get_cursor(db):
    """This function Connects to the database"""
    cred=dbcred()
    cnx = mysql.connector.connect(user=cred['DB_user'], password=cred['DB_password'], host=cred['DB_host'], database=db,
                                  autocommit=True)
    cursor = cnx.cursor(buffered=True, dictionary=True)
    return cnx, cursor

def send_accepted_mail(due_date, order_fee,ordertype,order_address,order_id,fromaddress,to_client_mail,to_ecesis_mail,client_name,subject,portal):
    """This function is to send Order accepted Emails"""
    try:
        mail_status='Order Accepted'
        logging.info('Connected to email')
        
        if fromaddress == ''    :
            logging.info(f"from mail : {fromaddress}")
            mail = sender.Mail('smtp.gmail.com', fromaddress , email_creds[fromaddress], 465, use_ssl=True,fromaddr=fromaddress)
       
        else:
            logging.info(f"from mail : {fromaddress}")
            mail = sender.Mail('smtp.gmail.com', fromaddress , email_creds[fromaddress], 465, use_ssl=True,fromaddr=fromaddress)
            
    
        success_message = successmessage(client_name,str(datetime.datetime.now()), due_date ,portal, order_fee, ordertype,order_address,order_id)
        client_mail_send(mail,to_client_mail,to_ecesis_mail,subject,success_message)
        
    except Exception as ex:
        mail_status='Accepted Mail Failure'
        exception_mail_send(portal,client_name,ex)
        logging.info('Exception arrises while sending mail')
        logging.info('Mail Not Send')
    return mail_status

def successmessage(client_name, acceptedtime, due_date, providename, orderfee, ordertype, address,order_id):
    """This Function returns the order accepted message template"""
    SUCCESS_MESSAGE = f"""This is an automatic notification that one of your orders was auto-accepted using our service:

    Client Name: {client_name}
    Accepted Time: {acceptedtime}
    Due Date: {due_date}
    Provider Name: {providename}
    Order Fee: {orderfee}
    Order Type: {ordertype}
    Address: {address}
    OrderID: {order_id}
    """
    return SUCCESS_MESSAGE



def close_cursor_connection(cursor, cnx):
    """This Fucntion is used to Close SQL Connection"""
    cursor.close()
    cnx.close()


def cursorexec(db,qtype,query):
    """This Fucntion is used to Execute SQL query"""
    cnx, cursor = get_cursor(db)
    cursor.execute(query)
    if "SELECT" in qtype:
        data = cursor.fetchone()
    else:
        data = "DATA INSERTED OR UPDATED SUCCESSFULLY"
    close_cursor_connection(cursor, cnx)
    return data

def logger_portal(client_name,portalname):
    """This Function is used to Setup logging"""
    path=f"BACKUP//{portalname}//{client_name}//" #Check path exist
    if not os.path.exists(path):os.makedirs(path)
    LOG_FILENAME = path + '{}'.format(client_name,) + today.strftime('%d-%m-%Y-%H-%M-%S.log')
    logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s',  # Include timestamp in each log line
        datefmt='%d-%m-%Y %H:%M:%S'  # Format for the timestamp
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)
    logging.getLogger().propagate=False




def exception_mail_send(portal_name,client_name,ex):
    """This Function is used to send Exception  Mails"""
    try:
        mail = sender.Mail('smtp.gmail.com', email_creds['exception_email'] , email_creds['exception_password'], 465, use_ssl=True,fromaddr=email_creds['exception_email'])
        logging.info('Connected to email')
        err_message = """This is an automatic notification:
Exception in {}'s {} account.

Exception in {}
""".format(client_name,portal_name,ex)
        logging.info(err_message)

        mail.send_message(subject=f'{portal_name} Exception!', to=email_creds['exception_email'], body=err_message)
        logging.info('Exception Mail sent')
    except Exception as ec:
        logging.info(ec)
        
def checkIsAccepted(client_data, address, portal):
    try:
        today = date.today()
        date_time = today.strftime('%Y-%m-%d')
        today_date=date_time+' 23:59:00'

        yesterday = today - timedelta(days=1)
        yesdate_time = yesterday.strftime('%Y-%m-%d')
        yesterday_date=yesdate_time+' 00:00:00'

        print(today_date)
        print(yesterday_date)
        logging.info('Connected to MySQL database...')
        
        data=cursorexec("order_updation", )
        logging.info("Accepted order - {}".format(data))
        if data:
            accepted_flag = True
            logging.info('Order Accepted by the client {}'.format(data['ClientName']))
        else:
            accepted_flag = False
            logging.info(f'Not a Accepted Order - Address: {address}')
        return accepted_flag
    except Exception as ex:
        logging.info(f"Exception in checkIsAccepted: {ex}")
        exception_mail_send(portal,client_data['Client_name'],ex)



def send_login_error_mail(portal_name,client_data):
    """This function is to send login error emails"""
    try:
        mail = sender.Mail('smtp.gmail.com', email_creds['login_error_email'] , email_creds['login_error_password'], 465, use_ssl=True,
                                   fromaddr=email_creds['login_error_email'])
        logging.info('Connected to email')
        err_message = f"""This is an automatic notification:
Unable to login to {client_data['Client_name']}'s {portal_name} account"""
        logging.info(err_message)
    
        logging.info('Login Error Mail sent')
    except Exception as ex:
        exception_mail_send(portal_name,client_data['Client_name'],ex)
        logging.info(ex)

  
def successmessageconditionalyaccept3(client_name, acceptedtime, due_date, providename, orderfee, ordertype, address,order_id,requested_due,msg,requested_fee):
    """This Function returns the order conditionally accepted message template"""
    SUCCESS_MESSAGE = f"""This is an automatic notification that one of your orders was {msg} using our service:

    Client Name: {client_name}
    Accepted Time: {acceptedtime}
    Due Date: {due_date}
    Provider Name: {providename}
    Order Fee: {orderfee}
    Order Type: {ordertype}
    Address: {address}
    OrderID: {order_id}
    Requested Due: {requested_due}
    Requested Fee: {requested_fee}
    """
    return SUCCESS_MESSAGE