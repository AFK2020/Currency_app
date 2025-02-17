import argparse
import requests
import datetime
import time
import math
import csv
import matplotlib.pyplot as plt
import numpy as np
import io
from collections import defaultdict
from datetime import timedelta,date
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph, Image
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing 
from reportlab.graphics import renderPDF
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from utils import retry


def run_pipeline(N):
    required_currency=['pkr','cad','aud']

    d1 = date.today()
    dates = [(d1 - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(N, 0, -1)]
    dictionary_data = {}
    file_path="data.csv"
    dictionary_data=defaultdict(list)
    for date1 in dates:
        dict_data = fetch_data(date1, dictionary_data)  # Call your fetch_data function for each date
        for currencies, details in dict_data["usd"].items():
            if currencies in required_currency:
                currency_code = currencies
                currency_value = details
                #dictionary_data.setdefault(currency_code,[]).append(currency_value) # if key does not exsist inside dictionary then assign an empty list to it. after that we append the value to that list
                dictionary_data[currency_code].append(currency_value) # if key does not exsist inside dictionary then assign an empty list to it. after that we append the value to that list

        # if date1 == dates[-1]:
        #    for values in required_currency:
        #        print(f"{values} Data for {date1}=", dict_data['usd'][values])

    data_file = csv_write(dictionary_data,file_path,dates)
    change_file = calculate_rate_of_change(dictionary_data)
    moving_avg_file = calculate_moving_avg(dictionary_data)
    sd_file = calculate_standard_deviations(dictionary_data,N)
    pdf_write(sd_file,moving_avg_file,change_file,data_file)


@retry
def fetch_data(date,Data_API_dictionary):

    http_url="https://cdn.jsdelivr.net/npm/@fawazahmed0/currency"
    URL=f"{http_url}-api@{date}/v1/currencies/usd.json"
    data=requests.get(URL)
    data_dict=data.json()
    return data_dict


def calculate_standard_deviations(SD_dictionary,N):
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


def calculate_rate_of_change(rate_change_dictionary):
    avg_value = {}
    for key in rate_change_dictionary:
        current = rate_change_dictionary[key][-1] #current data
        prev = rate_change_dictionary[key][0]     #last data we have
        avg_value[key] = ((current - prev)/current )*100

    return avg_value


def calculate_moving_avg(avg_dict):
    moving_averages = {}
    window_size = 3
    i=0 
    moving_averages=defaultdict(list)

    for key, value in avg_dict.items():

        while i < len(value) - window_size + 1:
        
            window = value[i : i + window_size]    #store elements from i to i+window size
            window_average = round(sum(window) / window_size, 2)    #calculate averrage
            #moving_averages.setdefault(key, []).append(window_average)  
            moving_averages[key].append(window_average)          
            i+=1  #shift window to right by 1 value
        i=0

    return moving_averages


def csv_write(csv_file_dictionary, file_path, dates):
    header = ['date'] + list(csv_file_dictionary.keys())
    list_dict = [header]    #[date, aud, cad, pkr]
    
    # iterate over the dates
    for i in range(len(dates)):
        row = [dates[i]]  # Start the row with the current date
        for currency in csv_file_dictionary.values():
            row.append(currency[i])
        
        list_dict.append(row)   #append each row of values
    with open(file_path, 'w', newline='') as output_file:
        dict_writer = csv.writer(output_file)
        dict_writer.writerows(list_dict)  # Write all rows
    
    return list_dict


def graph_plot(data_file_pdf):
    date_x = [row[0] for row in data_file_pdf[1:]]
    aus_x = [row[1] for row in data_file_pdf[1:]]
    cad_x = [row[2] for row in data_file_pdf[1:]]
    pkr_x = [row[3] for row in data_file_pdf[1:]]
    fig, ax = plt.subplots(figsize=(6, 4))  # Set the size of the plot
    plt.plot(date_x, aus_x, marker='o', color='b', label="AUD vs Date")
    plt.plot(date_x, cad_x, marker='o', color='b', label="CAD vs Date")
    #plt.plot(date_x, pkr_x, marker='o', color='b', label="PKR vs Date")
    
    plt.grid(True)

    # Save the plot as a PNG image in a buffer
    img_buffer = io.BytesIO()
    plt.xticks(rotation=45)  # Rotate dates for better readability
    plt.tight_layout()  # Adjust layout to prevent overlap
    plt.savefig(img_buffer, format='png')
    plt.close(fig)
    img_buffer.seek(0)
    return img_buffer



def pdf_write(rate_of_change_file_pdf,moving_avg_file_pdf,sd_file_pdf,data_file_pdf):
    file_name="table.pdf"

    doc=SimpleDocTemplate(file_name,papersize=letter)
    data_sd=[["Currency","Standard_Deviation"]] #converting dictionary into list of lists
    for key, value in sd_file_pdf.items():
        data_sd.append([key,value])
    table1=Table(data_sd)

    data_moving_avg=[["currency", "moving_avergae"]]
    for key, value in moving_avg_file_pdf.items():
        for mavg_value in value:
            data_moving_avg.append([key,mavg_value])  #To access list inside dictionary value
    table2=Table(data_moving_avg)

    data_rate_of_change=[["Currency", "rate_of_change"]]
    for key, value in rate_of_change_file_pdf.items():
        data_rate_of_change.append([key,value])
    table3=Table(data_rate_of_change)

    style = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Header row background color
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  # Header text color
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center-align text in all cells
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Font for header
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Padding for header row
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  # Background color for data rows
    ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Table grid lines
    ])

    styles = getSampleStyleSheet()
    title1 = Paragraph("Standard Deviation for currencies", styles['Heading1'])
    title2 = Paragraph("Moving Average", styles['Heading1'])
    title3 = Paragraph("Rate of change for currencies (%)", styles['Heading1'])

    table1.setStyle(style)
    table2.setStyle(style)
    table3.setStyle(style)
    space = Spacer(1,30)

    graph_buffer = graph_plot(data_file_pdf)

    # Add the graph to the PDF as a Drawing element
    drawing = Drawing(400, 300)
    image=Image(graph_buffer)
    image.width=400
    image.height=300

    elements = [title1, Spacer(1,20),table1,space, title2, Spacer(1,20),table2, space, title3, Spacer(1,20),table3, Spacer(1,30),image]
    doc.build(elements)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("n", type=int, help="Enter number of days for which data is required")
    args = parser.parse_args()  
    n=args.n

    if n>0:
        run_pipeline(n)
    else:
        print("Invalid input. N must be a positive integer")


