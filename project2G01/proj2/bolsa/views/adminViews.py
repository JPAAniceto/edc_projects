from django.shortcuts import render, HttpResponse, redirect
from bolsa.utils import getWikidataCompany, transformRevenue, queryDB, getCompanyFromDB, getWikidataCEO, getCEOfromDB, transformCEONat, coinExists, queryWikidata, coinSymbol
import requests


def adminMain(request):
    if request.user.is_superuser:
        context = {}
        return render(request, 'pages/admin/main.html', context)
    return redirect("/")


def adminAddCompany(request):
    if request.user.is_superuser:
        defaultValues = {}
        message = ""
        companySearchMessage = ""
        success = False
        showForm = False
        if request.method == 'POST':
            # Get items from request
            valuesToAdd = dict(request.POST)
            valuesToAdd.pop('csrfmiddlewaretoken')
            valuesToAdd.pop('action')
            # Get items out of lists
            for key in valuesToAdd:
                valuesToAdd[key] = valuesToAdd[key][0]
            # Deal with revenues
            revenueQuery = transformRevenue(valuesToAdd['companyRevenues'])
            if revenueQuery is None:
                message = "Revenue Values are incorrectly formatted"
            else: # If revenue is correctly formatted
                # Fill blank values
                for key in valuesToAdd:
                    if valuesToAdd[key] == "":
                        valuesToAdd[key] = "Unknown"
                # Check if CEO is in DB
                query = """
                PREFIX pred: <http://wikicompany.pt/pred/>
                PREFIX user: <http://wikicompany.pt/user/>
                SELECT ?ceo 
                WHERE {{
                    ?ceo a "ceo".
                    ?ceo pred:name "{}".
                }}
                """.format(valuesToAdd['companyCeo'])
                res = queryDB(query)
                if res:
                    ceo = '<' + res[0]['ceo'] + ">"
                else:
                    ceo = "\"" + valuesToAdd['companyCeo'] + "\""
                # Add company to DB
                query = """
                    PREFIX pred: <http://wikicompany.pt/pred/>
                    PREFIX company: <http://wikicompany.pt/companies/>
                    DELETE {{
                        company:{symbol} ?a ?b
                    }}
                    WHERE {{
                        company:{symbol} ?a ?b
                    }};
                    INSERT DATA{{
                        company:{symbol} pred:name "{name}".
                        company:{symbol} pred:symbol "{symbolUpper}".
                        company:{symbol} pred:website "{website}".
                        company:{symbol} pred:wikidataRef "{wikidataRef}".
                        company:{symbol} pred:revenue  [{revenue}].
                        company:{symbol} pred:industry "{industry}".
                        company:{symbol} pred:ceo {ceo}.
                        company:{symbol} pred:foundedBy "{founder}".
                        company:{symbol} pred:foundingYear "{fYear}".
                        company:{symbol} pred:country "{country}".
                        company:{symbol} pred:description "{description}".
                        company:{symbol} pred:logo "{logo}".
                        company:{symbol} a "company".
                    }}
                """.format(symbol=valuesToAdd['companySymbol'].lower(), name=valuesToAdd['companyName'], symbolUpper=valuesToAdd['companySymbol'].upper()
                           , website=valuesToAdd['companyWebsite'], wikidataRef=valuesToAdd['companyWikidataRef'], revenue=revenueQuery,
                           industry=valuesToAdd['companyIndustry'], ceo=ceo, founder=valuesToAdd['companyFounder'], fYear=valuesToAdd['companyFoundingYear']
                           , country=valuesToAdd['companyCountry'], description=valuesToAdd['companyDescription'], logo=valuesToAdd['companyLogo'])
                queryDB(query, update=True, simplify=False)
                success = True
        if 'companySymbol' in request.GET:
            # Get Data from Wikidata and set default Values
            defaultValues['symbol'] = request.GET['companySymbol']
            if getCompanyFromDB(request.GET['companySymbol']):
                companySearchMessage = "Company Already exists"
            else:
                fields = getWikidataCompany(request.GET['companySymbol'])
                showForm = True
                if fields:
                    defaultValues = {**defaultValues, **fields}
                else:
                    companySearchMessage = "Company not found in Wikidata"
        context = {
            'defaultValues': defaultValues,
            'companySearchMessage': companySearchMessage,
            'showForm': showForm,
            'message': message,
            'success': success
        }
        return render(request, 'pages/admin/addCompany.html', context)
    return redirect("/")

