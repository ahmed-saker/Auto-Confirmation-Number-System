# If there are new customers update "mails" sheet at "E:\Users\Administrator\Handover V2\Operations\mails.xlsx"

import requests
import pandas as pd
import xmltodict
from tqdm import tqdm
import aiohttp
import asyncio
import retrying
import pymysql
import json
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings("ignore")

juniper_user = 'xxxxt'
juniper_pass = 'xxxxxxx'

host = 'xxxxxxx'
port = xxxxx
user = 'xxxxxx'
password = 'xxxxxx'
database='xxxxxxxx'

def renew_access_token():
    while True:
        access_token = 'xxxxxxxxxxxxxxxxxxxxx'
        code = "xxxxxxxxxxxxxxxxxxx"
        client_id = "xxxxxxxxxxxxxx"
        client_secret = "xxxxxxxxxxxxxxx"
        grant_type = "xxxxxxxxxxxxxx"
        refresh_token = "xxxxxxxxxxxxxxxxxxxxxxxx"
        URL = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        params = {"refresh_token": refresh_token,"client_id": client_id,
            "client_secret": client_secret,"scope": ["Desk.tickets.ALL", "Desk.tickets.UPDATE", "Desk.tickets.CREATE"],
            "grant_type": "refresh_token"}
        try:
            # Sending a POST request and saving the response as a response object
            access_token_refresh = requests.post(url=URL, params=params)
            access_token_refresh_dict = json.loads(access_token_refresh.text)
            new_access_token = access_token_refresh_dict['access_token']
            break
        except Exception as e:
            print("Token Error:", e)
    return new_access_token

