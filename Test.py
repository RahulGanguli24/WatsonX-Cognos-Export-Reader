import pandas
import codecs

def watson():
    df=pandas.read_csv('Data/Cognos/Air Emission_SOx.csv')
    df=df.loc[df['Province'].isin(['Alberta'])]  #Passing the province value
    df=df.loc[df['Operator'].isin(['Imperial Oil Resources Limited'])] #passing the operator value
    df=df.loc[df['Year'].isin([2022])]  #Passing the year value
    df=df.loc[df['Data Source'].isin(['NPRI'])]  #Passing the data source value
    df=df.loc[df['Municipality'].isin(['null'])]  #Passing the municipality value
    #df=df.loc[df['Special Area'].isin(['NPRI'])]  #Passing the special area value
    #df=df.loc[df['Provincial Electoral District'].isin(['NPRI'])]  #Passing the FED value
    #df=df.loc[df['Federal Electoral District'].isin(['NPRI'])]  #Passing the PED value
    df=df.groupby(['Year','Data Source'], as_index=False)['Pollutant Emissions (tonnes)'].sum()
    print(df)
watson()