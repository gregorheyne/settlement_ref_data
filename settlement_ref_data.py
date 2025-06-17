import json
import pandas as pd

def build_lseg_eclr_json():
    
    lseg_codes = pd.read_csv('data_input/05 - MemberFirmCodes_June_17-2025_9_09_00_AM.xlsx - MemberFirmCodes.csv')
    # reduce to eclr
    # we use self settle only, since e.g. Settlement-Agent also shows other accounts
    # (check e.g. Settlement Code = 94589)
    flag_eclr = lseg_codes['Settles In'] == 'Euroclear Bank'
    flag_self_settle = lseg_codes['Settlement Type'] == 'Self-Settlement'
    lseg_eclr_codes = lseg_codes[flag_eclr & flag_self_settle]
    # drop cols
    lseg_eclr_codes = lseg_eclr_codes[['Account', 'Settlement Code', 'Settlement Provider']].drop_duplicates()
    # check that account and settlement provider are the same always
    flag_check = lseg_eclr_codes['Account'] != lseg_eclr_codes['Settlement Provider']
    assert lseg_eclr_codes[flag_check].shape[0] == 1, 'detected more account not equal to settlement provider'

    # build json from accounts
    lseg_eclr_codes = lseg_eclr_codes[['Account', 'Settlement Code']].drop_duplicates(subset=['Settlement Code'], keep='last')
    print(f'found {lseg_eclr_codes.shape[0]} eclr accounts')
    lseg_eclr_codes_json = dict(zip(lseg_eclr_codes['Settlement Code'],lseg_eclr_codes['Account']))
    # modify values to indicate source
    lseg_eclr_codes_json = {x: lseg_eclr_codes_json[x] + ' (via ECLR - LSEG)'  for x in lseg_eclr_codes_json.keys()}

    with open("data_generated/lseg_eclr_codes.json", "w") as file:
        json.dump(lseg_eclr_codes_json, file, indent=4)

    return None

def build_bolton_eclr_json():

    bolton = pd.read_csv('data_input/08 - RM_Euroclear_and_Clearstream_Member_Numbers(1).csv', dtype={'Clearstream Number': str})

    # keep only digits
    bolton = bolton[bolton['Euroclear Number'].str.isdigit() == True]

    # remove unknown / UNPPUBLISHED
    bolton = bolton[bolton['Participant Name'].str.contains('UNPPUBLISHED') == False]
    bolton = bolton[bolton['Participant Name'].str.contains('UNPUBL') == False]

    # check uniqueness
    assert bolton['Euroclear Number'].nunique() == bolton.shape[0], 'Euroclear Accounts not unique in Bolton'

    # convert to dict
    bolton_eclr_codes_json = dict(zip(bolton['Euroclear Number'],bolton['Participant Name'].str.strip()))
    # modify values to indicate source
    bolton_eclr_codes_json = {x: bolton_eclr_codes_json[x] + ' (via ECLR - Bolton)'  for x in bolton_eclr_codes_json.keys()}

    with open("data_generated/bolton_eclr_codes.json", "w") as file:
        json.dump(bolton_eclr_codes_json, file, indent=4)

    return None

def get_eclr_name_map():

    # read lseg_eclr_codes_json
    with open('data_generated/lseg_eclr_codes.json') as f:
        eclr_name_map = json.load(f)
    
    # augment with additional codes
    eclr_name_map['98366'] = 'Morgan Stanley (via ECLR - [02])'  # source [2]
    eclr_name_map['99365'] = 'Deutsche Bank AG, Frankfurt (via ECLR - [03])'  # source [3]
    eclr_name_map['91255'] = 'Deutsche Bank AG, London (via ECLR - [03])'  # source [3]
    eclr_name_map['95724'] = 'JP Morgan Securities, UK (via ECLR - [06])'  # source [6]
    eclr_name_map['92707'] = 'Merrill Lynch International, UK (via ECLR - [07])'  # source [7]
    eclr_name_map['23162'] = 'Bank of America SECURITIES EUROPE SA (via ECLR - [09])'  # source [9]
    eclr_name_map['23210'] = 'Bank of America SECURITIES EUROPE SA (via ECLR - [09])'  # source [9]
    eclr_name_map['98730'] = 'Pershing LLC (via ECLR - [08, 10])'  # source [8, 10]

    # load bolton_eclr_codes_json
    with open('data_generated/bolton_eclr_codes.json') as f:
        bolton_eclr_codes_json = json.load(f)

    # compare agsinst bolton_eclr_codes_json were possible
    # for code in eclr_name_map.keys():
    #     if code in bolton_eclr_codes_json.keys():
    #         print(f'{code}: {eclr_name_map[code]} and {bolton_eclr_codes_json[code]}')

    # augment with bolton_eclr_codes_json
    for code in bolton_eclr_codes_json.keys():
        if code not in eclr_name_map.keys():
            eclr_name_map[code] = bolton_eclr_codes_json[code]

    return eclr_name_map
