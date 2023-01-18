# info: vincent.poitras@ec.gc.ca
# These functions were developped with the intention to be called from a bash script
# and make easier the manipulations of yaml file wiyhin the bash script 


import yaml
import sys


def check_if_readable(yml_file):
    """
    Return yes if yml_file may be read
    Return no otherwise
    """
    stream = open(yml_file, 'r')
    try:
        dictionary = yaml.safe_load(stream)
        print('yes')
    except:
        print('no')



def replace_value(yml_file,newvalue,keys):
    """
    yml_file: File to edit
    newvalue: New value that will be set
    keys    : Array of key to identify the entry to replace (currently limited to 5 keys)
    """
    nkeys      = len(keys)
    stream     = open(yml_file, 'r')
    dictionary = yaml.safe_load(stream)

    # Should find a more cleaver way to do this (flattening and unflattening a dict?)
    if   nkeys == 1: dictionary[ keys[0] ]                                             = newvalue
    elif nkeys == 2: dictionary[ keys[0] ][ keys[1] ]                                  = newvalue
    elif nkeys == 3: dictionary[ keys[0] ][ keys[1] ][ keys[2] ]                       = newvalue
    elif nkeys == 3: dictionary[ keys[0] ][ keys[1] ][ keys[2] ][ keys[3] ]            = newvalue
    elif nkeys == 3: dictionary[ keys[0] ][ keys[1] ][ keys[2] ][ keys[3] ][ keys[4] ] = newvalue
    else:
        print('You have passed %d keys' % (nkeys) )
        print('Maxiumum number of keys is hardcoded to 5 (but this may be edited)')
        print('Exit')
        exit()
    stream = open(yml_file, 'w')
    output = yaml.dump(dictionary, stream)



def extract_value(yml_file, keys):
    """
    yml_file: File from which value will be extracted
    keys    : "list" of keys (each key is separated by a space)
    """
    #yml_file = sys.argv[1]
    #keys     = sys.argv[2:]

    stream     = open(yml_file, 'r')
    dictionary = yaml.safe_load(stream)


    for key in keys.split():
        try:
            # The key exist in the dictionary and is a string
            dictionary = dictionary[str(key)]
        except:
            # The key exist in the dictionary but is not a string
            for d in dictionary:
                if str(d) == key:
                    newkey = d
                    break
            try:
                dictionary = dictionary[newkey]
            except:
                print('[WARNING]\u00A0Key=%s\u00A0not\u00A0found.' % key)
                return()

    if type(dictionary) is dict or type(dictionary) is list:
        for key in dictionary:
            if not str(key) is None:
                output = str(key).replace(' ','\u00A0')
            print(output)
    else:
        value  = dictionary                  # To make explicit that we are not dealing anymore with a dictionary
        if value is None:
            output = ''
        else:
            output = str(value).replace(' ','\u00A0')
        print(output)

