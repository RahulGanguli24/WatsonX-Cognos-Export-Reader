import pandas
import ibm_boto3
from ibm_botocore.client import Config, ClientError
import io

#-------------------Value Reader Function--------------------
def value_reader(filename,metric,YR,PRV='Alberta',OP='none',CSD='none',PED='none',FED='none',SAREA='none'):

    df=pandas.read_csv(get_item_csv('hse-cob-watsonx',filename))

    #-------------------Mandatory Filter-------------------#
    df = df[df.Province == PRV]
    df = df[df.Year == YR]

    #-------------------Optional Filter-------------------#
    if OP =='none':                                             #---Operator
        df = df[df.Operator == df.Operator] 
    else:
        df = df[df.Operator == OP]
    if CSD =='none':                                             #---CSD
        df = df[df['Municipality'] == df['Municipality']]  
    else:
        df = df[df['Municipality'] == CSD]
    if PED =='none':                                             #---PED
        df = df[df['Provincial Electoral District'] == df['Provincial Electoral District']]  
    else:
        df = df[df['Provincial Electoral District'] == PED]
    if FED =='none':                                             #---FED
        df = df[df['Federal Electoral District'] == df['Federal Electoral District']]  
    else:
        df = df[df['Federal Electoral District'] == FED]
    if SAREA =='none':                                             #---Spcial Area
        df = df[df['Special Area'] == df['Special Area']]  
    else:
        df = df[df['Special Area'] == SAREA]

    df="{:,}".format(round(float(df[metric].sum()),2))
    #print(df)

    return 'CA$' + df if metric=='CAD Currency' else df #if len(df) > 0 else 'value unavailable'

#print(value_reader(filename='Data/Cognos/GHG.csv',metric='GHG Emissions (CO2e tonnes)',YR=2022))

#-------------------Contact Reader Function--------------------
def contact_reader(filename, location, ContactType):

    df = pandas.read_csv(get_item_csv('hse-cob-watsonx',filename))
    
    df = df[df['Municipality'] == location]
    
    if ContactType == 'Email':
        df = df['Email'].values
    elif ContactType == 'Twitter':
        df = df['X Handle'].values
    else:
        df = 'none'

    return df[0] #if len(df) > 0 else 'Contact detail unavailable'

#print(contact_reader(filename='Data/Contact Details/Municipality_Contact_Details.csv', location='Yellowhead County', Contacttype='Twitter'))


#-------------------Main Function--------------------                   
#def main(filetype,filename,location='none',column_name='none',YR=0,PRV='none',OP='none',CSD='Yellowhead County',PED='none',FED='none',SAREA='none'):
def main(args):   
    # Fetch Parameter values
    filetype = args.get("filetype", "Missing")
    location = args.get("location", "Missing")
    column_name = args.get("column_name", "Missing")

    # If Filetype is not provided no need to execute further
    if (filetype == "Missing") :
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
    if(filetype == "GHG"):
        filename = "Data/Cognos/GHG.csv"

   
    
    if filetype=='contact':
        response=contact_reader(filename,location,column_name)
    if filetype=='value':
        response=value_reader(filename,column_name,YR,PRV,OP,CSD,PED,FED,SAREA)

    return {
        "headers": {
            "Content-Type": "application/json",
        },
        "statusCode": 200,
        "body": response if len(response)>0 else 'Requested data is not available',
        }


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

#print(main('contact','Data/Contact Details/Municipality_Contact_Details.csv','Yellowhead County','Twitter'))
#print(main(filetype='value',filename='Data/Cognos/GHG.csv',column_name='GHG Emissions (CO2e tonnes)',YR=2022,PRV='Alberta',CSD='Yellowhead County'))
#print(main({"filetype":"contact","location":"Woodlands County","column_name":"Email"}))
#print(main({"filetype":"contact"}))

#get_buckets()
