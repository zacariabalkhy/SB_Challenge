from bs4 import BeautifulSoup
import requests
import json
import re
import collections as col

url = "https://www.wellsfargo.com/credit-cards/cash-back-college-card/terms"
page = requests.get(url)
soup = BeautifulSoup(page.content, 'html.parser')
tables = list(soup.find_all("table")) #get rates and fees table

rates_table = tables[1].contents
rates_table = rates_table[1].contents #get all children of rates table

fees_table = tables[2].contents
fees_table = fees_table[1].contents#get all the children of the fees table

rates_dict=[]
for tr in rates_table[0:6]:
    title_content = tr.contents #list of title and content
    title = title_content[0].text.strip() #get title
    text = title_content[1].text.strip() #get main text
    content_tags = list(title_content[1].contents) #get contents of content
    if len(content_tags) == 2:
        intro = content_tags[0].find('strong').text.strip()
        low_high_rates = list(content_tags[1].find_all('strong'))

        if len(low_high_rates) == 0:
            contents = [("rate", intro), ("text", text)]
        else:
            low_rate = low_high_rates[0].text.strip()
            high_rate = low_high_rates[1].text.strip()
            term = col.OrderedDict([("unit", "months"),
                                    ("amount", re.findall('\d+', text)[2])])
            intro_apr = col.OrderedDict([("term", term), ("rate", intro)])
            rate = col.OrderedDict([("intro", intro_apr),
                    ("low_amount", low_rate), ("high_amount", high_rate)])
            contents = [("rates", rate), ("text", text)]
    elif "days" in text:
        due_date = col.OrderedDict([("unit", "days"),
                                       ("number", re.findall('\d+', text)[0])])
    elif "Minimum Interest Charge" in title:
        charge = col.OrderedDict([("minimum charge", re.findall('[\d|.|$]+', text)[0])])
        contents = [("charge", charge), ("text", text)]
    else:
        contents = [("text", text)]
    contents=col.OrderedDict(contents)
    rates_dict.append((title, contents))


#get fees data
fees_dict=[]

#annual fees
annual_title = (fees_table[0].contents)[0].text.strip()
annual_text = (fees_table[0].contents)[1].text.strip()
annual_fees = col.OrderedDict([(annual_title, annual_text)])
fees_dict.append(("Annual Fees", annual_fees))

#transaction fees
transaction_fees_dict=[]
for tr in fees_table[2:6]:
    title_content = tr.contents #list of title and content
    title = title_content[0].find('strong').text.strip() #get title
    text = title_content[1].text.strip() #get main text
    strongs = list(title_content[1].find_all('strong'))
    if len(strongs) == 4:
        term = col.OrderedDict([("unit", "months"),
                                ("number", re.findall('\d+', text)[3])])
        intro = col.OrderedDict([("term", term),
                                 ("dollar", strongs[0].text.strip()),
                                 ("percent", strongs[1].text.strip())])
        normal_fees = col.OrderedDict([("dollar", strongs[3].text.strip()),
                                       ("percent", strongs[2].text.strip())])
        content = [("intro_fees", intro), ("normal_fees", normal_fees),
                   ("text", text)]
    elif len(strongs) == 2 and "$50" in text:
        normal_fees = col.OrderedDict([("overdraft<=$50", strongs[0].text.strip()),
                                       ("overdraft>50", strongs[1].text.strip())])
        content = [("fees", normal_fees), ("text", text)]
    elif len(strongs) == 2:
        normal_fees = col.OrderedDict([("dollar", strongs[0].text.strip()),
                                       ("percent", strongs[1].text.strip())])
        content = [("fees", normal_fees), ("text", text)]
    else:
        content = [("fee", strongs[0].text.strip()), ("text", text)]
    content=col.OrderedDict(content)
    transaction_fees_dict.append((title, content))
    fees_dict.append(("transaction fees", transaction_fees_dict))


#penalty fees
penalty_fees_dict=[]
for tr in fees_table[7:]:
    title_content = tr.contents #list of title and content
    title = title_content[0].find('strong').text.strip() #get title
    text = title_content[1].text.strip() #get main text
    fee = title_content[1].find('strong').text.strip()
    content = [("fee", fee), ("text", text)]
    content=col.OrderedDict(content)
    penalty_fees_dict.append((title, content))
fees_dict.append(("Penalty Fees", penalty_fees_dict))

rates_dict = col.OrderedDict(rates_dict)
fees_dict = col.OrderedDict(fees_dict)
page = col.OrderedDict([("APR/Rates", rates_dict), ("Fees", fees_dict)])
with open("wellsfargo.json", "w") as outfile:
    json.dump(page, outfile, indent=4)
