import argparse
from datetime import datetime


import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Qt5Agg')
from pyvis.network import Network
import tkinter as tk
import webbrowser

from PyPDF2 import PdfReader
from refextract import extract_references_from_file


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


    