def adminEditCompany(request):
    if request.user.is_superuser:
        defaultValues = {}
        message = ""
        success = False
        foundCompany = False
        if request.method == 'POST':
            # Get items from request
            valuesToAdd = dict(request.POST)
            valuesToAdd.pop('csrfmiddlewaretoken')
            valuesToAdd.pop('action')
            # Get items out of lists
            for key in valuesToAdd:
                valuesToAdd[key] = valuesToAdd[key][0]
            # Deal with revenues
            revenueQuery = transformRevenue(valuesToAdd['companyRevenues'])
            if revenueQuery is None:
                message = "Revenue Values are incorrectly formatted"
            else: # If revenue is correctly formatted
                # Fill blank values
                for key in valuesToAdd:
                    if valuesToAdd[key] == "":
                        valuesToAdd[key] = "Unknown"
                # Check if CEO is in DB
                query = """
                PREFIX pred: <http://wikicompany.pt/pred/>
                PREFIX user: <http://wikicompany.pt/user/>
                SELECT ?ceo 
                WHERE {{
                    ?ceo a "ceo".
                    ?ceo pred:name "{}".
                }}
                """.format(valuesToAdd['companyCeo'])
                res = queryDB(query)
                if res:
                    ceo = res[0]['ceo']
                else:
                    ceo = "\"" + valuesToAdd['companyCeo'] + "\""
                # Add company to DB
                query = """
                    PREFIX pred: <http://wikicompany.pt/pred/>
                    PREFIX company: <http://wikicompany.pt/companies/>
                    DELETE {{
                        company:{symbol} ?a ?b
                    }}
                    WHERE {{
                        company:{symbol} ?a ?b
                    }};
                    INSERT DATA{{
                        company:{symbol} pred:name "{name}".
                        company:{symbol} pred:symbol "{symbolUpper}".
                        company:{symbol} pred:website "{website}".
                        company:{symbol} pred:wikidataRef "{wikidataRef}".
                        company:{symbol} pred:revenue  [{revenue}].
                        company:{symbol} pred:industry "{industry}".
                        company:{symbol} pred:ceo {ceo}.
                        company:{symbol} pred:foundedBy "{founder}".
                        company:{symbol} pred:foundingYear "{fYear}".
                        company:{symbol} pred:country "{country}".
                        company:{symbol} pred:description "{description}".
                        company:{symbol} pred:logo "{logo}".
                        company:{symbol} a "company".
                    }}
                """.format(symbol=valuesToAdd['companySymbol'].lower(), name=valuesToAdd['companyName'], symbolUpper=valuesToAdd['companySymbol'].upper()
                           , website=valuesToAdd['companyWebsite'], wikidataRef=valuesToAdd['companyWikidataRef'], revenue=revenueQuery,
                           industry=valuesToAdd['companyIndustry'], ceo=ceo, founder=valuesToAdd['companyFounder'], fYear=valuesToAdd['companyFoundingYear']
                           , country=valuesToAdd['companyCountry'], description=valuesToAdd['companyDescription'], logo=valuesToAdd['companyLogo'])
                queryDB(query, update=True, simplify=False)
                success = True
        if 'companySymbol' in request.GET:
            # Get Data from DB and set default Values
            defaultValues['symbol'] = request.GET['companySymbol']
            fields = getCompanyFromDB(request.GET['companySymbol'])
            if fields:
                defaultValues = {**defaultValues, **fields}
        context = {
            'defaultValues': defaultValues,
            'message': message,
            'success': success,
        }
        return render(request, 'pages/admin/editCompany.html', context)
    return redirect("/")

