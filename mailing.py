import os
import boto3
from botocore.exceptions import ClientError
session = boto3.Session(
    aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
    region_name=os.environ['AWS_REGION']
)


def send_email(sender, recipient, subject, body):
    # Replace 'your-region' with your AWS region
    ses_client = session.client('ses', region_name=os.environ['AWS_REGION'])
    email_message = {
        'Subject': {'Data': subject},
        'Body': {'Html': {'Data': body}},
    }
    try:
        response = ses_client.send_email(
            Source=sender,
            Destination={'ToAddresses': [recipient]},
            Message=email_message
        )
        print('response: ', response)
    except ClientError as e:
        print("Error sending email:", e.response['Error']['Message'])


def template_create(user):
    return send_email(os.environ['AWS_MAIL_SENDER'], user.email, 'Verification de compte',
                      f"""
     <h2>Bonjour {user.name},</h2><br>
    <p>Votre compte a été créée,voici le code de verification de votre compte: <b>{user.token}</b> </p>
    Cordialement,<br> 
"""
                      )
