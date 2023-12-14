### An Easy Way to Scrape Scientifc Publications from Arxiv and Visualize their Connectivity


![Alt Text](exampleNetwork.png)


# Installation

### 1. Create a virtual enviroment

```
virtualenv --python=<path_to_python> <enviroment_name>
cd <enviroment_name>
Scripts/activate
```

### 2. Download the requirements

#### Navigate to the cloned GitHub repository and run

```
pip install -r requirements.txt
```

# Usage

```
python main.py --input<inputs_separated_by_commas>(string) --cutoff <earliest_year>(int) --max <max_number_of_articles>(int)
```

#### Example:
```
python main.py --input Physics_Informed_Machine_learning, PINN, PIML --cutoff 2018 --max 100
```
make sure to use "_" instead of a space. Also make sure to include a folder called "papers" in the repository before using it.

# Results
This will create three files and a folder:

1. "Network.html" : Open this file with your browser to see a visual representation of all the papers
   
    **Red Node**     = First Author of atleast one paper <br />
    **Blue Node** = Never the first Author <br />
    **Size of the Node** = the larger means more publication. Hover over the node to see the exact number <br />
    **Thickness of Edge** = the thicker the edge the more recent the publication. Hover over the edge to see the name of the publication/s <br />
   


2. "Overview.xlsx" : To see a summary of all the articles. columns = ['Authors', 'Title', 'Date', 'Summary', 'URL', 'Query']

3. "PublicationFrequency.png" : A histogram of the frequency of articles versus the years.
4. In the doler "papers" you will find all corresponding pdfs.

