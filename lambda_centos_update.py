#!/usr/bin/python
import json
import boto3
import email.message
from pprint import pprint
from datetime import datetime
from datetime import date
from datetime import time

def showAMI(imagesList):
    htmlList = "<h3>AMI CentOS available in AWS Marketplace (most recent on TOP)<ul>"
    sortedList = sorted(imagesList, key = lambda i: i['CreationDate'],reverse=True) 
    for varg in sortedList:
        cdate = varg['CreationDate']
        imgId = varg['ImageId']
        formDate = cdate[:10] + " " + cdate[11:19]
        formDate = datetime.strptime(formDate, '%Y-%m-%d %H:%M:%S')
        htmlList += "<li>" + imgId + " - Creation date: " + str(formDate) + "</li>"
    htmlList += "</ul>"    
    return htmlList

def processEc2(ec2Input, htmlTableRem):
    htmlTable = ""
    for varg in ec2Input:
        instances = varg['Instances']
        for warg in instances:
            htmlTable += "<tr>"
            imgId = warg['ImageId']
            insId = warg['InstanceId']
            insIp = ""
            insLt = warg['LaunchTime']
            insNa = ""
            state = warg['State']
            tags  = warg['Tags']
            u = state['Name']
            if (u == 'running'):
                insIp = warg['PrivateIpAddress']
            else:
                insIp = u
            for xarg in tags:
                t = xarg['Key']
                if (t == 'Name'):
                    insNa = xarg['Value']
            htmlTable += "<td>" + insNa + "</td>"
            htmlTable += "<td>" + insId + "</td>"
            htmlTable += "<td>" + imgId + "</td>"
            htmlTable += "<td>" + insIp + "</td>"
            htmlTable += "<td>" + str(insLt) + "</td>"
            htmlTable += "</tr>"
            print("Instance ID: " + insId + " - AMI ID: " + imgId + "\t- IP: " + insIp + "\t-> Name: " + insNa)
    return htmlTable

