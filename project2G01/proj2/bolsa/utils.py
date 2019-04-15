import json
from s4api.graphdb_api import GraphDBApi
from s4api.swagger import ApiClient
import requests
import datetime
import calendar

# Runs a given query in the bolsa database and returns its results
def queryDB(query, simplify=True, update=False):
    endpoint = "http://localhost:7200"
    repo_name = "bolsa"
    client = ApiClient(endpoint=endpoint)
    accessor = GraphDBApi(client)
    if not update:
        payload_query = {"query": query}
        res = accessor.sparql_select(body=payload_query,
                                 repo_name=repo_name)
    else:
        payload_query = {"update": query}
        res = accessor.sparql_update(body=payload_query,
                                     repo_name=repo_name)
    # If true returns a workable version of the query results
    if simplify:
        res = transformResults(res)
    return res

# Transforms a dictionary in json format to a more flexible format
def transformResults(result):
    res = json.loads(result)
    vars = []
    final_res=[]
    for e in res['head']['vars']:
        vars.append(e)
    for e in res['results']['bindings']:
        temp = {}
        for v in vars:
            try:
                temp[v] = e[v]['value']
            except:
                pass
        final_res.append(temp)
    return final_res

# Converts all relevant values in the input array, to the selected coin
def forexValuesExchange(input, var, coinCode, addSymbol=True):
    coin_v = coinValue(coinCode)     # Coin value in reference to USD
    coin_s = coinSymbol(coinCode)    # Coin symbol
    for e in input:
        # If it finds a key equal to var in the dictionary e its corresponding item will be a number,
        # the number will be formatted in accordance to the Metric Prefixes ex: 1000 -> 1,000
        try:
            if addSymbol:
                number = "{:,}".format(round(int(e[var]) * coin_v, 2))
                e[var] = number + coin_s
            else:
                e[var] = round(int(e[var]) * coin_v, 2)
        except:
            continue

    return input

# Returns the value of a coin in reference with USD
def coinValue(code):
    if code is 'usd':
        return 1
    coin_pair = "USD{}".format(str.upper(code))
    url = "https://www.freeforexapi.com/api/live?pairs={}".format(coin_pair)
    r = requests.get(url)
    response = r.json()
    if 'code' in response:
        if response['code'] is 200:
            return response['rates'][coin_pair]['rate']
    return 1

# Checks if we can get rates of a coin
def coinExists(code):
    if code is 'usd':
        return True
    coin_pair = "USD{}".format(str.upper(code))
    url = "https://www.freeforexapi.com/api/live?pairs={}".format(coin_pair)
    r = requests.get(url)
    response = r.json()
    if 'code' in response:
        if response['code'] is 200:
            return True
    return False

# Given the code of a coin, a query to the database is made that returns its symbol
def coinSymbol(code):
    if not code:
        return "$"
    query = """
    PREFIX pred: <http://wikicompany.pt/pred/>
    PREFIX coin: <http://wikicompany.pt/coin/>
    SELECT ?symbol
    WHERE {{
        ?coin pred:coinCode '{}'.
        ?coin pred:coinSymbol ?symbol.
    }}
    """.format(code)
    symbol = queryDB(query)[0]['symbol']
    return symbol

# A query to the database is made that returns all coins symbols and codes
def coins():
    coins = []
    query = """
        PREFIX pred: <http://wikicompany.pt/pred/>
        PREFIX coin: <http://wikicompany.pt/coin/>
        SELECT ?code ?symbol
        WHERE {
            ?coin pred:coinCode ?code.
            ?coin pred:coinSymbol ?symbol.
        }
        """
    coins = queryDB(query)
    return coins

# Transforms data from the query used in valuesFilter to usable data in the chart
def transformDataToChart(values):
    years = set()
    companies = set()
    graphData = {}
    for v in values:
        years.add(v['revenueYear'])
        graphData.setdefault(v['companyName'], []).append((v['revenueYear'], v['revenueValue']))
    years = sorted(years, key=float)
    for key in graphData:
        for year in years:
            if year not in [x[0] for x in graphData[key]]:
                graphData[key].append((year, 0))
        graphData[key] = sorted(graphData[key], key=lambda x: x[0])
    return graphData,years

# Check the result of a ask query
def checkAskQuery(result):
    res = json.loads(result)
    if not res['boolean']:
        return False
    else:
        return True

