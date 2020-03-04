import json, time, boto3
from dateutil.parser import parse
import hashlib

def glue_timestamp(datestring):
    # datestring: general time string 
    # returns: time string formated for AWS Glue
    return parse(datestring).strftime('%Y-%m-%d %X')

def lambda_handler(event, context):
    
    BUCKET_NAME = 'ggs-credit-card'
    file_path = '/tmp/data_file.json'
    
    body = str(event['body'])    
    
    data = {}
    data['email']=body
    
    body = body.replace('\r','')
    
    p1,p2 = body.split(';;')[:2]

    # first component is time
    data['time'] = glue_timestamp(p1)

    for line in p2.split('\n'):
        if 'Amount: ' in line:
            data['amount'] = float(line.split('Amount: ')[1].replace('$',''))
        if 'Where: ' in line:
            data['where'] = line.split('Where: ')[1]
        if 'Type: ' in line:
            data['bofa type'] = line.split('Type: ')[1]
        if 'date: ' in line.lower():
            # Bank of America is changing format here
            # may say 'Transaction date: ' or 'Date: '
            data['trans date'] = glue_timestamp(line.lower().split('date: ')[1])
            
    # name of file is hashed body of the email
    # so if the same email is processed twice it will overwrite previous file
    h = hashlib.sha1()
    h.update(data['email'].encode('utf-8'))
    key = h.hexdigest()[:10]
    
    with open(file_path, "w") as write_file:
        json.dump(data, write_file)
    
    s3 = boto3.client('s3')
    try:
        s3_response = s3.upload_file(file_path, BUCKET_NAME,key)
    except Exception as e:
        raise IOError(e)
    return {
        'statusCode': 200,
        'body': {
            'hash': key
        }
    }
