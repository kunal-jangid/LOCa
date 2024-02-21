import json
import time
import os
import numpy as np
import pandas
import requests
from bs4 import BeautifulSoup

import datastyler as ds

headers = {
    'User-Agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8'
}
url = "https://www.nseindia.com/api/option-chain-indices?symbol="


def removeNeg(s):
  if s < 0:
    return 0
  else:
    return s


def nifty():
  url = "https://www.nseindia.com/"
  req = requests.get(url, headers=headers)

  soup = BeautifulSoup(req.content, 'html.parser')

  niftyVal = soup.find("span", {"class": "val"}).string
  return niftyVal


def niftyval(index):
  headers = {
      'User-Agent':
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
      'Accept-Encoding': 'gzip, deflate, br',
      'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8'
  }
  url = "https://www.nseindia.com/"
  req = requests.get(url, headers=headers)

  soup = BeautifulSoup(req.content, 'html.parser')

  niftyVal = soup.find_all("p", {"class": "tb_val"})
  if index == "NIFTY":
    return niftyVal[0].text.split(' ')[0]
  elif index == "BANKNIFTY":
    return niftyVal[3].text.split(' ')[0]
  elif index == "FINNIFTY":
    return niftyVal[4].text.split(' ')[0]
  else:
    return "Error generated, try again or contact backend."


def IV(index):
  try:
    json_obj = requests.get(url + index, headers=headers).json()
    org_data = {}
    for i in json_obj["records"]["expiryDates"]:
      org_data[i] = {"PE": [], "CE": []}
    for j in json_obj["records"]["data"]:
      if "PE" in j:
        org_data[j["expiryDate"]]["PE"].append(j["PE"])
      if "CE" in j:
        org_data[j["expiryDate"]]["CE"].append(j["CE"])

    po = pandas.DataFrame.from_records(
        org_data[json_obj["records"]["expiryDates"][0]]["PE"])
    co = pandas.DataFrame.from_records(
        org_data[json_obj["records"]["expiryDates"][0]]["CE"])
    po = po["impliedVolatility"]
    co = co["impliedVolatility"]
    return po, co
  except:
    time.sleep(1)
    IV(index)


a, b = IV("NIFTY")
print(b)


def optionchain(index):
  json_obj = requests.get(url + index, headers=headers).json()
  nif = niftyval(index)
  result_df = raw_to_dataframe(json_obj)
  Prem = result_df['STRIKE'] - int(
      float(''.join(map(str, (niftyval(index).split(','))))))
  Prem_call = Prem * -1  # + result_df['LTP_call']
  Prem_put = Prem  #- result_df['LTP_put']
  result_df.insert(4, "Prem_c", Prem_call.tolist())
  result_df.insert(10, "Prem_p", Prem_put.tolist())
  result_df['Prem_c'] = result_df['Prem_c'].apply(removeNeg)
  result_df['Prem_p'] = result_df['Prem_p'].apply(removeNeg)
  return ds.prettier(result_df, index)


def raw_to_dataframe(json_obj):
  try:
    org_data = {}
    for i in json_obj["records"]["expiryDates"]:
      org_data[i] = {"PE": [], "CE": []}
    for j in json_obj["records"]["data"]:
      if "PE" in j:
        org_data[j["expiryDate"]]["PE"].append(j["PE"])
      if "CE" in j:
        org_data[j["expiryDate"]]["CE"].append(j["CE"])

    po = pandas.DataFrame.from_records(
        org_data[json_obj["records"]["expiryDates"][0]]["PE"])
    co = pandas.DataFrame.from_records(
        org_data[json_obj["records"]["expiryDates"][0]]["CE"])
    po = po[[
        "strikePrice", "pChange", "lastPrice", "totalTradedVolume",
        "changeinOpenInterest", "openInterest"
    ]]  #,"change","impliedVolatility"
    po.columns = ["STRIKE", "%", "LTP", "VOLUME", "CHNG_OI",
                  "openInterest"]  #,"CHNG", "IV"
    co = co[[
        "openInterest", "changeinOpenInterest", "totalTradedVolume",
        "lastPrice", "pChange", "strikePrice"
    ]]  #,"impliedVolatility"
    co.columns = ["openInterest", "CHNG_OI", "VOLUME", "LTP", "%",
                  "STRIKE"]  #,"IV"

    result_df = pandas.merge(co,
                             po,
                             how='right',
                             on="STRIKE",
                             indicator=False,
                             suffixes=("_c", "_p"))
    resistance1 = result_df['STRIKE'] - result_df['LTP_p']
    resistance2 = result_df['LTP_c'] + result_df['STRIKE']
    result_df.insert(6, "Br-Ev_p", resistance1.tolist())
    result_df.insert(5, "Br-Ev_c", resistance2.tolist())

    result_df[['LTP_c', 'LTP_p']] = result_df[['LTP_c', 'LTP_p']].round(1)
    result_df[['%_c', 'Br-Ev_c', '%_p',
               'Br-Ev_p']] = result_df[['%_c', 'Br-Ev_c', '%_p',
                                        'Br-Ev_p']].round(decimals=0)
    result_df['Br-Ev_p'] = result_df['Br-Ev_p'].astype(int)
    result_df['Br-Ev_c'] = result_df['Br-Ev_c'].astype(int)
    result_df = result_df.fillna(0)

    return result_df

  except Exception as e:
    print(e)


def pcr(index):
  json_obj = requests.get(url + index, headers=headers).json()
  df = raw_to_dataframe(json_obj)
  nif = int(float(''.join(map(str, (niftyval(index).split(','))))))
  c = df[df['STRIKE'] == (nif // 100 * 100)].index.values

  result = []

  for col in ['VOLUME', 'CHNG_OI', 'openInterest']:
    put_sum = df[col + '_p'].iloc[c[0] - 10:c[0]].sum()
    call_sum = df[col + '_c'].iloc[c[0]:c[0] + 10].sum()
    result.append(
        list((str(put_sum), str(call_sum), str(round(put_sum / call_sum,
                                                     4)), col)))
  return result
