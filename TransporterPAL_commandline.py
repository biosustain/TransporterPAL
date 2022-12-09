#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May  5 10:35:58 2022

@author: Jane Dannow Dyekjaer

@contributor: Joel A. V. Madsen

"""
import asyncio
import aiohttp
import sys
import requests
from requests.adapters import HTTPAdapter, Retry
import csv 
import json
import time

retries = Retry(total=5, backoff_factor=0.25, status_forcelist=[500, 502, 503, 504])
session = requests.Session()
session.mount("https://", HTTPAdapter(max_retries=retries)) 
POLLING_INTERVAL=3


contact="your@email.here"
headers ={'User-Agent':'Python {}'.format(contact)}

with open(r"species.v11.5.txt", newline='') as f:
    reader=csv.reader(f, delimiter='\t')
    species = list(reader)
f.close()



#substrate=sys.argv[1]    
#organism=sys.argv[2]
substrate="Insert the substrate"
organism="Insert the organism" 

#Iterate over organisms in species file to retrieve all taxid's
taxid=[]
for line in species[0:][:]:
    if organism in line[2]:
       results=line[0]
       taxid.append(results)


    
enzymes_full=[]

# Search Stich for proteins
stitch_api_url= "https://string-db.org/api"
output_format_stitch = "tsv-no-header"
method_stitch = "interactors"

stitch_proteins=[] 

# Sync call 1 start
step1_time = time.time()

def get_tasks_stitch_interaction_partners(async_session):
    tasks = []
    for i in taxid:
        request_url_stitch = "/".join([stitch_api_url, output_format_stitch, method_stitch])
        params_interaction_partners = {
            "identifiers" : substrate, 
            "species" : str(i), 
            "limit" : 10, 
        }
        tasks.append(async_session.post(request_url_stitch, data=params_interaction_partners, headers=headers, ssl=False))         
    return tasks

async def get_stitch_interaction_partners_responses():
    timeout = aiohttp.ClientTimeout(total=1200) #20min
    async with aiohttp.ClientSession(trust_env=True, timeout=timeout) as async_session:
        tasks = get_tasks_stitch_interaction_partners(async_session)

        batch_size=1000
        for start in range(0, len(tasks), batch_size):
            end= min(len(tasks), start+batch_size)
            tasks_to_run = tasks[start:end]

            responses = await asyncio.gather(*tasks_to_run)
            for response in responses:
                res = await response.text()
                for line in res.strip().split("\n"):
                    l = line.strip().split("\t")
                    stitch_proteins = l[0]
                    enzymes_full.append(stitch_proteins)

# Run event loop
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(asyncio.gather(get_stitch_interaction_partners_responses()))
except:
    sys.exit("Connection to host string-db.org/api stitch failed")


# Sync call 1 end


enzymes=list(set(enzymes_full))

if enzymes == ['Error', 'not found']:
    sys.exit("We didn't find any hits for your query. Please check spelling and check if the organism is in the list. Otherwise try using a synonym for the compound")

#Search STRING for interaction partners
string_api_url_interaction_partners = "https://string-db.org/api"
output_format_interaction_partners = "tsv-no-header"
method_interaction_partners = "interaction_partners"

string_interaction_partners=[]

# Sync call 2 start
step2_time = time.time()

def get_tasks_interaction_partners(async_session):
    tasks = []
    for i in enzymes:
        request_url_interaction_partners = "/".join([string_api_url_interaction_partners, output_format_interaction_partners, method_interaction_partners])
        params_interaction_partners = {
            "identifiers" : str(i), 
            "limit" : 15, 
        }
        tasks.append(async_session.post(request_url_interaction_partners, data=params_interaction_partners, headers=headers, ssl=False))         
    return tasks

async def get_interaction_partners_responses():
    timeout = aiohttp.ClientTimeout(total=1200) #20min
    async with aiohttp.ClientSession(trust_env=True, timeout=timeout) as async_session:
        tasks = get_tasks_interaction_partners(async_session)

        batch_size=1000
        for start in range(0, len(tasks), batch_size):
            end= min(len(tasks), start+batch_size)
            tasks_to_run = tasks[start:end]

            responses = await asyncio.gather(*tasks_to_run)
            for response in responses:
                res = await response.text()
                for line in res.strip().split("\n"):
                    l = line.strip().split("\t")
                    string_interaction_partners_ID = l[1]
                    string_interaction_partners.append(l[1])

# Run event loop
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(asyncio.gather(get_interaction_partners_responses()))
except:
    sys.exit("Connection to host string-db.org/api string failed")



# Sync call 2 end


#get unique interaction partners
interaction_partner_input=list(set(string_interaction_partners+enzymes))


uniprot_entries=[]
count=len(interaction_partner_input)

# Async call 3 start
step3_time = time.time()

def get_tasks_uniprot(async_session):
    tasks = []
    for partner in interaction_partner_input:
        url_uniprot = 'https://rest.uniprot.org/idmapping/run'
        params_uniprot = {"from": "STRING", "to": "UniProtKB", "ids":partner}
        tasks.append(async_session.post(url_uniprot, data=params_uniprot, headers=headers, ssl=False))         
    return tasks

async def fetch(client, job_id):
    async with client.get(f"https://rest.uniprot.org/idmapping/status/{job_id}") as resp:
        #assert resp.status == 200
        if resp.status is not 200:
            sys.exit("Fetch response from uniprot job_id did not return 200")
        return await resp.text()

async def get_uniprot_responses():
    timeout = aiohttp.ClientTimeout(total=1200) #20min
    async with aiohttp.ClientSession(trust_env=True, timeout=timeout) as async_session:
        tasks = get_tasks_uniprot(async_session)

        batch_size=1000
        for start in range(0, len(tasks), batch_size):
            end= min(len(tasks), start+batch_size)
            tasks_to_run = tasks[start:end]

            responses = await asyncio.gather(*tasks_to_run)
                
            for response in responses:
                result = await response.text()
                job_id = json.loads(result)['jobId']

                res = await fetch(async_session, job_id)
                uniprot_entries.append(res)

# Run event loop
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(asyncio.gather(get_uniprot_responses()))
except:
    sys.exit("Connection to host rest.uniprot.org/idmapping failed")


# Async call 3 end

   
#Get entries which contain any of the GO_annotations
    
GO_annotation =["transmembrane transporter activity",
                    "ATP-binding cassette (ABC) transporter complex",
                    "transmembrane transport",
                    "cell outer membrane",
                    "cytoplasmic side of plasma membrane",
                    "integral component of membrane",
                    "integral component of plasma membrane",
                    "integral component of cell outer membrane",
                    "compound transport",
                    "outer membrane",
                    "outer membrane-bounded periplasmic space",
                    "plasma membrane",
                    "porin activity",
                    "response to antibiotic",
                    "symporter activity",
                    "intrinsic component of cell outer membrane",
                    "ion transport",
                    "membrane",
                    "periplasmic space",
                    "ATP binding",
                    "ABC-type transporter activity",
                    "ATPase-coupled transmembrane transporter activity",
                    "efflux transmembrane transporter activity"]
    


GO_filter=[]

for i in uniprot_entries:
    if "GoTerm" in i:
        GO_filter=[item for item in uniprot_entries if any((keyword in item) for keyword in GO_annotation)]



if len(GO_filter)==0:
    sys.exit("I didn't find any hits for your search, try changing compound or organism")

#Get accession numbers from json file
accessions=[]

for i in GO_filter:
    res=json.loads(i)
    for d in res.values():
        x=res['results'][0]['to']['primaryAccession']
        accessions.append(x)


if len(accessions)==0:
    sys.exit("I didnt find any proteins for your query. Try again")

#Retrieve fasta and protein description
entry=[]
fasta=[]


# Sync call 4 start
step4_time = time.time()


# Async get fasta
def get_tasks_fasta(async_session):
    tasks = []
    for i in accessions:
        #url_uniprot = 'https://rest.uniprot.org/uniprotkb/search'
        tasks.append(async_session.get('https://rest.uniprot.org/uniprotkb/search',
            params={
                'query' :  i,
            },
            headers={
                'Accept': 'text/plain; format=fasta',
            },
        ))
    return tasks

async def get_uniprot_fasta_responses():
    timeout = aiohttp.ClientTimeout(total=1200) #20min
    async with aiohttp.ClientSession() as async_session:
        tasks = get_tasks_fasta(async_session)

        batch_size=1000
        for start in range(0, len(tasks), batch_size):
            end= min(len(tasks), start+batch_size)
            tasks_to_run = tasks[start:end]

            responses = await asyncio.gather(*tasks_to_run)
            
            for response in responses:
                fasta.append(await response.text())

# Run event loop
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(asyncio.gather(get_uniprot_fasta_responses()))
except:
    sys.exit("Connection to host rest.uniprot.org failed")
    
# Async get entries
def get_tasks_entry(async_session):
    tasks = []
    for i in accessions:
        #url_uniprot = 'https://rest.uniprot.org/uniprotkb/search'
        tasks.append(async_session.get('https://rest.uniprot.org/uniprotkb/search',
            params={
                'query' :  i,
            },
            headers={
                'Accept': 'text/plain; format=tsv',
            },
        ssl=False))
    return tasks

async def get_uniprot_entry_responses():
    timeout = aiohttp.ClientTimeout(total=1200) #20min
    async with aiohttp.ClientSession(trust_env=True, timeout=timeout) as async_session:
        tasks = get_tasks_entry(async_session)

        batch_size=1000
        for start in range(0, len(tasks), batch_size):
            end= min(len(tasks), start+batch_size)
            tasks_to_run = tasks[start:end]

            responses = await asyncio.gather(*tasks_to_run)
            for response in responses:
                entry.append(await response.text())

# Run event loop
loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(asyncio.gather(get_uniprot_entry_responses()))
except:
    sys.exit("Connection to host rest.uniprot.org/uniprotkb failed")


#Make sure that there is no empty proteins
      
entry = list(filter(None, entry))
get_output=[]
for i in range(len(entry)):
    l=entry[i].split('\t')
    get_output.append(l)

Entry_name=[]
Protein_name=[]
Organism_name=[]
for i in range(len(get_output)):
    Entry_name.append(get_output[i][7])
    Protein_name.append(get_output[i][9]) 
    Organism_name.append(get_output[i][11])





#Fetching TCDB_IDs

TCDB=[]       


count=len(Entry_name)
batch_size=50
for start in range(0,count, batch_size):
    end= min(count, start+batch_size)   
    try:
        for i in Entry_name[start:end]:
            url_uniprot = "https://rest.uniprot.org"
            r=requests.post(f"{url_uniprot}/idmapping/run", data={"from": "UniProtKB_AC-ID", "to": "TCDB", "ids":i}) 
            job_id = r.json()['jobId']
            response_uniprot = requests.get(f"{url_uniprot}/idmapping/status/{job_id}")      
            TCDB.append(json.loads(response_uniprot.text))

    except:
        sys.exit("Connection to host rest.uniprot.org/idmapping failed")

#print(TCDB)

TCDB_IDs=[]
for i in TCDB:
    if len(i)==1:
        for item in i:
            TCDB_IDs.append(i[item][0]['to'])

    else:
        TCDB_IDs.append('-')


#Get the scores
scores_input=[]
for i in accessions:
    scores_input.append(substrate+"%0d"+i)

#print(scores_input)
scores=[]

stitch_api_network= "https://string-db.org/api"
output_api_network = "tsv-no-header"
method_stitch_network = "network"

# Sync call 5 start
step5_time = time.time()


def get_tasks_stitch(async_session):
    tasks = []
    for i in scores_input:
        request_url_stitch_network = "/".join([stitch_api_network, output_api_network, method_stitch_network])
        params_network = {
            "identifiers" : i, 
            "limit" : 10,
        }
        tasks.append(async_session.post(request_url_stitch_network, data=params_network, headers=headers, ssl=False))         
    return tasks

async def get_stitch_responses():
    timeout = aiohttp.ClientTimeout(total=1200) #20min
    async with aiohttp.ClientSession(trust_env=True, timeout=timeout) as async_session:
        tasks = get_tasks_stitch(async_session)

        batch_size=1000
        for start in range(0, len(tasks), batch_size):
            end= min(len(tasks), start+batch_size)
            tasks_to_run = tasks[start:end]

            responses = await asyncio.gather(*tasks_to_run)
            for response in responses:
                res = await response.text()
                scores.append(res.split("\t")[5])

# Run event loop
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(asyncio.gather(get_stitch_responses()))
except:
    sys.exit("Connection to host string-db.org/api network failed")


# Sync call 5 end

#Write output
text_substrate = substrate.strip();
text_organism = organism.strip();
file_names=(text_substrate+"&"+text_organism).replace(" ", "_")
  
with open(file_names + '.fasta','w') as f:
     f.write(''.join(fasta))


header=['Entry name', 'Protein name', 'Organism', 'TCDB', 'Scores']
with open (file_names + '.txt', "w", newline='') as f:
    writer=csv.writer(f, delimiter='\t')
    writer.writerow(header)
    for i in range(len(Entry_name)):
        content=[Entry_name[i], Protein_name[i], Organism_name[i],TCDB_IDs[i], scores[i]]
        writer.writerow(content)
