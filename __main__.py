import pandas
import codecs
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
    if arg=='Indigenous Community (e.g. Reserve)':
        return 'Municipality'
    if arg=='Indigenous reserve or Metis settlement':
        return 'Municipality'
    if arg=='Indigenous traditional territory':
        return 'Special Area'
    if arg=='Indigenous special area':
        return 'Special Area'
    return "-1"

def contact_mapper(arg):
    if arg=='The entire province of Alberta':
        return 'Provincial'
    if arg=='A particular city or town':
        return 'Municipal district'
    if arg=='A distinct provincial electoral zone':
        return 'PED'
    if arg=='A particular federal electoral area':
        return 'FED'
    if arg=='A unique region, for instance, Indigenous traditional territory':
        return 'Indigenous'
    if arg=='Indigenous Community (e.g. Reserve)':
        return 'Indigenous'
    if arg=='Indigenous reserve or Metis settlement':
        return 'Indigenous'
    if arg=='Indigenous traditional territory':
        return 'Indigenous'
    return "-1"


#-------------------Value Reader Function--------------------
#def value_reader(filename,metric,YR,PRV,OP,CSD,PED,FED,SAREA):
def value_reader(filename,metric,YR,PRV,OP,location_type,location,multiplicationFactor):
    logging.info("Parameters received: filename=%s, metric=%s, YR=%s, PRV=%s, OP=%s, location_type=%s, location=%s, multiplicationFactor=%s", filename, metric, YR, PRV, OP,location_type,location,multiplicationFactor)
    location_type = location_type.replace("%20"," ")
    if (location_type.find("he entire province") > -1):
        location_type = 'Missing'

    location = location.replace("%20"," ")
    df=pandas.read_csv(get_item_csv('hse-cob-watsonx',filename), sep='\t', encoding = 'utf-16')
    logging.info("File Records: " + str(len(df.index)) )
    #logging.info( df.dtypes )
    #-------------------Mandatory Filter-------------------#
    df = df[df['Year'] == int(YR)]
    logging.info("File Records after Year Filter: " + str(len(df.index)) )
    df = df[df['Province'] == PRV]
    logging.info("Data Frame Records after Province Filter: " + str(len(df.index)) )
    #-------------------Optional Filter-------------------#

    if location_type !='Missing':
        if mapper(location_type) == "-1":
            return "invalid option for column name"
        df = df[df[mapper(location_type)] == location]
    logging.info("Mapper : " + mapper(location_type))
    logging.info("Records post any additional Filter: " + str(len(df.index)) ) 


    #locale.setlocale(locale.LC_ALL, 'en_CA.UTF-8')
    #result=locale.currency(df[metric].sum(),grouping=True) if metric=='CAD Currency' else "{:,.2f}".format(df[metric].sum())
    logging.info("Metric Column: " + metric ) 
    result = df[metric].sum()
    result = result * float(multiplicationFactor) if multiplicationFactor != 0 else result
    result="{:,.2f}".format(result)
    return result

def generateEmailList(df, emailNameColumn, emailAddressColumn):
    df['Email display']=df[emailNameColumn]+' &lt;'+df[emailAddressColumn]+'&gt;'
    email_list = df['Email display'].tolist()
    email_list = '; '.join( str(email) for email in email_list)
    return email_list +';'


def watsonx_Regional_contact_reader(filename, location, locationtype):
    #Read the Hierarchy
    df = pandas.read_excel(get_item_File('hse-cob-watsonx',filename), sheet_name='Geography_Heirarchy_Relation')
    df = df[df['Child CSDNAME'] == location]
    relatedRegions = len(df.index)
    logging.info("Parents/Related IDs for : " + location + ": " + str(relatedRegions) )
    allcontactdf = pandas.read_excel(get_item_File('hse-cob-watsonx',filename), sheet_name='Regional_Email_Contact')
    allcontactdf=allcontactdf[allcontactdf['Email'].notna()]
    relatedcontactdf = allcontactdf[allcontactdf.Region_ID.isin(df.Parent_CSDUID)]
    locationcontactdf = allcontactdf[allcontactdf['Region_Name'] == location]
    dfs = [relatedcontactdf , locationcontactdf]
    dfs = pandas.concat(dfs)
    #print(dfs)
    return dfs

