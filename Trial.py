

import pandas

def contact_reader(filename, location, XorEmail):
    df = pandas.read_csv(filename)
    
    df = df[df['Municipality'] == location]
    
    if XorEmail == 'Email':
        df = df['Email'].values
    elif XorEmail == 'Twitter':
        df = df['X Handle'].values
    else:
        df = 'none'

    return df[0] if len(df) > 0 else 'Contact detail unavailable'

print(contact_reader(filename='Data/Contact Details/Municipality_Contact_Details.csv', location='Yellowhead County', XorEmail='Twitter'))
