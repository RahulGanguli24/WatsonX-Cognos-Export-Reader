import pandas
import codecs

def watson(a1,a2=None):
    df=pandas.read_csv('Data/Cognos/GHG.csv')
    df=df[df.Province==a1]  #Passing the province value
    #df=df[df.Operator=='Imperial Oil Resources Limited'] #passing the operator value
    df=df[df.Year==a2]  #Passing the year value
    #df=df[df['Data Source']==a3]  #Passing the data source value
    #df=df[df['Data Source']=='Greenhouse Gas Reporting Program (GHGRP)']  #Passing the data source value
    #df=df.loc[df['Municipality'].isin(['null'])]  #Passing the municipality value
    #df=df.loc[df['Special Area'].isin(['NPRI'])]  #Passing the special area value
    #df=df.loc[df['Provincial Electoral District'].isin(['NPRI'])]  #Passing the FED value
    #df=df.loc[df['Federal Electoral District'].isin(['NPRI'])]  #Passing the PED value
    df=df.groupby(['Year','Data Source'], as_index=False)['GHG Emissions (CO2e tonnes)'].sum()
    print(df)
watson('Alberta')