def adminDeleteCompany(request):
    if request.user.is_superuser:
        companySymbol = ""
        companyName = ""
        message = ""
        success = False
        foundCompany = False
        if request.method == 'POST':
            # Delete company
            query = """
            PREFIX pred: <http://wikicompany.pt/pred/>
            PREFIX company: <http://wikicompany.pt/companies/>
            DELETE {{
                ?user pred:favCompany ?company.
            }}
            WHERE {{
                ?company a "company".
                ?company pred:symbol "{code}".
                ?user pred:favCompany ?company.
            }};
            DELETE {{
                ?company ?a ?b.
            }}
            WHERE {{
                ?company a "company".
                ?company pred:symbol "{code}".
                ?company ?a ?b.
            }};
            """.format(code=request.POST['companySymbol'].upper())
            queryDB(query, simplify=False, update=True)
            message = "Company Deleted"
        elif 'companySymbol' in request.GET:
            # Get Data from Wikidata and set default Values
            fields = getCompanyFromDB(request.GET['companySymbol'])
            if fields:
                companySymbol = request.GET['companySymbol']
                companyName = fields['name']
        context = {
            'companySymbol': companySymbol,
            'companyName': companyName,
            'message': message,
            'success': success,
        }
        return render(request, 'pages/admin/deleteCompany.html', context)
    return redirect("/")


def adminAddCEO(request):
    if request.user.is_superuser:
        defaultValues = {}
        message = ""
        searchMessage = ""
        success = False
        showForm = False
        if request.method == 'POST':
            # Get items from request
            valuesToAdd = dict(request.POST)
            valuesToAdd.pop('csrfmiddlewaretoken')
            valuesToAdd.pop('action')
            # Get items out of lists
            for key in valuesToAdd:
                valuesToAdd[key] = valuesToAdd[key][0]
            # Deal with nationalities
            code = valuesToAdd['ceoName'].lower().replace(" ","_")
            natQuery = transformCEONat(valuesToAdd['ceoNationality'], code)
            # Fill blank values
            for key in valuesToAdd:
                if valuesToAdd[key] == "":
                    valuesToAdd[key] = "Unknown"
            # Add CEO to DB
            query = """
                PREFIX pred: <http://wikicompany.pt/pred/>
                PREFIX ceo: <http://wikicompany.pt/ceo/>
                DELETE {{
                    ceo:{code} ?a ?b.
                }}
                WHERE {{
                    ceo:{code} ?a ?b.
                }};
                INSERT DATA{{
                    ceo:{code} pred:name "{name}".
                    ceo:{code} pred:photo "{logo}".
                    ceo:{code} pred:description "{description}".
                    ceo:{code} pred:sex "{sex}".
                    {nat}
                    ceo:{code} pred:birth "{birth}".
                    ceo:{code} pred:worth "{worth}".
                    ceo:{code} pred:wikidataRef "{wiki}".
                    ceo:{code} a "ceo".
                }}
            """.format(code=code, name=valuesToAdd['ceoName'], logo=valuesToAdd['ceoLogo'],
                       description=valuesToAdd['ceoDescription'], sex=valuesToAdd['ceoSex'],
                       birth=valuesToAdd['ceoBirth'], worth=valuesToAdd['ceoWorth'],
                       wiki=valuesToAdd['ceoWikidataRef'], nat=natQuery)
            queryDB(query, update=True, simplify=False)
            success = True
            # Check if CEO of Companies
            query = """
               PREFIX pred: <http://wikicompany.pt/pred/>
               PREFIX company: <http://wikicompany.pt/companies/>
               INSERT{{
                 ?company pred:ceo ?ceo. 
               }}
               WHERE {{
                   ?company a "company".
                   ?company pred:ceo "{name}".
                   ?ceo a "ceo".
                   ?ceo pred:name "{name}".
               }};
               DELETE{{
                 ?company pred:ceo "{name}". 
               }}
               WHERE {{
                   ?company a "company".
               }};
               """.format(name=valuesToAdd['ceoName'])
            queryDB(query, simplify=False, update=True)
        if 'ceoName' in request.GET:
            # Get Data from Wikidata and set default Values
            if getCEOfromDB(request.GET['ceoName']):
                searchMessage = "Ceo Already exists"
            else:
                fields = getWikidataCEO(request.GET['ceoName'])
                showForm = True
                if fields:
                    defaultValues = {**defaultValues, **fields}
                else:
                    searchMessage = "CEO not found in Wikidata"
        context = {
            'defaultValues': defaultValues,
            'searchMessage': searchMessage,
            'showForm': showForm,
            'message': message,
            'success': success
        }
        return render(request, 'pages/admin/addCEO.html', context)
    return redirect("/")