while True:
    mails = pd.read_excel(r"E:\Users\Administrator\Handover V2\Operations\mails.xlsx")
    
    column_mapping = {'@Id': 'Id', '@Status': 'Status', '@BookingCode': 'BookingCode', '@BookingDate': 'BookingDate',
                      '@LastModifiedDate': 'LastModifiedDate','@AgencyRef':'AgencyRef','@TimeZone':'TimeZone'}
    
    def get_booking_codes():
        url="xxxxxxxxxxxxxxxxxx"
        headers = {'content-type': 'text/xml','SOAPAction':'http://juniper.es/getBookingList',"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
            "Accept-Encoding": "*",
            "Connection": "keep-alive"}
        body = f"""<?xml version="1.0" encoding="utf-8"?>
            <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
              <soap:Body>
                <getBookingList xmlns="http://juniper.es/">
                  <user>{juniper_user}</user>
                  <password>{juniper_pass}</password>
                  <LastModifiedDateFrom>{(datetime.now() - timedelta(days=1)).strftime('%Y%m%d')}</LastModifiedDateFrom>
                  <LastModifiedDateTo>{(datetime.now()).strftime('%Y%m%d')}</LastModifiedDateTo>
                  <BeginTravelDateFrom>{(datetime.now()).strftime('%Y%m%d')}</BeginTravelDateFrom>
                  <Status>OK,Con</Status>
                </getBookingList>
              </soap:Body>
            </soap:Envelope>"""
        while True:
            try:
                response = requests.post(url,data=body,headers=headers)
                break
            except:
                pass
        data = xmltodict.parse(response.text)
        listBookingsDF = pd.DataFrame(data['soap:Envelope']['soap:Body']['getBookingListResponse']['getBookingListResult']['wsResult']['BookingList']['Booking'])
        return listBookingsDF
    listBookingsDF = get_booking_codes()
    
    listBookingsDF = listBookingsDF.rename(columns=column_mapping)
    bookingCodes = list(set(listBookingsDF['BookingCode'].to_list()))
    
    Juniper_df = pd.DataFrame(columns=['BookingCode','CustomerId','CustomerName','ConfirmationNumber','TravelDate'])
    
    @retrying.retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000, wait_exponential_max=10000)
    async def GetBookingData(session, code, pbar):
        url = "xxxxxxxxxxxxxxxxxxxx"
        headers = {
            'content-type': 'text/xml',
            'SOAPAction': "http://juniper.es/getBookings",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
            "Accept-Encoding": "*",
            "Connection": "keep-alive"
        }
        body = f"""<?xml version="1.0" encoding="utf-8"?>
            <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
              <soap:Body>
                <getBookings xmlns="http://juniper.es/">
                  <user>{juniper_user}</user>
                  <password>{juniper_pass}</password>
                  <BookingCode>{code}</BookingCode>
                </getBookings>
              </soap:Body>
            </soap:Envelope>"""
        try:
            async with session.post(url, data=body, headers=headers, timeout=120) as response:
                responseDict = xmltodict.parse(await response.text())
                AllBookings = responseDict['soap:Envelope']['soap:Body']['getBookingsResponse']['getBookingsResult']['wsResult']['Bookings']['Booking']
                if isinstance(AllBookings['Lines']['Line'], list):
                    for j in range(len(AllBookings['Lines']['Line'])):
                        try:
                            if isinstance(AllBookings['Lines']['Line'][j]['roomlist']['room'],list):
                                remark = AllBookings['Lines']['Line'][j]['roomlist']['room'][0]['confirmationreference']
                            else:
                                remark = AllBookings['Lines']['Line'][j]['roomlist']['room']['confirmationreference']
                        except:
                            remark = ''
                        row = [
                            AllBookings['@BookingCode'],
                            AllBookings['Customer']['@Id'],
                            AllBookings['Customer']['Name'],
                            remark,
                            AllBookings['Lines']['Line'][j]['BeginTravelDate'][:AllBookings['Lines']['Line'][j]['BeginTravelDate'].index('T')]
                        ]
                        Juniper_df.loc[len(Juniper_df)] = row
                else:
                    try:
                        if isinstance(AllBookings['Lines']['Line']['roomlist']['room'],list):
                            remark = AllBookings['Lines']['Line']['roomlist']['room'][0]['confirmationreference']
                        else:
                            remark = AllBookings['Lines']['Line']['roomlist']['room']['confirmationreference']
                    except:
                        remark = ''
                    row = [
                        AllBookings['@BookingCode'],
                        AllBookings['Customer']['@Id'],
                        AllBookings['Customer']['Name'],
                        remark,
                        AllBookings['Lines']['Line']['BeginTravelDate'][:AllBookings['Lines']['Line']['BeginTravelDate'].index('T')]
                    ]
                    Juniper_df.loc[len(Juniper_df)] = row
        except Exception as e:
            print(f"Error processing code {code}: {e}")
            pass
        finally:
            pbar.update(1)
    
    async def main():
        async with aiohttp.ClientSession() as session:
            tasks = []
            with tqdm(total=len(bookingCodes), desc="Processing") as pbar:
                for code in bookingCodes:
                    tasks.append(asyncio.ensure_future(GetBookingData(session, code, pbar)))
                await asyncio.gather(*tasks)
    start_time = time.time()
    print("Start Retreving Data From Api...")
    asyncio.run(main())
    print("Data Retrieved from Api in:", time.time() - start_time)
    
    mails['CustomerId'] = mails['CustomerId'].astype(str)
    Juniper_df['CustomerId'] = Juniper_df['CustomerId'].astype(str)
    
    last_df = (listBookingsDF.merge(Juniper_df,on='BookingCode',how='left')).merge(mails[['CustomerId','Mail']],on='CustomerId',how='left')
    
    last_df = last_df.sort_values(by='TravelDate').drop_duplicates(subset=['BookingCode'])
    
    last_df['CustomerName'] = last_df['CustomerName'].fillna('')

    filtered_df = last_df[~last_df['CustomerName'].str.contains('Global International|Global Egypt|how to work|Contracting|Individual company|E Commerce BTC|E Commerce BTB',case=False)]
    filtered_df['BookingDate'] = filtered_df['BookingDate'].apply(lambda x: x.split('T')[0])
    filtered_df['LastModifiedDate'] = filtered_df['LastModifiedDate'].apply(lambda x: x.split('T')[0])
    
    connection = pymysql.connect(host=host,port=port,user=user,password=password,database=database)
    cursor = connection.cursor()
    
    cursor.execute("select BookingCode,BookingDate,ConfirmationNumber,EmailSent from bookinglist where TravelDate>=%s",(f"{datetime.now().strftime('%Y-%m-%d')}",))
    results = cursor.fetchall()
    
    
    db_data = pd.DataFrame(results,columns=['BookingCode','db_BookingDate','db_HCN','EmailSent'])
    
    juniper_db_df = filtered_df.merge(db_data,on='BookingCode',how='left')
    NoMails = juniper_db_df[juniper_db_df['Mail'].isna()]
    NewBookings = juniper_db_df[(juniper_db_df['db_BookingDate'].isna()) & (juniper_db_df['Mail'].isna()==False)]
    connection = pymysql.connect(host=host,port=port,user=user,password=password,database=database)
    cursor = connection.cursor()
    
    NewBookings = NewBookings.reset_index()
    print("Start Saving New Bookings into DataBase")
    for i, v in tqdm(NewBookings.iterrows(), total=NewBookings.shape[0]):
        query = ("INSERT Ignore INTO bookinglist (Id, Status, BookingCode, BookingDate, LastModifiedDate, AgencyRef, TimeZone, CustomerId, CustomerName, ConfirmationNumber, TravelDate, CustomerEmail) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ")
        data = (NewBookings.iloc[i]['Id'], NewBookings.iloc[i]['Status'], NewBookings.iloc[i]['BookingCode'],
            NewBookings.iloc[i]['BookingDate'], NewBookings.iloc[i]['LastModifiedDate'], NewBookings.iloc[i]['AgencyRef'],
            NewBookings.iloc[i]['TimeZone'], NewBookings.iloc[i]['CustomerId'], NewBookings.iloc[i]['CustomerName'],
            NewBookings.iloc[i]['ConfirmationNumber'], NewBookings.iloc[i]['TravelDate'], NewBookings.iloc[i]['Mail'])
        cursor.execute(query, data)
    print("New Bookings have been saved successfully into DataBase")
    
    connection.commit()
    cursor.close()
    connection.close()
    
    UpdateBookings = juniper_db_df[((juniper_db_df['db_HCN'].isna()) | (juniper_db_df['db_HCN']=='')) & (juniper_db_df['db_BookingDate'].isna()==False) & ((juniper_db_df['ConfirmationNumber'].isna()==False) | (juniper_db_df['ConfirmationNumber']!='')) & (juniper_db_df['ConfirmationNumber'].str.contains('conf|number|conformation|confirmation|confirmed|reference|confrimation|confirm|hcn', case=False)) & (juniper_db_df['Mail'].isna()==False)]
    
    connection = pymysql.connect(host=host,port=port,user=user,password=password,database=database)
    cursor = connection.cursor()
    
    print("Start Update old Bookings into DataBase")
    UpdateBookings = UpdateBookings.reset_index()
    for i, v in tqdm(UpdateBookings.iterrows(), total=UpdateBookings.shape[0]):
        cursor.execute("""Update bookinglist set ConfirmationNumber = %s, CustomerEmail = %s,CustomerName = %s, CustomerId = %s
        where BookingCode =%s""", 
        (UpdateBookings.iloc[i]['ConfirmationNumber'],UpdateBookings.iloc[i]['Mail'],UpdateBookings.iloc[i]['CustomerName'],
         UpdateBookings.iloc[i]['CustomerId'], UpdateBookings.iloc[i]['BookingCode']))
    print("Data updated successfully into DataBase")
    
    connection.commit()
    cursor.close()
    connection.close()
    
    connection = pymysql.connect(host=host,port=port,user=user,password=password,database=database)
    cursor = connection.cursor()
    
    #cursor.execute("select BookingCode,AgencyRef,CustomerName,ConfirmationNumber,CustomerId from bookinglist where EmailSent is null and CustomerEmail is not null and ConfirmationNumber is not null and TravelDate>=%s",(f"{datetime.now().strftime('%Y-%m-%d')}",))
    
    cursor.execute("""
        SELECT BookingCode, AgencyRef, CustomerName, ConfirmationNumber, CustomerId
        FROM bookinglist
        WHERE (EmailSent IS NULL OR EmailSent = '')
          AND CustomerEmail IS NOT NULL
          AND ConfirmationNumber IS NOT NULL
          AND TravelDate >= CURRENT_DATE()
          AND (
                LOWER(ConfirmationNumber) LIKE '%conf%' OR
                LOWER(ConfirmationNumber) LIKE '%number%' OR
                LOWER(ConfirmationNumber) LIKE '%conformation%' OR
                LOWER(ConfirmationNumber) LIKE '%confirmation%' OR
                LOWER(ConfirmationNumber) LIKE '%confirmed%' OR
                LOWER(ConfirmationNumber) LIKE '%reference%' OR
                LOWER(ConfirmationNumber) LIKE '%confrimation%' OR
                LOWER(ConfirmationNumber) LIKE '%confirm%' OR
                LOWER(ConfirmationNumber) LIKE '%hcn%'
              );
        """)#,(f"{datetime.now().strftime('%Y-%m-%d')}",))
    
    results = cursor.fetchall()
    
    send_df = pd.DataFrame(results,columns=['BookingCode','AgencyRef','CustomerName','ConfirmationNumber','CustomerId'])#Mail
    
    cursor.close()
    connection.close()
    send_df = send_df.merge(mails[["CustomerId","Mail","CC"]], on="CustomerId",how="left")
    send_df["CC"] = send_df["CC"].fillna('')
    connection = pymysql.connect(host=host,port=port,user=user,password=password,database=database)
    cursor = connection.cursor()
    send_df = send_df.reset_index()
    try:
        print("Update Key Resorts bookings where agency ref is conf number set to null")
        drop_indices = []
        for i,v in send_df.iterrows():
            if send_df.iloc[i]['CustomerName'] == 'Key Resorts International (KRI)':
                AgencyRef = send_df.iloc[i]['AgencyRef'].split('-')[0]
                if AgencyRef in send_df.iloc[i]['ConfirmationNumber']:
                    cursor.execute("""Update bookinglist set ConfirmationNumber = %s where BookingCode =%s""", 
                    (None,send_df.iloc[i]['BookingCode']))
                    drop_indices.append(i)
        send_df = send_df.drop(drop_indices)
        send_df = send_df.reset_index(drop=True)
        connection.commit()
    except Exception as e:
        print("An error occurred:", str(e))
    
    finally:
        cursor.close()
        connection.close()
    
    
    connection = pymysql.connect(host=host,port=port,user=user,password=password,database=database)
    cursor = connection.cursor()
    new_access_token = renew_access_token()
    send_df = send_df.reset_index()
    
    try:
        print("Start Sending ..................")
        for i, v in tqdm(send_df.iterrows(), total=send_df.shape[0]):
            ticket_id = ''
            print(send_df.iloc[i]['Mail'],send_df.iloc[i]['BookingCode'],send_df.iloc[i]['ConfirmationNumber'],
                  send_df.iloc[i]['CustomerName'],send_df.iloc[i]['AgencyRef'],new_access_token)
            org_id="786481962"
            ticket_data={"departmentId":"766285000000006907","email":f"{send_df.iloc[i]['Mail']}",
                    "subject":f"Booking Confirmation [{send_df.iloc[i]['AgencyRef']}]-[{send_df.iloc[i]['BookingCode']}] {send_df.iloc[i]['CustomerName']}",
                "description":f"Booking Confirmation [{send_df.iloc[i]['AgencyRef']}]-[{send_df.iloc[i]['BookingCode']}] {send_df.iloc[i]['CustomerName']}",
            "contact":{"firstName":"Auto","lastName":"Confirmation"},"channel":"Email"}
            headers = {"Authorization":f"Zoho-oauthtoken {new_access_token}","orgId":org_id,
                "contentType": "application/json; charset=utf-8"}
            request=requests.post('https://desk.zoho.com/api/v1/tickets', headers=headers,data=json.dumps(ticket_data))
            data = request.json()
            try:
                ticket_id=data['id']
            except Exception as e:
                print(data,send_df.iloc[i]['Mail'],e)
            content=f"""
            <head>
            <style>
                body {{font-family: Arial, sans-serif;margin: 0;padding: 0;font-size: 10px;}}
                .container {{max-width: 600px;margin: 0 auto;padding: 20px;border: 1px solid #ccc;}}
                table {{width: 100%;border-collapse: collapse;margin-bottom: 20px;}}
                th, td {{border: 1px solid #ccc;padding: 10px;text-align: left;}}
                .footer {{background-color: #f7f7f7;padding: 10px;text-align: center;}}
            </style>
            </head>
            <body>
            <div class="container">
                <h1>Booking Confirmation</h1>
                <p>Dear Partner,</p>
                <p>Your booking has been confirmed. Please find the details below:</p>
                <p>*Please note that this is an auto-generated confirmation mail,replies to this mail will not be monitored.</p>
                <p>*if you have an additional request or an inquiry kindly submit a different mail with your request.</p>
                <table>
                    <tr>
                        <th>{send_df.iloc[i]['CustomerName']} Reference Number</th>
                        <th>EET Global Booking Code</th>
                        <th>Hotel Confirmation Number</th>
                    </tr>
                    <tr>
                        <td>{send_df.iloc[i]['AgencyRef']}</td>
                        <td>{send_df.iloc[i]['BookingCode']}</td>
                        <td>{send_df.iloc[i]['ConfirmationNumber']}</td>
                    </tr>
                </table>
                <footer>
                  <p>Terms and Conditions that apply for this booking as per the original booking made on EET Global Online System</p>
                  <p>2023 © EET Global</p>
                </footer>
                <p>If you have any questions, please contact our Customer Care team.</p>
            </div>
            <div class="footer">
                <p>Customer Care EET Global Team</p>
                <p>+202-33080700-33057373 (Ext: 1350)</p>
                <p>1st & 2nd floor, 94 Shehab St.,Mohandeseen, Giza, Egypt</p>
            </div>
            </body>"""
            #cc_emails = send_df.iloc[i]['CC'].split(',')
            ticket_data={"channel" : "EMAIL","content":content,"contentType":'html',"to":send_df.iloc[i]['Mail']
                         ,'fromEmailAddress':"customer.care@eetglobal.net"
                         ,"cc":"customer.care@eetglobal.net,"+send_df.iloc[i]['CC'],'ticketStatus':"Closed"}
            print(ticket_id)
            request=requests.post(f'https://desk.zoho.com/api/v1/tickets/{ticket_id}/sendReply?sendImmediately=true', headers=headers,data=json.dumps(ticket_data))
            cursor.execute("""Update bookinglist set EmailSent = %s where BookingCode =%s""", 
            ( ticket_id, send_df.iloc[i]['BookingCode']))
            time.sleep(2)
        connection.commit()
    except Exception as e:
        print("Error When Sending:", e)
    finally:
        cursor.close()
        connection.close() 
    print(f"Time Now is {datetime.now().strftime('%Y%m%d-%H:%M:%S')}")
    print("Sleep 5 Minutes ....")
    time.sleep(300)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    