#-------------------Watsonx Contact Module Reader Function--------------------
def watsonx_contact_reader(filename,location, locationtype):

#Read General Contacts
    #df = pandas.read_csv(get_item_File('hse-cob-watsonx','Contact Details/Watsonx_Contact_Module_Data.xlsx'))
    df = pandas.read_excel(get_item_File('hse-cob-watsonx',filename), sheet_name='General_Email_Contact')
    df=df[df['Email address'].notna()]
    
    filterColumn = contact_mapper(locationtype)
    logging.info("Filter Column for : " + locationtype + ": " + filterColumn )

    if filterColumn == '-1':
        return ""

    df = df[df[filterColumn] == 'Yes']

    #Define from where to pick teh email name and address
    emailNameColumn = 'Position'
    emailAddressColumn = 'Email address'
    
    #Get General Email List
    email_list = generateEmailList(df, emailNameColumn, emailAddressColumn)
    logging.info("General Email list generated for  : " + locationtype + " - "+ location+": "  )

    #Generate Regional List
    df = watsonx_Regional_contact_reader(filename,location, locationtype)
    emailNameColumn = 'Contact_Person_Name'
    emailAddressColumn = 'Email'
    email_list = email_list + generateEmailList(df, emailNameColumn, emailAddressColumn)

    return email_list


#-------------------Contact Reader Function--------------------
def contact_reader(filename, location, locationtype, ContactType):

    logging.info("Parameters received: filename=%s, location=%s, locationtype=%s ContactType=%s", filename,location,locationtype, ContactType)

   # if (ContactType == "Email" and location == "Duncan’s First Nation Traditional Territory"):
   #     return "ECCC Minister &lt;ministre-minister@ec.gc.ca&gt;; ECCC Chief of staff &lt;jamie.kippen@ec.gc.ca&gt;; ECCC DM &lt;Christine.Hogan@ec.gc.ca&gt;; ECCC ADM &lt;Paul.Halucha@ec.gc.ca&gt;; NRCan Minister &lt;ministre-minister@nrcan-rncan.gc.ca&gt;; NRCan Chief of staff &lt;kyle.harrietha@nrcan-rncan.gc.ca&gt;; NRCAN DM &lt;Michael.vandergrift@nrcan-rncan.gc.ca&gt;; NRCAN ADM &lt;Jeff.labonte@nrcan-rncan.gc.ca&gt;; AB Environment Minister &lt;epa.minister@gov.ab.ca&gt;; AB Environment Chief of staff &lt;christopher.thresher@gov.ab.ca&gt;; AB Environment DM &lt;Sherri.Wilson@gov.ab.ca&gt;; AB Environment ADM &lt;kasha.piquette@gov.ab.ca&gt;; AB Environment opposition &lt;Sarah.Elmeligi@albertandp.ca &gt;; AB Energy Minister &lt;Brian.Jean@gov.ab.ca&gt;; AB Energy Chief of staff &lt;vitor.marciano@gov.ab.ca&gt;; AB Energy DM &lt;larry.kaumeyer@gov.ab.ca&gt;; AB Energy opposition &lt;Naagwan.Alguneid@albertandp.ca&gt;; AB Municipal affairs minister &lt;Ric.Mciver@gov.ab.ca&gt;; AB Municipal affairs chief of staff &lt;hillary.cleminson@gov.ab.ca&gt;; AB Municipal affairs DM &lt;brandy.cox@gov.ab.ca &gt;; AB Municipal affairs opposition &lt;kyle.kasawski@albertandp.ca&gt;; AB Indigenous relations Minister &lt;Rick.Wilson@gov.ab.ca &gt;; AB Indigenous relations Chief of staff &lt;riley.braun@gov.ab.ca&gt;; AB Indigenous relations DM &lt;Donavon.young@gov.ab.ca&gt;; AB Indigenous relations opposition &lt;brooks.arcandpaul@albertandp.ca&gt;; Provincial news Indigenous &lt;jjubinville@aptn.ca&gt;;"
    
    result=""
    #if locationtype=='The entire province of Alberta' or locationtype=='A particular city or town' or locationtype=='A unique region, for instance, Indigenous traditional territory' or locationtype=='Indigenous Community (e.g. Reserve)':
    result=watsonx_contact_reader(filename,location,locationtype)
    

    return result if len(result) > 0 else 'Contact detail unavailable for ' + location

