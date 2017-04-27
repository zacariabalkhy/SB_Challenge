from bs4 import BeautifulSoup
import requests
import json
import re
import collections as col

url = "https://www.americanexpress.com/us/credit-cards/personal-card-application/terms/blue-credit-card/25330-10-0/?print#FeeTable"
page = requests.get(url)
soup = BeautifulSoup(page.content, 'html.parser')
# apr_rates = soup.find("font", { "class" : "aprfontsize"})
int_rates_table = soup.find("div", {"id" : "lendingratestable"})
fees_table = soup.find("div", {"id" : "commonfeestable"})

# scrape all data for lendingratestable
text=[]
rate_type=[]
APR=[]
for subBlock in int_rates_table.select('div[class*=tableSubBlock]'):
    texti = subBlock.select_one('div[class*=val]')
    APRi = texti.find('b')
    text.append(texti.text.strip())
    rate_type.append(subBlock.select_one('div').text.strip())
    if APRi is None:
        continue
    APR.append(APRi.text.strip())

# organize data for lendingratestable

# Purchase APR
purchase = col.OrderedDict([("purchase_APR", APR[0]), ("apr_text", text[0])])

#Balanct Transfer APR
term = col.OrderedDict([("unit", "days"),
                        ("amount", re.findall('\d+', text[1].split('%')[1])[0])])

BT = col.OrderedDict([("balance_tansfer_APR", APR[1]),
                      ("term", term), ("text", text[1])])

#APR for Cash Advances

CA = col.OrderedDict([("cash_advance_apr", APR[2]), ("apr_text", text[2])])

#Penalty APR
when1 = re.split('[)|;]+', text[3])[1]
when2 = re.split('[)|H]+', text[3])[2]
when = col.OrderedDict([("1", when1), ("2", when2)])
length = col.OrderedDict([("unit", "months"),
                          ("amount", re.findall(r'\d', text[3].split('?')[1])[0]),
                          ("length_text", re.split('[?]+', text[3])[1])])
pen = col.OrderedDict([("penalty_apr", APR[3]),
                       ("when_applied", when),
                       ("how_long", length),
                       ("apr_text", text[3])])

#APR
APR = col.OrderedDict([("purchase", purchase),
                       ("balance transfer", BT),
                       ("cash advances", CA),
                       ("penalty (when applicable)", pen)])

#tips
tips = soup.find("div", {"id" : "tipsval"})
tips = col.OrderedDict([("tips", tips.text.strip())])





#scrape data from feestable
fees = list(fees_table.select('div[class*=tableSubBlock]'))
fees_dict = []
#get annual fees since its a bit different
annual_title = fees[0].find('div', {"class" : "annualfee"}).text.strip()
annual_fee = fees[0].select_one('div[class*=val]')
annual_fee = annual_fee.find('b').text.strip()
fee = col.OrderedDict([("fee", annual_fee)])
fees_dict.append((annual_title, annual_fee))

#scrape the rest of the fee table
for i in range(1, len(fees)):
    fee_type = fees[i].find('span').text.strip()
    fee_type_dict =[]
    for fee_number in fees[i].select('div[class*=fee]'):
        value = list(fee_number.find_all('b'))
        value_dict=[]
        for j in range(0, len(value)):
            if '%' in value[j].text:
                value_dict.append(("percent", value[j].text.strip()))
            elif '$' in value[j].text:
                value_dict.append(("dollars", value[j].text.strip()))
            else:
                value_dict.append(("None", "none"))
        value_dict = col.OrderedDict(value_dict)
        fees_text = fee_number.find('div', {"id" : None}).text.strip()
        feei = col.OrderedDict([("fees", value_dict), ("text", fees_text)])
        fee_type_dict.append((fee_number.select_one('div[class*=Label]').text.strip(),
                          feei))
    fee_type_dict = col.OrderedDict(fee_type_dict)
    fees_dict.append((fee_type, fee_type_dict))
fees_dict = col.OrderedDict(fees_dict)


page = col.OrderedDict([("APR/Rates", APR), ("Tips", tips), ("Fees", fees_dict)])




with open("amex.json", "w") as outfile:
    json.dump(page, outfile, indent=4)
