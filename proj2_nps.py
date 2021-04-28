#################################
##### Name: Eva Zenilman
##### Uniqname: ezenilma
#################################

from bs4 import BeautifulSoup
import requests
import json
import time
import secrets 

CACHE_FILENAME = 'nps_cache.json'
CACHE_DICT = {}

baseurl = 'https://www.nps.gov'

key = secrets.CONSUMER_KEY
secret_key = secrets.CONSUMER_SECRET_KEY

def load_cache():
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache

def save_cache(cache):
    cache_file = open(CACHE_FILENAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

def make_url_request_using_cache(url, cache):
    if url in cache.keys(): # the url is our unique key
        print("Using Cache")
        return cache[url]
    else:
        print("Fetching")
        time.sleep(1)
        response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone
    
    def info(self):
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"

def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    # response = requests.get(baseurl).text
    response = make_url_request_using_cache(baseurl, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')
    searchbar = soup.find('ul', class_='dropdown-menu SearchBar-keywordSearch')
    state_nps = {}
    a_level = searchbar.find_all('a')
    for state in a_level:
        state_nps[state.text.lower()] = baseurl + state.get("href")

    return state_nps

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    # response = requests.get(site_url).text
    response = make_url_request_using_cache(site_url, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')

    # Get the category and name
    hero = soup.find('div', class_='Hero-titleContainer clearfix')

    hero_category = hero.find('span', class_="Hero-designation")
    category = hero_category.text.strip()

    hero_name = hero.find('a')
    name = hero_name.text.strip()

    # Get the address, zip code, and phone
    footer = soup.find('div', class_ = 'ParkFooter-contact')

    footer_locality = footer.find('span', itemprop='addressLocality')
    footer_region = footer.find('span', itemprop='addressRegion')
    locality = footer_locality.text.strip()
    region = footer_region.text.strip()
    address = locality + ', ' + region

    footer_zip = footer.find('span', itemprop='postalCode')
    zipcode = footer_zip.text.strip()

    footer_phone = footer.find('span', itemprop='telephone')
    phone = footer_phone.text.strip()

    nationalsite = NationalSite(category, name, address, zipcode, phone)
    return nationalsite

def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    ## Make soup for state page
    # response = requests.get(state_url).text
    response = make_url_request_using_cache(state_url, CACHE_DICT)
    soup = BeautifulSoup(response, 'html.parser')

    ## For each national site listed
    state_site_parent = soup.find('ul', id='list_parks')
    state_site_lis = state_site_parent.find_all('li', class_='clearfix')
    count = 1
    state_sites = []
    sites_print = []
    for state_site_li in state_site_lis:

        ## extract url
        site_link_tag = state_site_li.find('h3')
        state_site_tag = site_link_tag.find('a')
        state_site_path = state_site_tag['href']
        state_site_url = baseurl + state_site_path

        ## append site instance to list
        state_site = get_site_instance(state_site_url)
        state_sites.append(state_site)

    return state_sites

def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    map_api = "http://www.mapquestapi.com/search/v2/radius"
    origin = site_object.zipcode

    # implementing caching
    cache = load_cache()
    if origin in cache:
        print("Using Cache")
    else:
        print("Fetching")
        params = {
            'key': key,
            'origin': origin,
            'radius': 10,
            'maxMatches': 10,
            'ambiguities': 'ignore',
            'outformat': 'json'
        }
        response = requests.get(map_api, params).json()
        cache[origin] = response
        save_cache(cache)

    response = cache[origin]
    place_data = response["searchResults"]
    for place in place_data:
        name = place['name']
        fields = place['fields']
        category = fields['group_sic_code_name_ext']
        address = fields['address']
        city = fields['city']

        if category == '':
            category = 'no category'
        else:
            category = category

        if address == '':
            address = 'no address'
        else:
            address = address

        if city == '':
            city = 'no city'
        else:
            city = city

        print('- ' + name + ' (' + category + '): ' + address + ', ' + city)

    return response

CACHE_DICT = load_cache()

# site_instance = get_site_instance("https://www.nps.gov/isro/index.htm")
# # print(site_instance.name)
# nearby_places = get_nearby_places(site_instance)

if __name__ == "__main__":

    state_dict = build_state_url_dict()

    # User asked to enter a state name
    inp = input("Enter a state name (e.g. Michigan, michigan) or 'exit': ")
    while inp.lower() != 'exit':

        # if the state name is valid
        if inp.lower() in state_dict.keys():
            state_url = state_dict[inp.lower()]
            state_sites = get_sites_for_state(state_url)
            print('----------------------------------------')
            print(f"List of national sites in {inp.lower()}")
            print('----------------------------------------')
            count=1
            for site in state_sites:
                print('['+str(count)+'] ' + site.info())
                count+=1

            # User asked if they want more detail
            inp = input("Choose the number for detail search or 'exit' or 'back': ")

            #if they have requested more detail
            while inp.isnumeric():
                if int(inp) in range(0, len(state_sites)):
                    ind = int(inp) - 1
                    request = state_sites[ind]
                    print('----------------------------------------')
                    print(f"Places near {request.name}")
                    print('----------------------------------------')
                    get_nearby_places(request)
                    inp = input("Choose the number for detail search or 'exit' or 'back': ")
                else:
                    print('invalid input')
                    inp = input("Choose the number for detail search or 'exit' or 'back': ")

            #if they have chosed to go back
            if inp.lower() == 'back':
                inp = input("Enter a state name (e.g. Michigan, michigan) or 'exit': ")

        #if the state name is not valid
        else:
            print('wrong name')
            inp = input("Enter a state name (e.g. Michigan, michigan) or 'exit': ")

