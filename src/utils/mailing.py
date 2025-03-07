import smtplib, ssl
import os
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders

def get_email_template():
    """Read the HTML email template file and return its content."""
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'web', 'templates', 'email_template.html')
    with open(template_path, 'r') as f:
        return f.read()

def inject_content_to_template(content):
    """Insert email-specific content into the HTML template."""
    template = get_email_template()
    return template.replace('<!-- EMAIL_CONTENT -->', content)

def send_email(receiver_email, sender_email, password, subject, html):
    smtp_server = "smtp.gmail.com"
    port = 465 
    context = ssl.create_default_context()

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email
    
    # Use the template with injected content
    html_content = inject_content_to_template(html)
    html_part = MIMEText(html_content, "html")
    message.attach(html_part)

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            return True
    except Exception as e:
        print(e)
        return False

def send_welcome_mail(info):
    receiver_email = info['receiver_email']
    sender_email = info['sender_email']
    password = info['password']
    subject = info['subject']
    username = info['username']
    user_password = info['user_password']
    website_url = info['website_url']
    name = info['name']

    html = f"""
    <h2>Welcome to Data Manager!</h2>
    <p>Dear {name},</p>
    <p>Your account has been successfully created. You can now access all the features of Data Manager.</p>
    <p>Use the following credentials to log in:</p>
    <table>
        <tr>
            <td><strong>Username:</strong></td>
            <td>{username}</td>
        </tr>
        <tr>
            <td><strong>Password:</strong></td>
            <td>{user_password}</td>
        </tr>
    </table>
    <a href="https://{website_url}" class="btn">Login to Data Manager</a>
    <p><strong>Important:</strong> Please change your password after your first login for security reasons.</p>
    <p>If you have any questions, please don't hesitate to contact us.</p>
    <p>Best regards,<br>The Data Manager Team</p>
    """
    send_email(receiver_email, sender_email, password, subject, html)

def send_report_mail(info):
    receiver_email = info['receiver_email']
    sender_email = info['sender_email']
    password = info['password']
    subject = info['subject']
    txt = info['txt']
    link2entry = info['link2entry']
    sender_username = info['sender_username']
    
    html = f"""
    <h2>Entry Report Notification</h2>
    <p>You have been notified by <strong>{sender_username}</strong> about an entry in the Data Manager.</p>
    <p><a href="https://{link2entry}" class="btn">View Entry</a></p>
    <h3>Report Details:</h3>
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 4px; border-left: 4px solid #3498db;">
        {txt}
    </div>
    """
    return send_email(receiver_email, sender_email, password, subject, html)

def send_password_reset_mail(info):
    receiver_email = info['receiver_email']
    sender_email = info['sender_email']
    password = info['password']
    subject = info['subject']
    txt = info['txt']

    html = f"""
    <h2>Password Reset</h2>
    <p>{txt}</p>
    <p>If you did not request a password reset, please contact the administrator immediately.</p>
    """
    return send_email(receiver_email, sender_email, password, subject, html)

def send_new_order_mail(order_data, mail_args):
    receiver_email = mail_args['receiver_email']
    sender_email = mail_args['sender_email']
    password = mail_args['password']
    subject = mail_args['subject']
    order_name = order_data['order_name']
    link = order_data['link']
    quantity = order_data['quantity']
    note = order_data['note']
    assignee = order_data['order_assignee']
    author = order_data['order_author']
    
    html = f"""
    <h2>New Order Created</h2>
    <p>A new order has been created in the Data Manager system.</p>
    <table>
        <tr>
            <td><strong>Order Name:</strong></td>
            <td>{order_name}</td>
        </tr>
        <tr>
            <td><strong>Quantity:</strong></td>
            <td>{quantity}</td>
        </tr>
        <tr>
            <td><strong>Note:</strong></td>
            <td>{note}</td>
        </tr>
        <tr>
            <td><strong>Assignee:</strong></td>
            <td>{assignee}</td>
        </tr>
        <tr>
            <td><strong>Author:</strong></td>
            <td>{author}</td>
        </tr>
    </table>

    """
    send_email(receiver_email, sender_email, password, subject, html)

def send_order_status_mail(order_data, mail_args):
    sender_email = mail_args['sender_email']
    receiver_email = mail_args['receiver_email']
    password = mail_args['password']
    subject = mail_args['subject']
    order_name = order_data['order_name']
    status = order_data['status']
    author = order_data['order_author']

    status_color = "#28a745" if status.lower() == "ordered" else "#ffc107"
    
    html = f"""
    <h2>Order Status Update</h2>
    <p>The status of an order has been updated in the Data Manager system.</p>
    <table>
        <tr>
            <td><strong>Order Name:</strong></td>
            <td>{order_name}</td>
        </tr>
        <tr>
            <td><strong>New Status:</strong></td>
            <td><span style="color: {status_color}; font-weight: bold;">{status}</span></td>
        </tr>
        <tr>
            <td><strong>Updated by:</strong></td>
            <td>{author}</td>
        </tr>
    </table>
    <p>You can log in to the Data Manager to view more details about this order.</p>
    """
    send_email(receiver_email, sender_email, password, subject, html)   