def adminEditCEO(request):
    if request.user.is_superuser:
        defaultValues = {}
        message = ""
        searchMessage = ""
        success = False
        showForm = False
        if request.method == 'POST':
            # Get items from request
            valuesToAdd = dict(request.POST)
            valuesToAdd.pop('csrfmiddlewaretoken')
            valuesToAdd.pop('action')
            # Get items out of lists
            for key in valuesToAdd:
                valuesToAdd[key] = valuesToAdd[key][0]
            # Deal with nationalities
            code = valuesToAdd['ceoName'].lower().replace(" ","_")
            natQuery = transformCEONat(valuesToAdd['ceoNationality'], code)
            # Fill blank values
            for key in valuesToAdd:
                if valuesToAdd[key] == "":
                    valuesToAdd[key] = "Unknown"
            # Add CEO to DB
            query = """
                PREFIX pred: <http://wikicompany.pt/pred/>
                PREFIX ceo: <http://wikicompany.pt/ceo/>
                DELETE {{
                    ceo:{code} ?a ?b.
                }}
                WHERE {{
                    ceo:{code} ?a ?b.
                }};
                INSERT DATA{{
                    ceo:{code} pred:name "{name}".
                    ceo:{code} pred:photo "{logo}".
                    ceo:{code} pred:description "{description}".
                    ceo:{code} pred:sex "{sex}".
                    {nat}
                    ceo:{code} pred:birth "{birth}".
                    ceo:{code} pred:worth "{worth}".
                    ceo:{code} pred:wikidataRef "{wiki}".
                    ceo:{code} a "ceo".
                }}
            """.format(code=code, name=valuesToAdd['ceoName'], logo=valuesToAdd['ceoLogo'],
                       description=valuesToAdd['ceoDescription'], sex=valuesToAdd['ceoSex'],
                       birth=valuesToAdd['ceoBirth'], worth=valuesToAdd['ceoWorth'],
                       wiki=valuesToAdd['ceoWikidataRef'], nat=natQuery)
            queryDB(query, update=True, simplify=False)
            success = True
            # Check if CEO of Companies
            query = """
               PREFIX pred: <http://wikicompany.pt/pred/>
               PREFIX company: <http://wikicompany.pt/companies/>
               INSERT{{
                 ?company pred:ceo ?ceo. 
               }}
               WHERE {{
                   ?company a "company".
                   ?company pred:ceo "{name}".
                   ?ceo a "ceo".
                   ?ceo pred:name "{name}".
               }};
               DELETE{{
                 ?company pred:ceo "{name}". 
               }}
               WHERE {{
                   ?company a "company".
               }};
               """.format(name=valuesToAdd['ceoName'])
            queryDB(query, simplify=False, update=True)
        if 'ceoName' in request.GET:
            # Get Data from Wikidata and set default Values
            fields = getCEOfromDB(request.GET['ceoName'])
            if fields:
                defaultValues = {**defaultValues, **fields}
                showForm = True
                searchMessage = defaultValues['name']
            else:
                searchMessage = "CEO not in DB"
        context = {
            'defaultValues': defaultValues,
            'searchMessage': searchMessage,
            'showForm': showForm,
            'message': message,
            'success': success
        }
        return render(request, 'pages/admin/editCEO.html', context)
    return redirect("/")


