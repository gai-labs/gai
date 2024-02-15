from gai.tools.Scraper import Scraper
from gai.common.logging import getLogger
logger = getLogger(__name__)

class Googler:

    @staticmethod
    def google(search_query, n_results=10, period=None):
        results = []
        links=[]
        try:
            scraper=Scraper()
            period="d"
            #GOOGLE_SEARCH = f"https://www.google.com/search?q={search_query}&tbs=qdr:{period}"
            GOOGLE_SEARCH = f"https://www.google.com/search?q={search_query}"
            text,links = scraper.scrape(GOOGLE_SEARCH)
        except Exception as e:
            logger.error('Googler.google: Failed to extract links. error=',e)

        try:
            #Scrape top n search results
            dict_items = list(links.items())
            for key, value in dict_items:
                if (value.startswith("https://www.google.com/url?q=")):
                    value = value.split("https://www.google.com/url?q=")[1].split("&sa=U&")[0]
                    if (value.startswith("https://accounts.google.com")):
                        continue
                    if (value.startswith("https://support.google.com")):
                        continue
                    if (value.startswith("https://maps.google.com")):
                        continue
                    if (value.startswith("/search")):
                        continue
                    results.append({"title":key,"url":value})
                    
            return results
        except Exception as e:
            logger.error('Googler.google: error=',e)
