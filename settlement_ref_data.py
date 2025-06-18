import json
import pandas as pd

def build_lseg_eclr_json():

    lseg_codes = pd.read_csv('data_input/05 - MemberFirmCodes_June_17-2025_9_09_00_AM.xlsx - MemberFirmCodes.csv')

    # check on settlement types
    assert set(lseg_codes['Settlement Type']) == {'Self-Settlement', 'Settlement-Agent', 'Model-B'}, 'settlement types changed'

    # reduce to eclr
    flag_eclr = lseg_codes['Settles In'] == 'Euroclear Bank'
    lseg_eclr_codes = lseg_codes[flag_eclr].copy()

    # region start with self settle
    flag_self_settle = lseg_eclr_codes['Settlement Type'] == 'Self-Settlement'
    lseg_eclr_codes_self = lseg_eclr_codes[flag_self_settle].copy()
    # drop cols
    lseg_eclr_codes_self = lseg_eclr_codes_self[['Account', 'Settlement Code', 'Settlement Provider']].drop_duplicates()
    # check that account and settlement provider are the same always
    flag_check = lseg_eclr_codes_self['Account'] != lseg_eclr_codes_self['Settlement Provider']
    assert lseg_eclr_codes_self[flag_check].shape[0] == 1, 'detected more account not equal to settlement provider for self settlement'
    # build json from accounts
    lseg_eclr_codes_self = lseg_eclr_codes_self[['Account', 'Settlement Code']].drop_duplicates(subset=['Settlement Code'], keep='last')
    print(f'found {lseg_eclr_codes_self.shape[0]} eclr self settlement accounts')
    lseg_eclr_codes_self_json = dict(zip(lseg_eclr_codes_self['Settlement Code'], lseg_eclr_codes_self['Account']))
    # modify values to indicate source
    lseg_eclr_codes_self_json = {x: lseg_eclr_codes_self_json[x] + ' (via ECLR - LSEG)'  for x in lseg_eclr_codes_self_json.keys()}
    # endregion

    # region settlement types 'Settlement-Agent' and 'Model-B'
    flag_non_self = lseg_eclr_codes['Settlement Type'] != 'Self-Settlement'
    lseg_eclr_codes_non_self = lseg_eclr_codes[flag_non_self].copy()
    # drop cols
    lseg_eclr_codes_non_self = lseg_eclr_codes_non_self[['Account', 'Settlement Code', 'Settlement Provider']].drop_duplicates()
    # check that account and settlement provider are never the same
    flag_check = lseg_eclr_codes_non_self['Account'] == lseg_eclr_codes_non_self['Settlement Provider']
    assert lseg_eclr_codes_non_self[flag_check].shape[0] == 0, 'detected account equal to settlement provider for non-self'
    # further reduction by only allowing codes that are not in the self settlement version already
    # (check for example code 14448, which is used for self-settlement but also for model-b types)
    lseg_eclr_codes_non_self = lseg_eclr_codes_non_self[~lseg_eclr_codes_non_self['Settlement Code'].isin(lseg_eclr_codes_self_json.keys())]
    # check for duplicate Settlement Codes
    lseg_eclr_codes_non_self['count_code'] = lseg_eclr_codes_non_self.groupby('Settlement Code')['Settlement Code'].transform('count')
    lseg_eclr_codes_non_self[lseg_eclr_codes_non_self['count_code']==4]
    # since there are still duplicates in the accounts we just take the settlement provider
    #  but flag is as being an agent or model b type inferred
    lseg_eclr_codes_non_self = lseg_eclr_codes_non_self[['Settlement Code', 'Settlement Provider']].drop_duplicates()
    print(f'found {lseg_eclr_codes_non_self.shape[0]} eclr non-self settlement accounts')
    # build json from accounts
    lseg_eclr_codes_non_self_json = dict(zip(lseg_eclr_codes_non_self['Settlement Code'], lseg_eclr_codes_non_self['Settlement Provider']))
    # modify values to indicate source
    lseg_eclr_codes_non_self_json = {x: lseg_eclr_codes_non_self_json[x] + ' (via ECLR - LSEG non-self)'  for x in lseg_eclr_codes_non_self_json.keys()}
    # endregion

    # combine
    lseg_eclr_codes_json = lseg_eclr_codes_self_json | lseg_eclr_codes_non_self_json
    print(f'{len(lseg_eclr_codes_json)} lseg eclr codes together')

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
    eclr_name_map['21159'] = 'Citigroup (via ECLR - [11])'  # source [11]
    eclr_name_map['77354'] = 'Société Générale Luxembourg (via ECLR - [12])' # source [12]

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
