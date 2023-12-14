import pandas as pd
import arxiv
import re
import os
from os.path import exists
import argparse

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Qt5Agg')
from pyvis.network import Network

from PyPDF2 import PdfReader
from refextract import extract_references_from_file

client = arxiv.Client()


def flatten_extend(matrix):
    flat_list = []
    for row in matrix:
        flat_list.extend(row)
    return flat_list

def splitAuthornames(names):
    newNames = []
    for name in names:
        nameSeparated = name.split()
        newname = nameSeparated.pop(1)
        newNames.append(newname)

    return ', '.join(newNames[:3])

def check_file(fullfile):
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

def SearchArxiv(queries, nresults, cutoffDate):
    all_data = []
    names_list = []
    title_list = []
    references = []
    counter = 0
    for query in queries:

        search = arxiv.Search(
            query = query,
            max_results = int(nresults / len(queries)),
            sort_by = arxiv.SortCriterion.Relevance,
            sort_order = arxiv.SortOrder.Descending
        )
        
        results = client.results(search)
        
        for result in results:
            
            temp = ["","","","","",""]
            names = re.findall(r"'(.*?)'", str(result.authors))
            
            #temp[0] = splitAuthornames(names)
            temp[0] = names
            temp[1] = result.title
            temp[2] = result.published.date()
            temp[3] = result.summary
            temp[4] = result.pdf_url
            temp[5] = query

            print(temp[2])
            if(int(str(temp[2])[:4]) > cutoffDate and title_list.count(temp[1]) <= 0):
                
                filename = "papers/" + "".join(x for x in temp[1] if x.isalnum() or x == " " or x== "-") + ".pdf"
                
                if(exists(filename) == False):
                    result.download_pdf(filename=filename)
                
                    if check_file(filename):
                                            
                        title_list.append(temp[1])
                        all_data.append(temp)
                        names_list.append(names)
                        references.append(extract_references_from_file(filename))
                        
                        print("Saved ", str(counter) + " : ", temp[1])
                        counter += 1
                    else:
                        print("Corrupted File Deleted: ", filename)
                        os.remove(filename)
                
                else:
                    print("File already exists - no download - :" + "Saved ", str(counter) + " : ", temp[1])                  
                    title_list.append(temp[1])
                    all_data.append(temp)
                    names_list.append(names)
                    references.append(extract_references_from_file(filename))
                    counter += 1
                        
                
                
    return all_data, names_list, title_list, references

def createAuthorNetwork(names_list, title_list, df, cutoffDate, wf):

    # Create a graph
    G = nx.Graph()

    # Add edges between names within the same list
    
    flattened_list = flatten_extend(names_list)
    for names in names_list:
        c = 0
        for name in names:
            count = flattened_list.count(name)
            if(G.has_node(name) == False):
                if(c==0): # First author
                    G.add_node(name, size= 5 + count**2, color='red', title = str(count), hover = str(count), label=name)
                    c += 1
                else:
                    if(c == 0):
                        G.add_node(name, size= 5 + count**2, color='red', title = str(count), hover = str(count), label=name)
                    else:
                        G.add_node(name, size= 5 + count**2, color='Blue', title = str(count), hover = str(count), label=name)
    
    for names, title_, PublishDate in zip(names_list, title_list, list(df.Date)):
        weighingFactor = ((int(str(PublishDate)[:4]) - cutoffDate + 1)**wf) / 2
        edgeLabel = str(PublishDate) + " : " + title_
        
        for i in range(len(names) - 1):

            if(G.has_edge(names[i], names[i + 1]) == False):

                G.add_edge(names[i],names[i + 1], color='black', weight=weighingFactor, hover= edgeLabel, title = edgeLabel)  # Connect names in the list
            else: # adds to the title if the authors shar multiple papers

                oldTitle = G.edges[names[i],names[i + 1]]['title']
                oldweight = G.edges[names[i],names[i + 1]]['weight']
                new_label = oldTitle + " -|- " + edgeLabel
                new_weight = (oldweight + weighingFactor)/2
                G.edges[names[i], names[i + 1]]['title'] = new_label
                G.edges[names[i], names[i + 1]]['hover'] = new_label
                G.edges[names[i], names[i + 1]]['weight'] = new_weight
                
        G.add_edge(names[0], names[len(names) - 1], color='black', weight=weighingFactor, hover=edgeLabel, title=edgeLabel)

    #net = Network(width = "1920px", height = "1080px", notebook = False, cdn_resources='remote', directed=False)
    net = Network(width = "1920px", height = "1080px", directed=False)
    net.from_nx(G)
    
    net.toggle_physics(True)
    #net.show_buttons(filter_=['physics'])
    net.save_graph("Network.html")   
    
def createDateHistogram(dates):

    # Create a histogram of dates
    plt.figure(figsize=(10, 6))
    plt.hist(dates, bins=60, edgecolor='black')  # Adjust the number of bins as needed
    plt.xlabel('Date')
    plt.ylabel('Frequency')
    plt.title('Histogram of Dates')
    plt.xticks(rotation=45)  # Rotate x-axis labels for better readability
    plt.tight_layout()
    plt.savefig("PublicationFrequency.png")


def main(input, cutoffDate, maxNumberOfPapers):
    
    queries = [f"abs:{query} AND ti:{query}" for query in input]

    print(queries, cutoffDate, maxNumberOfPapers)

    all_data, names_list, title_list, references = SearchArxiv(queries, maxNumberOfPapers, cutoffDate)


    df = pd.DataFrame(all_data, columns = ['Authors', 'Title', 'Date', 'Summary', 'URL', 'Query']) 
    df = df.sort_values('Date', ascending=False)
    df.to_excel("Overview.xlsx")

    createAuthorNetwork(names_list, title_list, df, cutoffDate, 0.5)
    createDateHistogram(list(df.Date))
    
    
    
    
    
if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  help="Queries for the Search on Arxiv (separated by a comma if multiple)"   , type=str)
    parser.add_argument("--cutoff", help="The earliest year you want papers from"                               , type=int)
    parser.add_argument("--max",    help="The maximum number of publications you want"                          , type=int)
    args = parser.parse_args()
    
    queries = args.input.replace("_", " ").split(",")

    main(queries, args.cutoff, args.max)