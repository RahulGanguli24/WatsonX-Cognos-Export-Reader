import pandas
import locale
import logging
import ibm_boto3
from ibm_botocore.client import Config, ClientError
import io
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s : %(message)s')

def mapper(arg):
    if arg=='The entire province of Alberta':
        return 'Alberta'
    if arg=='A particular city or town':
        return 'Municipality'
    if arg=='A distinct provincial electoral zone':
        return 'Provincial Electoral District'
    if arg=='A particular federal electoral area':
        return 'Federal Electoral District'
    if arg=='A unique region, for instance, Indigenous traditional territory':
        return 'Special Area'
    return "-1"


#-------------------Value Reader Function--------------------
#def value_reader(filename,metric,YR,PRV,OP,CSD,PED,FED,SAREA):
def value_reader(filename,metric,YR,PRV,OP,location_type,location):
    logging.info("Parameters received: filename=%s, metric=%s, YR=%s, PRV=%s, OP=%s, location_type=%s, location=%s", filename, metric, YR, PRV, OP,location_type,location)

    df=pandas.read_csv(get_item_csv('hse-cob-watsonx',filename))
    
    #-------------------Mandatory Filter-------------------#
    df = df[df['Year'] == YR]
    df = df[df['Province'] == PRV]

    #-------------------Optional Filter-------------------#

    if location_type !='Missing':
        if mapper(location_type) == "-1":
            return "invalid option for column name"
        df = df[df[mapper(location_type)] == location]
    
    

    locale.setlocale(locale.LC_ALL, 'en_CA.UTF-8')
    result=locale.currency(df[metric].sum(),grouping=True) if metric=='CAD Currency' else "{:,.2f}".format(df[metric].sum())

    #result="{:,.2f}".format(df[metric].sum())
    return result

#print(value_reader(filename='Data/Cognos/GHG.csv',metric='GHG Emissions (CO2e tonnes)',YR=2022))

#-------------------Contact Reader Function--------------------
def contact_reader(filename, location, ContactType):

    df = pandas.read_csv(get_item_csv('hse-cob-watsonx',filename))
    
    df = df[df['Municipality'] == location]
    
    if ContactType == 'Email':
        result = df['Email'].values
    elif ContactType in ('X (twitter) post','Twitter'):
        result = df['X Handle'].values
    else:
        result = 'none'

    return result[0] if len(result) > 0 else 'Contact detail unavailable for ' + location

#print(contact_reader(filename='Data/Contact Details/Municipality_Contact_Details.csv', location='Yellowhead County', Contacttype='Twitter'))


#-------------------Main Function--------------------                   
#def main(filetype,filename,location='none',column_name='none',YR=0,PRV='none',OP='none',CSD='Yellowhead County',PED='none',FED='none',SAREA='none'):
def main(args):   
    # Fetch Parameter values
    filetype = args.get("filetype", "missing").lower()
    location_type = args.get("location_type", "Missing")
    location = args.get("location", "Missing")
    column_name = args.get("column_name", "Missing")
    YR = args.get("YR", "Missing")
    PRV = args.get("PRV", "Missing").capitalize()
    OP = args.get("OP", "Missing")

    # If Filetype is not provided no need to execute further
    if (filetype == "missing") :
        return {
        "headers": {
            "Content-Type": "application/json",
        },
        "statusCode": 200,
        "body": "Filetype is missing",
        }
    
    # Define File Names
    filename = "Not Defined"
    if(filetype == "contact"):
        filename = "Data/Contact Details/Municipality_Contact_Details.csv"
    if(filetype == "ghg"):
        filename = "Data/Cognos/GHG.csv"
        column_name="GHG Emissions (CO2e tonnes)"
    if(filetype == "liability"):
        filename = "Data/Cognos/Cost Liability.csv"
        column_name= "CAD Currency"
    if(filetype == "air_health"):
        filename = "Data/Cognos/Env Health_Acute aquatic toxicity.csv"
        column_name= "Pollutant Emissions (tonnes)"
  
    
    if filetype=='contact':
        response=contact_reader(filename,location,column_name)
    if filetype in ('ghg','liability','air_health'):
        response=value_reader(filename,column_name,YR,PRV,OP,location_type,location)

    logging.info("Main function execution complete, preparing response")

    jsonBody =  response if len(response)>0 else 'Requested data is not available'

    return json.dumps({
        "headers": {
            "Content-Type": "application/json",
        },
        "statusCode": 200,
        "body": jsonBody,
        } )