#print(contact_reader(filename='Data/Contact Details/Municipality_Contact_Details.csv', location='Yellowhead County', Contacttype='Twitter'))


#-------------------Main Function--------------------                   
#def main(filetype,filename,location='none',column_name='none',YR=0,PRV='none',OP='none',CSD='Yellowhead County',PED='none',FED='none',SAREA='none'):
def main(args):   
    # Fetch Parameter values
    filetype = args.get("filetype", "missing").lower()
    location_type = args.get("location_type", "Missing")
    location = args.get("location", "Missing")
    column_name = args.get("column_name", "missing")
    YR = args.get("YR", "Missing")
    #PRV = args.get("PRV", "Missing").capitalize() # Capitalizing doesn't work when deploying to IBM Cloud
    PRV = args.get("PRV", "Missing").capitalize()
    OP = args.get("OP", "Missing")
    multiplicationFactor =  args.get("mf", 0)

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
        filename = "Contact Details/Watsonx_Contact_Module_Data.xlsx"
    # -- GHG
    if(filetype == "ghg"):
        filename = "Data/Cognos/GHG.csv"
        if(column_name=="missing"):
            column_name="GHG Emissions (CO2e tonnes)"
    # -- Liability
    if(filetype == "liability"):
        filename = "Data/Cognos/Cost Liability.csv"
        column_name= "CAD Currency"
    # -- Environmental Health
    if(filetype == "acute_aquatic"):
        filename = "Data/Cognos/Env Health_Acute aquatic toxicity.csv"
        column_name= "Pollutant Emissions (tonnes)"
    if(filetype == "chronic_aquatic"):
        filename = "Data/Cognos/Env Health_Chronic aquatic toxicity.csv"
        column_name= "Pollutant Emissions (tonnes)"
    if(filetype == "terrestrial_ecotoxicity"):
        filename = "Data/Cognos/Env Health_Terrestrial ecotoxicity.csv"
        column_name= "Pollutant Emissions (tonnes)"
    # -- Human Health
    if(filetype == "carcinogenicity"):
        filename = "Data/Cognos/Human Health_Carcinogenicity.csv"
        column_name= "Pollutant Emissions (tonnes)"
    if(filetype == "endocrine"):
        filename = "Data/Cognos/Human Health_Endocrine activity.csv"
        column_name= "Pollutant Emissions (tonnes)"
    if(filetype == "mutagenicity"):
        filename = "Data/Cognos/Human Health_Mutagenicity Genotoxicity.csv"
        column_name= "Pollutant Emissions (tonnes)"
    if(filetype == "reproductive"):
        filename = "Data/Cognos/Human Health_Reproductive toxicity.csv"
        column_name= "Pollutant Emissions (tonnes)"
    if(filetype == "developmental"):
        filename = "Data/Cognos/Human health_Developmental toxicity including developmental neurotoxicity.csv"
        column_name= "Pollutant Emissions (tonnes)"
    # Production and Well count
    if(filetype == "production"):
        filename = "Data/Cognos/Production.csv"
        if(column_name=="missing"):
            column_name="Oil_Volume_BOE"
    if(filetype == "asset"):
        filename = "Data/Cognos/Asset.csv"

    # mines
    if(filetype == "mines"):
        filename = "Data/Cognos/Mines.csv"
        column_name= "Mines_Count"

    #Complaints and Failures
    if(filetype == "failures"):
        filename = "Data/Cognos/Failures.csv"
        if(column_name=="missing"):
            column_name="Releases"
    if(filetype == "complaints"):
        filename = "Data/Cognos/Complaints.csv"
        column_name= "Complaints"

    #Royalties
    if(filetype == "royalty"):
        filename = "Data/Cognos/Royalties.csv"
        column_name= "Royalty"
  
    
    if filetype=='contact':
        response=contact_reader(filename,location,location_type,column_name)
    if filetype != 'contact': #in ('ghg','liability','acute_aquatic','chronic_aquatic','terrestrial_ecotoxicity','carcinogenicity','endocrine','mutagenicity','reproductive','developmental', 'asset', 'production'):
        response=value_reader(filename,column_name,YR,PRV,OP,location_type,location, multiplicationFactor)

    logging.info("Main function execution complete, preparing response")

    return {
        "headers": {
            "Content-Type": "application/json",
        },
        "statusCode": 200,
        "body":  json.dumps(response), # if len(response)>0 else 'Requested data is not available' ,
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
        stream = io.StringIO(csvFile["Body"].read().decode('utf-16'))
        return stream
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to retrieve file contents: {0}".format(e))

def get_item_File(bucket_name, item_name):
    print("Retrieving item from bucket: {0}, key: {1}".format(bucket_name, item_name))
    cos_client = get_cos_client()
    try:
        File = cos_client.get_object(Bucket=bucket_name, Key=item_name)
        stream = io.BytesIO(File["Body"].read())
        return stream
    except ClientError as be:
        print("CLIENT ERROR: {0}\n".format(be))
    except Exception as e:
        print("Unable to retrieve file contents: {0}".format(e))


#get_item('hse-cob-watsonx','Data/Contact Details/Municipality_Contact_Details.csv')

#print(main({"filetype":"contact","location_type":"A particular city or town","location":"Drumheller","column_name":"Email"}))
#print(main({"filetype":"contact","location":"The entire province of Alberta","column_name":"Email"}))
#print(main({"filetype":"contact","location_type":"Indigenous reserve or Metis settlement", "location":"Piikani 147","column_name":"Email"}))
#print(main({"filetype":"contact","location_type":"A distinct provincial electoral zone", "location":"West Yellowhead","column_name":"Email"}))
#https://cloud-object-reader-watsonx.1j6t9u3ndy9d.ca-tor.codeengine.appdomain.cloud/?filetype=contact&location=Yellowhead County&column_name=Twitter
# print(main({"filetype":"Liability","YR":0,"PRV":"Alberta"}))


# print(main({"filetype":"GHG","YR":2020,"PRV":"alberta"}))
#print(main({"filetype":"mines","YR":2021,"PRV":"Alberta","location_type":"The%20entire%20province%20of%20Alberta","location":"Yellowhead%20County", "mf":"4.27"}))
#print(main({"filetype":"Production","column_name":"Gas_Volume_BOE","YR":2022,"PRV":"Alberta","location_type":"Indigenous%20special%20area","location":"Duncan%E2%80%99s%20First%20Nation%20Traditional%20Territory"}))
#print(main({"filetype":"mines","YR":2021,"PRV":"Alberta","location_type":"Indigenous traditional territory", "location":"Duncan’s First Nation Traditional Territory"}))
#print(main({"filetype":"Liability","YR":0,"PRV":"Alberta"}))
#print(main({"filetype":"Liability","YR":0,"PRV":"alberta","location_type":"A particular city or town","location":"Yellowhead County"}))
#https://cloud-object-reader-watsonx.1j6t9u3ndy9d.ca-tor.codeengine.appdomain.cloud/?filetype=Liability&YR=0&location_type=A particular city or town&location=Yellowhead County&PRV=Alberta
# print(main({"filetype":"GHG","YR":2020,"PRV":"alberta","location_type":"A particular federal electoral area","location":"Yellowhead"}))
#https://cloud-object-reader-watsonx.1j6t9u3ndy9d.ca-tor.codeengine.appdomain.cloud/?filetype=Liability&YR=0&PRV=Alberta&location_type=The%20entire%20province%20of%20Alberta