def adminDeleteCEO(request):
    if request.user.is_superuser:
        ceoName = ""
        message = ""
        showForm = True
        success = False
        foundCompany = False
        if request.method == 'POST':
            # Check if ceo is associated to a company
            query = """
            PREFIX pred: <http://wikicompany.pt/pred/>
           PREFIX company: <http://wikicompany.pt/companies/>
            INSERT{{
             ?company pred:ceo "{name}". 
           }}
           WHERE {{
               ?company a "company".
               ?company pred:ceo ?ceo.
               ?ceo a "ceo".
               ?ceo pred:name "{name}"
           }};
           DELETE{{
             ?company pred:ceo ?ceo. 
           }}
           WHERE {{
               ?company a "company".
               ?company pred:ceo ?ceo.
               ?ceo a "ceo".
               ?ceo pred:name "{name}".
           }};
            """.format(name=request.POST['ceoName'])
            queryDB(query, simplify=False, update=True)
            # Delete CEO from DB
            query = """
               PREFIX pred: <http://wikicompany.pt/pred/>
               PREFIX company: <http://wikicompany.pt/companies/>
               DELETE {{
                   ?user pred:favCeo ?ceo.
               }}
               WHERE {{
                   ?ceo a "ceo".
                   ?ceo pred:name "{}".
                   ?user pred:favCeo ?ceo.
               }};
               DELETE {{
                   ?ceo ?a ?b.
               }}
               WHERE {{
                   ?ceo a "ceo".
                   ?ceo pred:name "{}".
                   ?ceo ?a ?b.
               }};                    
               """.format(request.POST['ceoName'], request.POST['ceoName'])
            queryDB(query, simplify=False, update=True)
            message = "CEO Deleted"
        elif 'ceoName' in request.GET:
            # Get Data from Wikidata and set default Values
            fields = getCEOfromDB(request.GET['ceoName'])
            if fields:
                ceoName = request.GET['ceoName']
                showForm = True
        context = {
            'ceoName': ceoName,
            'showForm': showForm,
            'message': message,
            'success': success,
        }
        return render(request, 'pages/admin/deleteCEO.html', context)
    return redirect("/")


def adminAddCoin(request):
    if request.user.is_superuser:
        message = ""
        success = ""
        coinSymbol = ""
        if request.method == 'POST':
            coin = request.POST['code']
            if coinExists(coin):
                # Get symbol from Wikidata
                query= """
                SELECT ?symbol
                WHERE {{
                  ?coin wdt:P498 "{}".
                  ?coin wdt:P5061 ?symbol.
                  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
                }}
                """.format(coin.upper())
                res = queryWikidata(query)
                if not res:
                    message = "Couldn't find symbol on wikidata"
                coinSymbol = res[0]['symbol']
                query ="""
                PREFIX pred: <http://wikicompany.pt/pred/>
                PREFIX coin: <http://wikicompany.pt/coin/>
                INSERT DATA{{
                    coin:{code} pred:coinCode "{code}".
                    coin:{code} pred:coinSymbol "{symbol}".
                    coin:{code} a "coin".
                }}
                """.format(code=coin.lower(), symbol=coinSymbol)
                success = "Coin added"
                queryDB(query, simplify=False, update=True)
            else:
                message = "Coin not supported :("
        context = {
            'coinSymbol': coinSymbol,
            'message': message,
            'success': success
        }
        return render(request, 'pages/admin/addCoin.html', context)
    return redirect("/")


def adminDeleteCoin(request):
    if request.user.is_superuser:
        message = ""
        success = ""
        image = ""
        symbol = ""
        if request.method == 'POST':
            coin = request.POST['code']
            symbol = coinSymbol(coin)
            if coin.lower() == "usd":
                image = "https://media.giphy.com/media/xUPGcl3ijl0vAEyIDK/giphy.gif"
            elif symbol:
                query = """
                   PREFIX pred: <http://wikicompany.pt/pred/>
                   PREFIX coin: <http://wikicompany.pt/coin/>
                   DELETE {{
                       coin:{code} ?s ?o.
                   }}
                   WHERE {{
                       coin:{code} ?s ?o.
                   }}
                   """.format(code=coin.lower())
                success = "Coin Deleted"
                queryDB(query, simplify=False, update=True)
            else:
                message = "Coin not in DB currently"
        context = {
            'coinSymbol': symbol,
            'message': message,
            'success': success,
            'image': image
        }
        return render(request, 'pages/admin/deleteCoin.html', context)
    return redirect("/")

def adminExportDB(request):
    headerParams = {"Accept": "text/n3"}
    url = 'http://localhost:7200/repositories/bolsa/statements'
    response = requests.get(url, headers=headerParams)
    export = HttpResponse(response.text, content_type='text/rdf+n3')
    export['Content-Disposition'] = 'attachment; filename="export.n3"'
    return export