def get_cos_client():
    # Constants for IBM COS values
    COS_ENDPOINT = "https://s3.us-east.cloud-object-storage.appdomain.cloud" # Current list avaiable at https://control.cloud-object-storage.cloud.ibm.com/v2/endpoints
    COS_API_KEY_ID = "MMj-A6kBsqzIfOTAs8HUWXrL0h6Miv9EJe0GX41i1zHb" # eg "W00YixxxxxxxxxxMB-odB-2ySfTrFBIQQWanc--P3byk"
    COS_INSTANCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/3e2d7f0ac149488f932eeb418173ca33:7026d0c9-ae1b-4691-a28c-2a93f07efec9::" # eg "crn:v1:bluemix:public:cloud-object-storage:global:a/3bf0d9003xxxxxxxxxx1c3e97696b71c:d6f04d83-6c4f-4a62-a165-696756d63903::"

    # Create client
    cos_client = ibm_boto3.client("s3",
        ibm_api_key_id=COS_API_KEY_ID,
        ibm_service_instance_id=COS_INSTANCE_CRN,
        config=Config(signature_version="oauth"),
        endpoint_url=COS_ENDPOINT
    )
    return cos_client

def get_buckets():
    print("Retrieving list of buckets")
    cos_client = get_cos_client()
    try:
        buckets = cos_client.list_buckets()
        for bucket in buckets["Buckets"]:
            print("Bucket Name: {0}".format(bucket["Name"]))
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to retrieve list buckets: {0}".format(e))

def get_bucket_contents(bucket_name):
    print("Retrieving bucket contents from: {0}".format(bucket_name))
    cos_client = get_cos_client()
    try:
        files = cos_client.list_objects(Bucket=bucket_name)
        for file in files.get("Contents", []):
            print("Item: {0} ({1} bytes).".format(file["Key"], file["Size"]))
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to retrieve bucket contents: {0}".format(e))

def get_item(bucket_name, item_name):
    print("Retrieving item from bucket: {0}, key: {1}".format(bucket_name, item_name))
    cos_client = get_cos_client()
    try:
        file = cos_client.get_object(Bucket=bucket_name, Key=item_name)
        print("File Contents: {0}".format(file["Body"].read()))
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to retrieve file contents: {0}".format(e))

def get_item_csv(bucket_name, item_name):
    print("Retrieving item from bucket: {0}, key: {1}".format(bucket_name, item_name))
    cos_client = get_cos_client()
    try:
        csvFile = cos_client.get_object(Bucket=bucket_name, Key=item_name)
        stream = io.StringIO(csvFile["Body"].read().decode('utf-8'))
        return stream
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to retrieve file contents: {0}".format(e))


#get_item('hse-cob-watsonx','Data/Contact Details/Municipality_Contact_Details.csv')

# print(main({"filetype":"contact","location":"Woodbuffalo","column_name":"Email"}))
#print(main({"filetype":"contact","location":"Yellowhead County","column_name":"Twitter"}))

# print(main({"filetype":"Liability","YR":0,"PRV":"Alberta"}))


# print(main({"filetype":"GHG","YR":2020,"PRV":"alberta"}))
#print(main({"filetype":"GHG","YR":2020,"PRV":"alberta","location_type":"A particular city or town","location":"Yellowhead County"}))
# print(main({"filetype":"GHG","YR":2020,"PRV":"alberta","location_type":"A particular federal electoral area","location":"Yellowhead"}))