# Get Wikidata Info for a company
def getWikidataCompany(symbol):
    # Search company in Wikidata
    query ="""
    SELECT DISTINCT ?id ?idLabel ?idDescription
    WHERE {{
    ?id wdt:P414 ?exchange .
    ?id p:P414 ?exchangeSub .
    ?exchangeSub pq:P249 '{}' . 
    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
    }}
    """.format(symbol.upper())
    res = queryWikidata(query)
    if not res:
        return []
    companyId = res[0]['id'].split("/")[-1]
    # Get fields of company
    fields = {}
    fields['name'] = res[0]['idLabel']
    fields['description'] = res[0]['idDescription']
    fields['symbol'] = symbol
    fields['wikidataRef'] = companyId
    query="""
    SELECT ?industryLabel ?website ?ceoLabel ?founderLabel ?foundingYear ?countryLabel ?logo
    WHERE{{
       OPTIONAL {{ wd:{id} wdt:P452 ?industry.}}
       OPTIONAL {{ wd:{id} wdt:P856 ?website.}}
       OPTIONAL {{ wd:{id} wdt:P169 ?ceo.}}
       OPTIONAL {{ wd:{id} wdt:P112 ?founder.}}
       OPTIONAL {{ wd:{id} wdt:P571 ?foundingYear.}}
       OPTIONAL {{ wd:{id} wdt:P17 ?country.}}
       OPTIONAL {{ wd:{id} wdt:P154 ?logo.}}
       SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
    }}
    LIMIT 1
    """.format(id=companyId)
    res = queryWikidata(query)
    res = res[0]
    fields = {**res, **fields}
    # Get Revenues of company
    query = """
    SELECT ?revValue ?revYear
    WHERE{{
        wd:{} p:P2139 ?stat.
        ?stat ps:P2139 ?revValue;
        pq:P585 ?revYear.
    }}
    """.format(companyId)
    res = queryWikidata(query)
    if not res:
        return []
    #Transform Years
    for a in res:
        a['revYear'] = datetime.datetime.fromisoformat(a['revYear'].replace('Z','')).year
    fields['revenue'] = res
    return fields

# Query Wikidata using POST
def queryWikidata(query, simplify=True):
    url = "https://query.wikidata.org/sparql"
    headers = {
        "Accept": "application/sparql-results+json "
    }
    data = {
        "query": query
    }
    result = requests.post(url, headers=headers, data=data)
    if simplify:
        result = transformResults(result.text)
    return result

# Transform revenue Values from the form textarea to query form
def transformRevenue(string):
    values = string.replace("\r", "").replace("\n", "").replace(" ", "").split(";")
    revenueQuery = ""
    if values[-1] == '':
        values = values[:-1]
    try:
        for entry in values:
            values = entry.split(",")
            revenueQuery = revenueQuery + "pred:revenueValues [pred:Year \"{}\";pred:Value \"{}\"];".format(values[1],values[0])
    except:
        revenueQuery = None
    return revenueQuery

# Get a company from DB and all its data
def getCompanyFromDB(symbol):
    #get company Info
    fields = {}
    query="""
    PREFIX pred: <http://wikicompany.pt/pred/>
    PREFIX company: <http://wikicompany.pt/companies/>
    SELECT ?industryLabel ?website ?ceoLabel ?ceoName ?founderLabel ?foundingYear ?countryLabel ?logo ?description ?name ?wikidataRef
    WHERE{{
        ?company a "company".
       ?company pred:symbol "{}".
       ?company pred:name ?name.
       ?company pred:industry ?industryLabel.
       ?company pred:website ?website.
       ?company pred:ceo ?ceoLabel.
       ?company pred:foundedBy ?founderLabel.
       ?company pred:foundingYear ?foundingYear.
       ?company pred:country ?countryLabel.
       ?company pred:logo ?logo.
       ?company pred:description ?description.
       ?company pred:wikidataRef ?wikidataRef.
       OPTIONAL{{?ceoLabel pred:name ?ceoName.}}
       }}
    """.format(symbol.upper())
    info = queryDB(query)
    if not info:
        return []
    info = info[0]
    fields = {**info, **fields}
    #Get company revenue
    query = """
    PREFIX pred: <http://wikicompany.pt/pred/>
    PREFIX company: <http://wikicompany.pt/companies/>
    SELECT ?revValue ?revYear
    WHERE{{
        ?company a "company".
        ?company pred:symbol "{}".
        ?company pred:revenue ?rev.
        ?rev pred:revenueValues ?revenue.
        ?revenue pred:Year ?revYear.
        ?revenue pred:Value ?revValue.
    }}
    """.format(symbol.upper())
    info = queryDB(query)
    if not info:
        return []
    fields['revenue'] = info
    return fields

