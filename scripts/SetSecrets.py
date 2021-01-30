import os

if os.environ.get('USERNAME','unknown') == 'leis':
    print ('secret set')
else:
    print ('secret not set')