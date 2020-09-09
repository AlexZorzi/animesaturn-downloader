# importing the requests library 
import requests,os,subprocess
import sys
import signal
from bs4 import BeautifulSoup
import re
from datetime import datetime
import locale
import time
import concurrent.futures

#config
download_path = "/share/Plex/ANIME/"
crawl_path = "/Users/edoardo/Documents/GitHub/animesaturn-downloader/"
leng = True #solo anime in italiano (utile per gli anime doppiati, es: SAO)
all = True #anime correlati
#

only_link = list()
list_link = list()
correlati_list = list()
anime = {}
all_ep = {}
titolo = ""
season = 0
season_num = 0


def create_crawl_fixed():
    crwd = ""
    for link in list_link:
        crwd = crwd + '''
        {
        text= %s
        downloadFolder= %s%s/Season_%s
        enabled= true
        autoStart= true
        autoConfirm= true
        }
        '''%(link,download_path,titolo,all_ep[link])
    with open("%s%s.crawljob"%(crawl_path,titolo), 'a') as f:
        f.write(crwd)
        f.close()
    list_link.clear()

def create_crawl():
    print("ep number: %d"%len(list_link))
    crwd = ""
    for link in list_link:
        crwd = crwd + '''
        {
        text= %s
        downloadFolder= %s%s/Season_%d
        enabled= true
        autoStart= true
        autoConfirm= true
        }
        '''%(link,download_path,titolo,season_num)
    with open("%s%s.crawljob"%(crawl_path,titolo), 'a') as f:
        f.write(crwd)
        f.close()
    list_link.clear()
def reorder_correlati():
    global titolo
    for URL in correlati_list:
        new_r = requests.get(url = URL, params = {})
        pastebin_url = new_r.text 
        parsed_html = BeautifulSoup(pastebin_url,"html.parser")
        anno = parsed_html.find('div', attrs={'class':'container shadow rounded bg-dark-as-box mb-3 p-3 w-100 text-white'})
        release = re.findall("(?<=<b>Data di uscita:</b> )(.*)(?=<br/>)",str(anno))
        anime[release[0]] = URL
    locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')
    ordered_data = sorted(anime.items(), key = lambda x:datetime.strptime(x[0], "%d %B %Y"), reverse=False)
    titolo = re.findall("(?<=anime/)(.*)", ordered_data[0][1])[0]
    for x in ordered_data:
        only_link.append(x[1])
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(only_link)) as pool:
        results = pool.map(selected_anime, only_link)

def sig_handler(_signo, _stack_frame):
    print("\n")
    sys.exit(0)
def get_correlati(URL):
    is_lang = "-ITA" in URL #controlla se il link supporta la lingua ita
    #analizzo url e cerco la sezione "correlati" e richiamo la funzione per trovare gli episodi per gonuno di essi
    new_r = requests.get(url = URL, params = {})
    pastebin_url = new_r.text 
    parsed_html = BeautifulSoup(pastebin_url,"html.parser")
    correlati = parsed_html.find_all('div', attrs={'class':'owl-item anime-card-newanime main-anime-card'})
    correlati_list.append(URL)
    for dim in correlati:
        anime = dim.find('a')['href']
        if(leng and is_lang):
            if("-ITA" in anime):
                correlati_list.append(anime)
        else: correlati_list.append(anime)
    reorder_correlati()

def one_link(ep):
    x = ep.split("§")
    new_r = requests.get(url = x[0], params = {})
    pastebin_url = new_r.text
    parsed_html = BeautifulSoup(pastebin_url,"html.parser")
    anime_page = parsed_html.find('div', attrs={'class':'card bg-dark-as-box-shadow text-white'})
    is_link = anime_page.find('a')['href']
    if 'watch' in is_link: 
        episode = is_link+'&s=alt'
    all_ep[episode] = x[1]
    list_link.append(episode)

def selected_anime(URL):
    global season
    global season_num
    ep_list = list()
    #visito la pagina, trovo il tasto per l'episodio. Sucessivamente analizzo quella  pagina e ottengo il link di streaming
    new_r = requests.get(url = URL, params = {})
    pastebin_url = new_r.text 
    parsed_html = BeautifulSoup(pastebin_url,"html.parser")
    all_info = parsed_html.find('div', attrs={'class':'container shadow rounded bg-dark-as-box mb-3 p-3 w-100 text-white'})
    info = re.findall("(?<=<b>Episodi:</b> )(.*)(?=<br/>)",str(all_info))
    anime_type = anime_page = parsed_html.find('span', attrs={'class':'badge badge-secondary'})
    if ('OVA' in anime_type.text or "Special" in info[0] or "Movie" in info[0]): 
        season_num = 0
    else: 
        season +=1
        season_num = season
    print(season_num)
    anime_ep = parsed_html.find_all('div', attrs={'class':'btn-group episodes-button episodi-link-button'})
    list_link.clear()
    for dim in anime_ep:
        episode = dim.find('a')['href']
        episode = episode +"§%d"%season_num
        #print(episode)
        ep_list.append(episode)
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(ep_list)) as pool:
        results = pool.map(one_link, ep_list)
    ep_list.clear()
    #get_link(anime_ep)
def main():
    global season
    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)
    anime_list  = list()
    name = input("nome:")
    #name = "dxd"
    URL = "https://www.animesaturn.com/animelist?search="+name
    r = requests.get(url = URL, params = {})
    pastebin_url = r.text 
    html = pastebin_url
    parsed_html = BeautifulSoup(html,"html.parser")
    animes = parsed_html.find_all('ul', attrs={'class':'list-group'})
    x = 1
    for dim in animes:
        print(x)
        print("TITOLO:")
        title = dim.find('a',attrs={'class':'badge badge-archivio badge-light'})
        trama = dim.find('p',attrs={'class':'trama-anime-archivio text-white rounded'})
        link = dim.find('a')['href']
        print("\x1b[32m" + title.text + "\x1b[0m")
        print("TRAMA:")
        print("\x1b[37m" + trama.text +"\x1b[0m")
        anime_list.append(link)
        print("--------")
        x+=1
    selected = int(input("ID:"))
    #selected = 2
    selected -=1 #la lista parte da 0
    URL = anime_list[selected]
    if(all):
        get_correlati(URL)
    else:
        season = 1
        selected_anime(URL)
    create_crawl_fixed()

if __name__ == "__main__":
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))