# Get Wikidata Info for a CEO
def getWikidataCEO(name):
    fields = {}
    ceoRef = ""
    # Get all possible ceos from wikidata
    query ="""
    SELECT DISTINCT ?id ?idLabel ?idDescription
    WHERE {
      {
      ?company wdt:P414 ?exchange .
      ?company wdt:P169 ?id.
      ?id wdt:P735 ?firstNameItem.
      ?id wdt:P734 ?lastNameItem.
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
      
      }
      UNION {
         ?id wdt:P31 wd:Q5.
         ?id p:P39 ?subItem.
         ?subItem ps:p39 wd:Q484876.
         ?subItem pq:P642 ?company.
         ?company wdt:P414 ?exchange .
       }
    }
    """
    res = queryWikidata(query)
    for entry in res:
        if name in entry['idLabel']:
            ceoRef = entry['id'].split("/")[-1]
            fields['name'] = entry['idLabel']
            fields['description'] = entry['idDescription']
            fields['wikidataRef'] = entry['id'].split("/")[-1]
            break
    if not ceoRef:
        return []
    # Return information from Wikidata
    query ="""
    SELECT ?image ?sexLabel ?birth ?worth
    WHERE {{
      OPTIONAL {{wd:{id} wdt:P18 ?image. }}
      OPTIONAL {{wd:{id} wdt:P21 ?sex.}}
      OPTIONAL {{wd:{id} wdt:P569 ?birth.}}
      OPTIONAL {{wd:{id} wdt:P2218 ?worth.}}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
    }}
    """.format(id=ceoRef)
    res = queryWikidata(query)
    fields = {**res[0], **fields}
    birth = datetime.datetime.fromisoformat(fields['birth'].replace('Z', ''))
    fields['birth'] = calendar.month_name[birth.month] + " " + str(birth.year)
    query = """
    SELECT ?nationalityLabel
    WHERE {{
      OPTIONAL {{wd:{} wdt:P27 ?nationality. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
    }}
    """.format(ceoRef)
    res = queryWikidata(query)
    nationalities = []
    for a in res:
        nationalities.append(a['nationalityLabel'])
    fields['nationality'] = nationalities
    return fields

# Transform CEO nationalities into query form
def transformCEONat(string, id):
    values = string.split(",")
    query = ""
    if values[-1] == '':
        values = values[:-1]
    for entry in values:
        query = query + "ceo:{} pred:nationality \"{}\".".format(id, entry)
    return query


# Get Ceo from DB
def getCEOfromDB(name):
    fields = {}
    # Return information from Wikidata
    query = """
        PREFIX pred: <http://wikicompany.pt/pred/>
        SELECT ?image ?sexLabel ?birth ?worth ?description ?wikidataRef
        WHERE {{
          ?ceo a "ceo".
          ?ceo pred:name "{}".
          OPTIONAL {{?ceo pred:photo ?image. }}
          OPTIONAL {{?ceo pred:sex ?sexLabel.}}
          OPTIONAL {{?ceo pred:birth ?birth.}}
          OPTIONAL {{?ceo pred:worth ?worth.}}
          OPTIONAL {{?ceo pred:description ?description.}}
          OPTIONAL {{?ceo pred:wikidataRef ?wikidataRef.}}
        }}
        """.format(name)
    res = queryDB(query)
    if not res:
        return {}
    fields['name'] = name
    fields = {**res[0], **fields}
    query = """
        PREFIX pred: <http://wikicompany.pt/pred/>
        SELECT ?nationalityLabel
        WHERE {{
          ?ceo a "ceo".
          ?ceo pred:name "{}".
          OPTIONAL {{?ceo pred:nationality ?nationalityLabel. }}
        }}
        """.format(name)
    res = queryDB(query)
    nationalities = []
    for a in res:
        nationalities.append(a['nationalityLabel'])
    fields['nationality'] = nationalities
    return fields

