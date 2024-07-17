import pandas
import codecs
import argparse

def file_reader(YR,PRV='Alberta',OP='none',CSD='none',PED='none',FED='none',SAREA='none'):
    df=pandas.read_csv('Data/Cognos/GHG.csv')
    #-------------------OMandatory Filter-------------------O#
    df = df[df.Province == PRV]
    df = df[df.Year == YR]
    #-------------------Optional Filter-------------------O#
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
    df=df.groupby(['Year'], as_index=False)['GHG Emissions (CO2e tonnes)'].sum()
    #print(df)
    return {
        "headers": {
            "Content-Type": "application/json",
        },
        "statusCode": 200,
        "body": df,
        }
#print(file_reader(2022))


def contact_reader(filename,location,emailorX_column_name):
    return "contant_email"
    
def value_reader(filename,metric_column_name,YR,PRV='Alberta',OP='none',CSD='none',PED='none',FED='none',SAREA='none'):
    return "CA$1,000.00"

def main(filetype,location='none',column_name='none',YR=0,PRV='none',OP='none',CSD='none',PED='none',FED='none',SAREA='none'):
    response='empty '+ filetype
    
    if filetype=='municipal contact':
        response=contact_reader('Data/Contact Details/Municipality_Contact_Details.csv',location)
    if filetype=='GHG':
        response=value_reader('Data/Cognos/GHG.csv',column_name,YR)
    
    return {
        "headers": {
            "Content-Type": "application/json",
        },
        "statusCode": 200,
        "body": response,
        }

print(main('GHG'))

