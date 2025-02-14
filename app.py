import argparse
import requests
import datetime
import time
import math
from datetime import timedelta,date

from utils import retry


def run_pipeline(N):
    d1 = date.today()
    dates = [(d1 - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(N, 0, -1)]
    dictionary_data={}
    for date1 in dates:
        dict_data=fetch_data(date1, dictionary_data)  # Call your fetch_data function for each date
        if date1==dates[-1]:
            current_data(dict_data,date1)

    Change_file=Rate_of_change(dict_data)
    Moving_avg=_file=moving_avg(dict_data)
    SD_file=SD_calculation(dict_data,N)

@retry
def fetch_data(date,Data_API_dictionary):
    http_url="https://api.currencyapi.com/v3/historical?"
    URL=f"{http_url}apikey=cur_live_Ls5wtFCl01C8akKiByP9fuyG3oOyiOaNwnMODRxC&currencies=EUR%2CUSD%2CCAD%2CPKR%2CAUD%2CCNY&date={date}"
    data=requests.get(URL)
    data_dict=data.json()

    for currencies, details in data_dict["data"].items():
        currency_code=currencies
        currency_value= details['value']
        Data_API_dictionary.setdefault(currency_code,[]).append(currency_value) # if key does not exsist inside dictionary then assign an empty list to it. after that we append the value to that list
    return Data_API_dictionary


def SD_calculation(SD_dictionary,N):
    dictionary_mean={}
    for key, value in SD_dictionary.items():
        dictionary_mean[key]=sum(value)/N

    for SD_key, SD_values in SD_dictionary.items():
        mean_value = dictionary_mean[SD_key]
        updated_values = [v-mean_value for v in SD_values]
        SD_dictionary[SD_key] = updated_values

    Total_values=len(SD_dictionary[key])
    for key, values in SD_dictionary.items():
        SD_dictionary[key]=sum((value**2) for value in values)
    for key, value in SD_dictionary.items():
        SD_dictionary[key]=math.sqrt(value/(Total_values-1))

    return SD_dictionary


def Rate_of_change(rate_change_dictionary):
    avg_value={}
    for key in rate_change_dictionary:
        current=rate_change_dictionary[key][-1] #current data
        prev=rate_change_dictionary[key][0]     #last data we have
        avg_value[key]= ((current - prev)/current )*100

    return avg_value


def moving_avg(avg_dict):
    moving_averages = {}
    window_size = 3
    i=0 

    for key, value in avg_dict.items():
        while i < len(value) - window_size + 1:
        
            window = value[i : i + window_size]    #store elements from i to i+window size
            window_average = round(sum(window) / window_size, 2)    #calculate averrage
            moving_averages.setdefault(key, []).append(window_average)            
            i+=1  #shift window to right by 1 value
        i=0

    print(moving_averages)

def current_data(current_data,date_current):
    print(f"Data for current date {date_current} is \n",current_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("n", type=int, help="Enter number of days for which data is required")
    args = parser.parse_args()  
    n=args.n

    if n>0:
        run_pipeline(n)
    else:
        print("Invalid input. N must be a positive")