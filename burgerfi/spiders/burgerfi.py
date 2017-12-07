import scrapy
import json
import csv
from scrapy.spiders import Spider
from scrapy.http import FormRequest
from scrapy.http import Request
from scrapy.selector import HtmlXPathSelector
from chainxy.items import ChainItem
import re

class BurgerfiSpider(scrapy.Spider):
    name = "burgerfi"
    search_url = "https://burgerfi.com/find-location/?loc=%s&mil=1000"

    phone_numbers = []
    def __init__(self):
        fp = open('states.json', 'rb')
        self.states = json.loads(fp.read())

    def start_requests(self):
        for state in self.states: 
            url = self.search_url % state["code"]
            yield scrapy.Request(url=url, callback=self.parse_store)

    def parse_store(self, response):
        stores = response.xpath("//div[@class='location-content']")

        for store in stores:
            item = ChainItem()
	    item['store_name'] = "-".join(self.validate(store.xpath(".//div[@class='info']//h3/text()")).split("-")[1:]).strip()
	    item['store_number'] = ""

            info = store.xpath(".//div[@class='info']//p/text()").extract()
	    item['address'] = info[0].strip()
	    item['phone_number'] = info[-1].strip().replace(".", "-")

            if len(info) == 2:
                address = info[0].split(",")
            else:
                address = info[1].split(",")

            try:
	        item['city'] = address[0].strip()

                if len(address) > 4:
                    item["address2"] = address[0].strip()
                    item['city'] = address[1].strip().split(" ")[0]
                    item['state'] = address[2].strip().split(" ")[0]
                else:
                    item['state'] = address[1].strip().split(" ")[0]
            except:
                if len(address[0].strip().split(" ")) > 2:
	            item['address'] = address[0].strip()
	            item['city'] = address[0].strip().split(" ")[-3]
                    item['state'] = address[0].strip().split(" ")[-2]
                else:
                    item['state'] = address[0].strip().split(" ")[0].strip()
                    item['city'] = info[0].split(" ")[-1].strip()

            if item['phone_number'].split("-")[-1].isdigit() == False:
                temp = info[-1].strip().split(",")
                item['city'] = info[1].strip().split(" ")[-2]
                item['state'] = info[1].strip().split(" ")[-1]
                item['phone_number'] = ""
            elif len(item['state']) > 2 and item['state'] != "Texas":
                try:
                    item["address2"] = address[0].strip()
                    item["city"] = address[1].strip()
                    item["state"] = address[2].strip().split(" ")[0]
                except:
                    item['city'] = info[0].split(" ")[-1].strip()
                    item['state'] = info[1].strip().split(" ")[0].replace(".", "")

            try:
	        item['zip_code'] = re.search("\d{5}", "".join(info)).group(0)
            except:
                item['zip_code'] = ""
            
            if len(item["city"]) > 15:
                item["city"] = item["city"].split(" ")[-1]

	    item['country'] = "United States"
	    item['latitude'] = ""
	    item['longitude'] = ""
	    item['store_hours'] = "; ".join(store.xpath("//div[@class='hours']//p/text()").extract()).replace("\r\n", "")
	    item['store_type'] = ""
	    item['other_fields'] = ''
	    item['coming_soon'] = '0'

            item['address'] = item['address'].split(item["city"])[0].strip()

            if item['phone_number'] != "" and item['phone_number'] in self.phone_numbers:
                continue
            self.phone_numbers.append(item['phone_number'])

	    yield item
        
    def validate(self, xpath_obj):
        try:
            return xpath_obj.extract_first().strip()
        except:
            return ""


