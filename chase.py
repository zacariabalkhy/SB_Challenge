from bs4 import BeautifulSoup
import requests
import json
import re
import collections as col

url = "https://applynow.chase.com/FlexAppWeb/pricing.do?card=FNPN&page_type=appterms"
page = requests.get(url)
soup = BeautifulSoup(page.content, 'html.parser')
tables = list(soup.find_all("table")) #get rates and fees table
rates_table = tables[1].contents #get all children of rates table
fees_table = tables[2].contents #get all the children of the fees table




#getting all the different rates
rates_dict = [] #to store the different blocks in the table (this will be converted to an ordered dict)

for tr in rates_table[3:]: #iterate through the blocks
    title_content = list(tr.find_all("td"))
    title = title_content[0].text.strip() #title of the block
    content_tags = title_content[1].find("p") #rates and text in the block
    text = content_tags.text.strip() #get the text
    span_tags = list(content_tags.find_all('span')) #if the rates are stored in <span>
    strong_tags = list(content_tags.find_all('strong')) #if the rates are stored in <strong>
    if len(strong_tags) == 0 and len(span_tags) == 0 and "days" in text: #paying interest block
            due_date = col.OrderedDict([("unit", "days"),
                                       ("number", re.findall('\d+', text)[0])])
            content = col.OrderedDict([("due_date", due_date), ("text", text)])
            rates_dict.append((title, content))
            continue
    if len(span_tags) != 0: #Purchase block
        low = span_tags[0].text.strip()
        high = span_tags[1].text.strip()
    elif len(strong_tags) == 1: #Cash Advance block
        low = strong_tags[0].text.strip()
        high = strong_tags[0].text.strip()
    elif len(strong_tags) == 2: #Balance Transfer block
        low = strong_tags[0].text.strip()
        high = strong_tags[1].text.strip()
    else: #minimum interest and Tips block
        low = "0"
        high = "0"
    amount = col.OrderedDict([("low_amount", low), ("high_amount", high)]) #store amounts in a subdict
    content = col.OrderedDict([("rates", amount), ("text", text)]) #store contents in a subdict
    rates_dict.append((title, content)) #append the table dict






#getting all the different fees
fees_dict=[]

#annual fees
annual_title_or_content = list(fees_table[3].find_all("td")) #get the annual content
annual_title = annual_title_or_content[0].text.strip() #isolate the title
annual_content_tags = annual_title_or_content[1].find("p") #isolate the information
annual_text = annual_content_tags.text.strip() #get the text info
annual_strong_tags = list(annual_content_tags.find_all('strong')) #get the numbers
intro = annual_strong_tags[0].text.strip() #intro fee
after = annual_strong_tags[1].text.strip() #after one year fee
annual_amount = col.OrderedDict([("intro", intro), ("after 1 year", after)]) #put fees into dict
annual_content = col.OrderedDict([("fees", annual_amount), ("text", annual_text)]) #put content into dict
fees_dict.append((annual_title, annual_content)) #append fees dict

#transaction fees
transaction_fees_dict=[]
for tr in fees_table[5:7]:
    title_content = list(tr.find_all("td"))
    title = title_content[0].text.strip() #title of the block
    content_tags = title_content[1].find("p") #fees and text in the block
    text = content_tags.text.strip() #get the text
    strong_tags = list(content_tags.find_all('strong')) #if the rates are stored in <strong>
    if len(strong_tags) != 0 : #Balance and cash advance blocks
        dollar = strong_tags[0].text.strip()
        percent = strong_tags[1].text.strip()
    else:
        dollar = "0"
        percent = "0"
    amount = col.OrderedDict([("dollar_amount", dollar), ("percent", percent)]) #store amounts in a subdict
    content = col.OrderedDict([("fees", amount), ("text", text)]) #store contents in a subdict
    transaction_fees_dict.append((title, content))
transaction_fees_dict = col.OrderedDict(transaction_fees_dict)
fees_dict.append(("transaction fees", transaction_fees_dict))

#penalty fees
penalty_fees_dict=[]
for tr in fees_table[9:]:
    title_content = list(tr.find_all("td"))
    title = title_content[0].text.strip() #title of the block
    content_tags = title_content[1].find("p") #fees and text in the block
    text = content_tags.text.strip() #get the text
    strong_tags = list(content_tags.find_all('strong')) #if the rates are stored in <strong>
    if len(strong_tags) == 3:
        balance100 = strong_tags[0].text.strip()
        balance250 = strong_tags[1].text.strip()
        balancemore = strong_tags[2].text.strip()
        amount = col.OrderedDict([("balance<$100", balance100),
                                  ("$100<balance<$250", balance250),
                                  ("$250<balance", balancemore)]) #store amounts in a subdict
        content = col.OrderedDict([("fees", amount), ("text", text)]) #store contents in a subdict
    elif len(strong_tags) == 1:
        fee = strong_tags[0].text.strip()
        content = col.OrderedDict([("fees", fee), ("text", text)]) #store contents in a subdict
    else:
        fee = "0"
        content = col.OrderedDict([("fees", fee), ("text", text)]) #store contents in a subdict
    penalty_fees_dict.append((title, content))
penalty_fees_dict = col.OrderedDict(penalty_fees_dict)
fees_dict.append(("penalty fees", penalty_fees_dict))



fees_dict = col.OrderedDict(fees_dict)
rates_dict = col.OrderedDict(rates_dict)
page = col.OrderedDict([("APR/Rates", rates_dict), ("Fees", fees_dict)])

with open("Chase.json", "w") as outfile:
    json.dump(page, outfile, indent=4)
