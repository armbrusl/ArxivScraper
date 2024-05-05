import argparse
from datetime import datetime
from Scraper import Scraper

if __name__ == "__main__":
    
    defaultR = '18010101_' + str(datetime.now().strftime("%Y%m%d"))
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default = ''       , help = "Queries for the Search on Arxiv (separated by a comma if multiple)"  , type=str)
    parser.add_argument("--range", default = defaultR , help = "The earliest year you want papers from"                              , type=str)
    parser.add_argument("--max"  , default = 0        , help = "The maximum number of publications you want"                         , type=int)
    args = parser.parse_args()

    scr = Scraper(args)
    
    scr.searchArxiv()
    scr.createExcel()
    scr.createDateHistogram()
    scr.cosineSimilarity()
    scr.createAuthorNetwork()


    

