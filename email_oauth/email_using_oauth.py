import os
import httplib2
import oauth2client
from oauth2client import client, tools, file
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from apiclient import errors, discovery
import mimetypes
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase

#for type hinting
from typing import Optional

SCOPES = 'https://www.googleapis.com/auth/gmail.send'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'monitoring_system'


class Send_Email():
    def get_credentials(self) -> oauth2client.client.OAuth2Credentials:
        """This function is used to get or make credentials from client_secret.json
    
    Returns
    --------
        `oauth2client.client.OAuth2Credentials`: OAuth credentials
    """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'gmail-python-email-send.json')
        store = oauth2client.file.Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.user_agent = APPLICATION_NAME
            credentials = tools.run_flow(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    def SendMessage(self,
                    to: str,
                    subject: str,
                    msgHtml: str,
                    msgPlain: Optional[str] = None,
                    attachmentFile: Optional[os.PathLike] = None) -> str:
        """This function is used to send an email 
      
            Parameters
            -----------
                - `to` (str): Email id of the recipient
                - `subject` (str): Subject of the E-Mail
                - `msgHtml` (str): HTML Section of the E-Mail
                - `msgPlain` (Optional[str], optional): Normal Text section of the E-Mail. Defaults to None.
                - `attachmentFile` (Optional[os.PathLike], optional): Path of attached file, if any. Defaults to None.
            
            Returns
            --------
                `str`: Message ID
        """
      
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('gmail', 'v1', http=http)
        if attachmentFile:
            message1 = self.createMessageWithAttachment(
                to, subject, msgHtml, msgPlain, attachmentFile)
        else:
            message1 = self.CreateMessageHtml(to, subject, msgHtml, msgPlain)
        result = self.SendMessageInternal(service, "me", message1)
        return result

    def SendMessageInternal(self, service, user_id, message):
        try:
            message = (service.users().messages().send(userId=user_id,
                                                       body=message).execute())
            print('Message Id: %s' % message['id'])
            return message
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
            return "Error"

    def CreateMessageHtml(self, to, subject, msgHtml, msgPlain=None):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        # msg['From'] = sender
        msg['To'] = to
        if msgPlain:
            msg.attach(MIMEText(msgPlain, 'plain'))
        if msgHtml:
            msg.attach(MIMEText(msgHtml, 'html'))
        return {
            'raw': base64.urlsafe_b64encode(msg.as_string().encode()).decode()
        }

    def createMessageWithAttachment(self, to, subject, msgHtml, msgPlain,
                                    attachmentFile):
        """Create a message for an email.

      Args:
        sender: Email address of the sender.
        to: Email address of the receiver.
        subject: The subject of the email message.
        msgHtml: Html message to be sent
        msgPlain: Alternative plain text message for older email clients          
        attachmentFile: The path to the file to be attached.

      Returns:
        An object containing a base64url encoded email object.
      """
        message = MIMEMultipart('mixed')
        message['to'] = to
        # message['from'] = sender
        message['subject'] = subject

        messageA = MIMEMultipart('alternative')
        messageR = MIMEMultipart('related')

        messageR.attach(MIMEText(msgHtml, 'html'))
        messageA.attach(MIMEText(msgPlain, 'plain'))
        messageA.attach(messageR)

        message.attach(messageA)

        print("create_message_with_attachment: file: %s" % attachmentFile)
        content_type, encoding = mimetypes.guess_type(attachmentFile)

        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
        if main_type == 'text':
            fp = open(attachmentFile, 'rb')
            msg = MIMEText(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'image':
            fp = open(attachmentFile, 'rb')
            msg = MIMEImage(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'audio':
            fp = open(attachmentFile, 'rb')
            msg = MIMEAudio(fp.read(), _subtype=sub_type)
            fp.close()
        else:
            fp = open(attachmentFile, 'rb')
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())
            fp.close()
        filename = os.path.basename(attachmentFile)
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        message.attach(msg)

        return {'raw': base64.urlsafe_b64encode(message.as_string())}

    def leave_email(self, *, admin_emails, emp_email, form_data):
        #Name
        if form_data["lastname"]:
            name = form_data["firstname"] + " " + form_data["lastname"]
        else:
            name = form_data["firstname"]

        startdate = form_data["startdate"]
        enddate = form_data["enddate"]

        reason = form_data["reason"]
        leavetype = form_data["leavetype"]
        #half day
        try:
            if form_data["halfday"]:
                halfday = True
        except KeyError:
            halfday = False

        admin_contents = f"""\
    <html>
      <body>
        <h1>Leave Application of <strong>{name}</strong><h1>
        <h3><em>{name}</em> wants to take leave from <strong>{startdate}</strong> till <strong>{enddate}</strong></h3>
        <h3><strong>Half Day:</strong> <em>{halfday}</em></h3>
        <h3><strong>Leave Type:</strong> <em>{leavetype}</em></h3>
        <h3><strong>Reason:</strong> <em>{reason}</em></h3>
        <br>
      </body>
    </html>"""

        # for admin_email in admin_emails:
        #   self.SendMessage(
        #       to=admin_email,
        #       subject=f"Leave Application of {name}",
        #       msgHtml = admin_contents
        #   )

        #* enter your email in to
        self.SendMessage(to="rishabhkalra1501@gmail.com",
                         subject=f"Leave Application of {name}",
                         msgHtml=admin_contents)

        user_contents = f"""\
    <html>
      <body>
        <h1><strong>{name}</strong> application for leave<h1>
        <h3><strong>Start Date:</strong> <em>{startdate}</em> <strong>End Date:</strong> <em>{enddate}</em></h3>
        <h3><strong>Half Day:</strong> <em>{halfday}</em></h3>
        <h3><strong>Leave Type:</strong> <em>{leavetype}</em></h3>
        <h3><strong>Reason:</strong> <em>{reason}</em></h3>
        <br>
        <p>If you feel this happened by mistake or want to provide additional information. Contact the concerned personnel</p>
      </body>
    </html>"""

        self.SendMessage(to=emp_email,
                         subject=f"Reply to {name} Application for Leave",
                         msgHtml=user_contents)

    def new_employee_email(self, *, emp_data):
        name = emp_data["Name"]
        email = emp_data["Email"]
        role = emp_data["Role"]

        contents = f"""\
    <html>
      <body>
        <h1>Welcome to the Organization <em>{name}</em><h1>
      
        <h3>Some details regarding you</h3>
        <ul>
          <li>Name: {name}</li>
          <li>Email: {email}</li>
          <li>Role: {role}</li>
        </ul>  

        <br>
        <p>If you feel this happened by mistake or want to provide additional information.Contact the concerned personnel</p>
      </body>
    </html>"""
        self.SendMessage(to=email,
                         subject=f"Welcome to the organization",
                         msgHtml=contents)


#! EMAIL USING YAGMAIL

# class Send_Email:
#   def __init__(self):
#     load_dotenv()
#     user_name = os.getenv('EMAIL') #email of the gmail account you want to send emails from
#     password = os.getenv('PASSWORD')
#     self.yag = yagmail.SMTP(user_name,password)

#   def leave_email(self,*,admin_emails,emp_email,form_data):
#     #Name
#     if form_data["lastname"]:
#       name = form_data["firstname"] +" "+ form_data["lastname"]
#     else:
#       name = form_data["firstname"]

#     startdate = form_data["startdate"]
#     enddate = form_data["enddate"]

#     reason = form_data["reason"]
#     leavetype = form_data["leavetype"]
#     #half day
#     try:
#       if form_data["halfday"]:
#         halfday = True
#     except KeyError:
#       halfday = False

#     admin_contents = f"""\
#     <html>
#       <body>
#         <h1>Leave Application of <strong>{name}</strong><h1>
#         <h3><em>{name}</em> wants to take leave from <strong>{startdate}</strong> till <strong>{enddate}</strong></h3>
#         <h3><strong>Half Day:</strong> <em>{halfday}</em></h3>
#         <h3><strong>Leave Type:</strong> <em>{leavetype}</em></h3>
#         <h3><strong>Reason:</strong> <em>{reason}</em></h3>
#         <br>
#       </body>
#     </html>"""

#     # for admin_email in admin_emails:
#     #   self.yag.send(
#     #       to=admin_email,
#     #       subject=f"Leave Application of {name}",
#     #       contents = admin_contents
#     #   )

#     self.yag.send(
#         to="rishabhkalra1501@gmail.com",
#         subject=f"Leave Application of {name}",
#         contents = admin_contents
#     )

#     user_contents = f"""\
#     <html>
#       <body>
#         <h1><strong>{name}</strong> application for leave<h1>
#         <h3><strong>Start Date:</strong> <em>{startdate}</em> <strong>End Date:</strong> <em>{enddate}</em></h3>
#         <h3><strong>Half Day:</strong> <em>{halfday}</em></h3>
#         <h3><strong>Leave Type:</strong> <em>{leavetype}</em></h3>
#         <h3><strong>Reason:</strong> <em>{reason}</em></h3>
#         <br>
#         <p>If you feel this happened by mistake or want to provide additional information. Contact the concerned personnel</p>
#       </body>
#     </html>"""
#     self.yag.send(
#         to=emp_email,
#         subject=f"Reply to {name} Application for Leave",
#         contents = user_contents
#     )

#   def new_employee_email(self,*,emp_data):

#     name=emp_data["Name"]
#     email = emp_data["Email"]
#     role=emp_data["Role"]

#     contents = f"""\
#     <html>
#       <body>
#         <h1>Welcome to the Organization <em>{name}</em><h1>

#         <h3>Some details regarding you</h3>
#         <ul>
#           <li>Name: {name}</li>
#           <li>Email: {email}</li>
#           <li>Role: {role}</li>
#         </ul>

#         <br>
#         <p>If you feel this happened by mistake or want to provide additional information.Ignore this Email</p>
#       </body>
#     </html>"""
#     self.yag.send(
#         to=email,
#         subject=f"Welcome to the organization",
#         contents = contents
#     )
