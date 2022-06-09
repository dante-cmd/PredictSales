from pyparsing import html_comment
from selenium.webdriver.firefox.service import Service
from selenium import webdriver
from lxml.html import fromstring
import re
from urllib.parse import urljoin 
import time
import numpy as np

driver_path = r'C:\dmozilla\geckodriver.exe'
ser = Service(driver_path)
opt = webdriver.FirefoxOptions()

# selenium without opening browser 
opt.add_argument('--headless')

# Create a new instance of the Firefox driver
driver = webdriver.Firefox(service=ser, options=opt)

def DownloadHtml(url):
    
    # Go to the page
    driver.get(url)
    
    # download
    return driver.page_source

def get_links(html, grouped_link, main_link):
    
    all_links = set()
    tree = fromstring(html)
    to_parse_xpath = grouped_link.replace(main_link, '')

    for link in tree.xpath('//a/@href'):
        # print(link )
        # or  re.search(r"/p/.+", link)
        if link and (re.search(rf'.*{to_parse_xpath}.*page.*|.*{to_parse_xpath}.*', link) or  re.search(r"/p/.+", link)):

            link = urljoin(main_link, link)

            link = link.rstrip('/')
            all_links.add(link)

    return all_links

def link_crawler(main_link, grouped_link, minutes=5): # link_regex
    """ Crawl from the given start URL following links matched by link_regex
    """
    crawl_queue = [grouped_link]
    none_type = type(None)
    time_init = time.time()
    critic_time = 30
    seen_intermediate = {grouped_link}
    seen_final = set()
    time_final = time.time()

    while crawl_queue and (time.time() - time_final) < minutes*60:
        index_crawl = np.random.randint(0, len(crawl_queue))
        #index_crawl
        url = crawl_queue.pop(index_crawl)
        html = DownloadHtml(url)
        actual_time = (time.time() - time_init)

        print(len(crawl_queue), end='\r')

        if actual_time < critic_time:

            if not isinstance(html, none_type):
                all_links = get_links(html, grouped_link, main_link)
                if all_links:
                    all_links_remain = all_links.difference(seen_intermediate.union(seen_final))

                    for link in list(all_links_remain):

                        if re.search(rf"({main_link}/p/.+)", link):
                            # crawl_queue.append(link)
                            seen_final.add(link)
                            # print("Ratio Seen/Queve", len(seen_final)/len(crawl_queue), end='\r')
                            # print(link)
                        else :
                            crawl_queue.append(link)
                            seen_intermediate.add(link)
                else:
                    pass


        else:
            print('Sleeping 2 seconds', end='\r')
            time.sleep(2)
            time_init = time.time()

    return seen_final

def isfloat(str):
    try: 
        float(str)
    except ValueError: 
        return False
    return True


def get_data(url):
    # key_dict=tuple(url_dict.keys())[0]
    html_page = DownloadHtml(url)

    tree = fromstring(html_page)
    data = {}
    title = tree.xpath('//h1//span//text()')
    #print(title)
    title = title[0].strip()
    data['title'] = title
    
    list_tag = []
    
    for element in tree.xpath('//main//li//a'):    
        if element.attrib['href']:
            tag_element = re.sub(r'^/c?/?(.*)', r'\1' ,element.attrib['href'])
            if tag_element:
                list_tag.append(tag_element)

    data['tags'] = list_tag
    
    for element in tree.xpath('//div[@class="product-price"]//div[contains(@class,"product-price-container")]//span'): 
        if element.attrib['class'] and re.search('.*price.*|.*discount.*',element.attrib['class']):
            price_descount = element.text.strip()
            price_descount_filter = re.sub(r'(?:S/ (.+)|-\s(\d{1,}).*)', r'\2\1', price_descount)
            data[element.attrib['class']] = float(price_descount_filter)
    
    seller = {}
    for element in tree.xpath('//div[@class="seller-rating-section"]//*'): 
        
        if element.attrib['class']:
            if re.search(".*score.*|.*link\-low\-md.*",element.attrib['class']):
                seller_element = element.text.strip()
                seller_element = float(seller_element) if isfloat(seller_element) else seller_element
                seller.update({element.attrib['class']: seller_element})
                # seller.append({element.attrib['class']: seller_element})
    data['seller']= seller
    return data

from pathlib import Path
import json

def download_data_pages(url):

    path_init = Path()

    if not (path_init / 'DataPages').exists():
        (path_init / 'DataPages').mkdir()
    
    data_page = get_data(url)
    #title_name = data_page['title']
    title_name = np.random.randint(100_000,999_999)
    title_name = str(title_name)

    with open(path_init / 'DataPages' / f'{title_name}.json', 'w') as writer:
            json.dump(data_page, writer)
            print(f'{title_name} was downloaded...', end='\r')