def lambda_handler(event, context): 
    print("...Current execution time: " + str(datetime.utcnow()))
    print("boto3 requested...")
    EC2 = boto3.client('ec2', region_name='eu-west-1')
    print("boto3 instantiated...")
    response = EC2.describe_images(
        Owners=['679593333241'], # CentOS
        Filters=[
          {'Name': 'name', 'Values': ['CentOS Linux 7 x86_64 HVM EBS *']},
          {'Name': 'architecture', 'Values': ['x86_64']},
          {'Name': 'root-device-type', 'Values': ['ebs']},
        ],
    )
    print("boto3 describe images successfully called...")
    
    imagesList = sorted(response['Images'],
                  key=lambda x: x['CreationDate'],
                  reverse=True)
    currentDate = imagesList[0]['CreationDate'][:10] + " " + imagesList[0]['CreationDate'][11:19]
    currentDate = datetime.strptime(currentDate, '%Y-%m-%d %H:%M:%S')
    latestAMI = imagesList[0]
    OldAmis = ""
    print("...Going through all available images from Marketplace...")
    for varg in imagesList:
        cdate = varg['CreationDate']
        imgId = varg['ImageId']
        formDate = cdate[:10] + " " + cdate[11:19]
        formDate = datetime.strptime(formDate, '%Y-%m-%d %H:%M:%S')
        print(str(formDate) + " " + imgId)
        if (datetime.date(formDate)>datetime.date(currentDate)):
            latestAMI = varg
            currentDate = formDate
    
    print("\n-----------------------------------------------\nLatest CentOS AMI description below:\n-----------------------------------------------")
    print("Name of AMI - " + latestAMI['Name'])
    print("Date of AMI - " + latestAMI['CreationDate'])
    print("Info of AMI - " + latestAMI['Description'])
    print("  ID of AMI - " + latestAMI['ImageId'])
    #print("OutdatedAMI - " + OldAmis[:-1])
    print("\n------------------------------------")
    print("---------READY FOR DISCOVERY--------")
    print("------------------------------------")
    
    response = EC2.describe_instances(
        Filters=[
          {'Name': 'image-id', 'Values': [latestAMI['ImageId']]},
          {'Name': 'architecture', 'Values': ['x86_64']},
          {'Name': 'root-device-type', 'Values': ['ebs']},
        ],
    )
    # Ec2OkList = sorted(response['Reservations'],
                  # key=lambda x: x[1]['LaunchTime'],
                  # reverse=True)
    Ec2OkList = response['Reservations']
    
    print("--------------------------")
    print("   UP TO DATE IDs/AMIs    ")
    print("--------------------------")
    testMail = """
        <table style="width:100%;bgcolor:#01AA01">
            <caption>UP TO DATE INSTANCES</caption>
            <tr>
                <th>NAME</th>
                <th>EC2 ID</th>
                <th>AMI ID</th>
                <th>IP</th>
                <th>LAUNCH TIME</th>
            </tr>
        """    
    amisInfo = showAMI(imagesList)
    theTable = testMail
    theTable += processEc2(Ec2OkList, testMail)
    theTable += "</table>"

    print("--------------------------")
    print("    OUTDATED IDs/AMIs     ")
    print("--------------------------")
    testMailKo = """
        <table style="width:100%;bgcolor:#AA0101">
            <caption>OUTDATED INSTANCES</caption>
            <tr>
                <th>NAME</th>
                <th>EC2 ID</th>
                <th>AMI ID</th>
                <th>IP</th>
                <th>LAUNCH TIME</th>
            </tr>
        """
    theOutTable = testMailKo
    for varg in imagesList:
        imgId = varg['ImageId']
        if (imgId != latestAMI['ImageId']):
            print("OLD AMI: " + imgId + " ")
            print("-----------------------")
            OldAmis += "'" + imgId + "',"
            response = EC2.describe_instances(
                Filters=[
                  {'Name': 'image-id', 'Values': [imgId]},
                  {'Name': 'architecture', 'Values': ['x86_64']},
                  {'Name': 'root-device-type', 'Values': ['ebs']},
                ],
            )
            Ec2KoList = response['Reservations']
            theOutTable += processEc2(Ec2KoList, testMailKo)
    testMailKo += "</table>"    
    
    # -----MAIL PART-----        
    theTime = datetime.now()    
    import smtplib
    email_content = """
    <html>
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        
       <title>Tutsplus Email Newsletter</title>
       <style type="text/css">
        a {color: #d80a3e;}
        body, #header h1, #header h2, p {margin: 0; padding: 0;}
        #main {border: 1px solid #cfcece;}
        img {display: block;}
        #top-message p, #bottom p {color: #3f4042; font-size: 12px; font-family: Arial, Helvetica, sans-serif; }
        #header h1 {color: #ffffff !important; font-family: "Lucida Grande", sans-serif; font-size: 24px; margin-bottom: 0!important; padding-bottom: 0; }
        #header p {color: #ffffff !important; font-family: "Lucida Grande", "Lucida Sans", "Lucida Sans Unicode", sans-serif; font-size: 12px;  }
        h5 {margin: 0 0 0.8em 0;}
        h5 {font-size: 18px; color: #444444 !important; font-family: Arial, Helvetica, sans-serif; }
        p {font-size: 12px; color: #444444 !important; font-family: "Lucida Grande", "Lucida Sans", "Lucida Sans Unicode", sans-serif; line-height: 1.5;}
           table, th, td {
            border: 1px solid black;
            border-collapse: collapse;
        }
        th, td {
            padding: 5px;
            text-align: left;
        }
       </style>
    </head>
     
    <body>
    """ + amisInfo + """
    <table width="100%" cellpadding="0" cellspacing="0" bgcolor="e4e4e4"><tr><td>
    <table id="top-message" cellpadding="20" cellspacing="0" width="600" align="center">
        <tr>
          <td align="center">
            <p><h1>CentOS instances check</h1></p>
          </td>
        </tr>
      </table>
     
    <table id="main" width="600" align="center" cellpadding="0" cellspacing="15" bgcolor="ffffff">
        <tr>
          <td>
            <table id="header" cellpadding="10" cellspacing="0" align="center" bgcolor="8fb3e9">
              <tr>
                <td width="570" align="center"  bgcolor="#d80a3e"><h1>NESS ENVIRONMENT DEV/QUA/PROD</h1></td>
              </tr>
              <tr>
                <td width="570" align="right" bgcolor="#d80a3e"><p>""" + str(theTime) + """</p></td>
              </tr>
            </table>
          </td>
        </tr> 
        <tr>            
            <td bgcolor="FF6347">
                """ + theOutTable  + """
            </td>
        </tr>
        <tr>
            <td bgcolor="32CD32">
                """ + theTable  + """
            </td>
        </tr>
      </table>
      <table id="bottom" cellpadding="20" cellspacing="0" width="600" align="center">
        <tr>
          <td align="center">
            <p><a href="mailto:david.****@****.ch?Subject=CentOS%20Notifications">Feedback/suggestions</a> | <a href="https://sts.tamedia.ch/adfs/ls/idpinitiatedsignon.aspx?loginToRp=urn:amazon:webservices">Connect to AWS console</a></p>
          </td>
        </tr>
      </table><!-- top message -->
    </td></tr></table><!-- wrapper -->
     
    </body>
    </html>
     
     
    """
    msg = email.message.Message()
    msg['Subject'] = 'NESS - CentOS notifications' 
    msg['From'] = 'david.****@**.**'
    msg['To'] = 'it.eap.dev****@**.**'
    password = "*********"
    msg.add_header('Content-Type', 'text/html')
    msg.set_payload(email_content)
    
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login("david.****@**.**", password)
    server.sendmail(
      msg['From'], 
      msg['To'], 
      msg.as_string())
    server.quit()
    
    return 0