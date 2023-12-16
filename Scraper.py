import pandas as pd
import arxiv
import re
import os
from os.path import exists
import os
from datetime import datetime
import numpy as np

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Qt5Agg')
from pyvis.network import Network
import webbrowser

from PyPDF2 import PdfReader
from refextract import extract_references_from_file

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class Scraper():
    
    def __init__(self, args):
        
        queries      = [f"abs:{query} AND ti:{query}" for query in args.input.replace("_", " ").split(",")]
        dates = args.range.split("_")

        if len(dates) == 1:
            dates.append(datetime.now().strftime("%Y%m%d"))
        
        self.queries        = queries
        self.earliestDate   = datetime.strptime(dates[0], '%Y%m%d').date()
        self.latestDate     = datetime.strptime(dates[1], '%Y%m%d').date()
        self.maxPapers      = args.max
        
        self.foldername     = self.createDirectory()
        self.allData = {'authors' :[], 'title':[], 'date':[], 'summary':[], 'url':[], 'query':[], 'references':[]}
        
        print("Queries: "      , self.queries)
        print("Earliest Date: ", self.earliestDate)
        print("Latest Date: "  , self.latestDate)
        print("Max Papers: "   , self.maxPapers, "\n")

    def createDirectory(self):
        # Get current date and time
        current_datetime = datetime.now()
        date_time_str = current_datetime.strftime("%Y%m%d_%H%M%S")  # Format: YYYY-MM-DD_HH-MM-SS

        # Create a folder based on current date and time
        folder_name = "search" + date_time_str
        os.mkdir(folder_name)

        # Create 'papers' and 'references' folders within the newly created folder
        papers_folder = os.path.join(folder_name, 'papers')
        references_folder = os.path.join(folder_name, 'references')

        os.mkdir(papers_folder)
        os.mkdir(references_folder)

        print("Successfully Created the Directory", "\n")
        
        return folder_name

    def checkDownloadability(self, fullfile):
        
        with open(fullfile, 'rb') as f:
            try:
                pdf = PdfReader(f)
                info = pdf.metadata
                if info:
                    return True
                else:
                    return False
            except Exception as e:
                return False

    def createExcel(self):
        df = pd.DataFrame(self.allData) 
        df.to_excel(self.foldername + "/Overview.xlsx", index=False)
        print("Done Creating Excel Sheet")
        
        return df

    def saveCurrentPaper(self, temp):
        
        self.allData['authors'].append(temp[0])
        self.allData['title'].append(temp[1])
        self.allData['date'].append(temp[2])
        self.allData['summary'].append(temp[3])
        self.allData['url'].append(temp[4])
        self.allData['query'].append(temp[5])
        self.allData['references'].append(temp[6])
        
        print("Saved: (" + str(temp[2]) + ") " + temp[1])
              
    def searchArxiv(self):
        print("Ingesting Found Publications")
        for query in self.queries:

            search = arxiv.Search(
                query = query,
                max_results = int(self.maxPapers / len(self.queries)),
                sort_by = arxiv.SortCriterion.Relevance,
                sort_order = arxiv.SortOrder.Descending
            )
            
            client = arxiv.Client()
            
            for result in client.results(search):
                
                temp = ["", "", "", "", "", "", ""]
                
                temp[0] = re.findall(r"'(.*?)'", str(result.authors))
                temp[1] = result.title
                temp[2] = result.published.date()
                temp[3] = result.summary
                temp[4] = result.pdf_url
                temp[5] = query
                	
                if self.earliestDate < temp[2] < self.latestDate and self.allData['title'].count(temp[1]) == 0:

                    cleanedTitle = self.foldername + "/papers/" + "".join(x for x in temp[1] if x.isalnum() or x == " " or x== "-") + ".pdf"
                    
                    if exists(cleanedTitle) == False:
                        
                        result.download_pdf(filename = cleanedTitle)

                        if self.checkDownloadability(cleanedTitle):             
                            temp[6] = extract_references_from_file(cleanedTitle)
                            self.saveCurrentPaper(temp)
                        else:
                            print("Corrupted File Deleted: (" + str(temp[2]) + ") " + temp[1])
                            #os.remove(cleanedTitle)
                    else:
                        temp[6] = extract_references_from_file(cleanedTitle)               
                        self.saveCurrentPaper(temp)

        print("Done Analyzing Results", "\n")

    def createAuthorNetwork(self):
        
        G = nx.Graph()
        for names in self.allData['authors']:
            c = 0
            for name in names:
                count = sum(x.count(name) for x in self.allData['authors'])
                sizeNode =  5 + count**2
                if G.has_node(name) == False:
                    if c == 0 : # First author
                        G.add_node(name, size = sizeNode, color='red', title = str(count), hover = str(count), label = name)
                        c += 1
                    else: # Non-First author
                        G.add_node(name, size = sizeNode, color='Blue', title = str(count), hover = str(count), label = name)
        
        for names, _title, date in zip(self.allData['authors'], self.allData['title'], self.allData['date']):
            
            weightEdge  = ((date - self.earliestDate).days / (self.latestDate - self.earliestDate).days) * 10
            labelEdge   = str(date) + " : " + _title
            
            # Adding the edges between all authors except first and last
            for i in range(len(names) - 1):

                # If the edge does not already exist simply add the edge. If it does already exist make cahnges to the edge label and weight
                if G.has_edge(names[i], names[i + 1]) == False : 
                    G.add_edge(names[i], names[i + 1], color = 'black', weight = weightEdge, hover = labelEdge, title = labelEdge) 
                else: 
                    oldTitle   = G.edges[names[i], names[i + 1]]['title']
                    oldweight  = G.edges[names[i], names[i + 1]]['weight']
                    
                    new_label  = oldTitle + " -|- " + labelEdge
                    new_weight = (oldweight + weightEdge)/2
                    
                    G.edges[names[i], names[i + 1]]['title']  = new_label
                    G.edges[names[i], names[i + 1]]['hover']  = new_label
                    G.edges[names[i], names[i + 1]]['weight'] = new_weight
            
            # Adding the edge between the first and last author     
            G.add_edge(names[0], names[len(names) - 1], color='black', weight = weightEdge, hover = labelEdge, title = labelEdge)

        net = Network(width = "1920px", height = "1080px", directed=False)
        net.from_nx(G)
        net.toggle_physics(True)
        net.save_graph(self.foldername + "/Network.html") 
        print("Done Creating Network Plot. Redirecting to Browser (carefull with Safari).")
        webbrowser.open_new(os.path.abspath(self.foldername + "/Network.html"))
           
    def createDateHistogram(self):
        nBins = int(abs(((self.latestDate - self.earliestDate).days)) / 365.25 * 12) # Adjust the number of bins based on the search window
        
        # Create a histogram of dates
        plt.figure(figsize=(10, 6))
        plt.hist(self.allData['date'], bins = nBins, edgecolor = 'black')  
        plt.xlabel('Date')
        plt.ylabel('Frequency')
        plt.title('Histogram of Dates')
        plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
        plt.tight_layout()
        plt.savefig(self.foldername + "/PublicationFrequency.png")
        print("Done Creating Histogram Plot")

    
    def cosineSimilarity(self):
        # Create TF-IDF vectorizer
        print("Begin Analyzing Similarities")
        vectorizer = TfidfVectorizer(stop_words='english')
        
        if len(self.allData['summary']) != 0:
            tfidf_matrix = vectorizer.fit_transform(self.allData['summary'])

            # Compute cosine similarity between all pairs of abstracts
            similarities = cosine_similarity(tfidf_matrix, tfidf_matrix)

            # Print the similarity matrix
            print("Done Analyzing Similarities")
            np.save(self.foldername + "/similarities.npy", similarities)
            
            plt.figure(figsize=(20, 20))
            plt.imshow(similarities)
            plt.colorbar()
            plt.savefig(self.foldername + "/similarities.png")
        else:
            print("Not Enough Data to Make Similarity Calculations")