from django.shortcuts import render, redirect
from bolsa.utils import queryDB, forexValuesExchange, transformDataToChart


# Home page view
def home(request):
    selected_coin = 'usd'
    if 'selected_coin' in request.session:
        selected_coin = request.session['selected_coin']

    # Reads from the database all companies, their revenue from 2017 and their CEOs
    query = """
    PREFIX pred: <http://wikicompany.pt/pred/>
    SELECT ?companyName ?value ?ceoName ?company ?ceo ?symbol
    WHERE {
        ?company 	pred:revenue	?revnode.
        ?company    pred:symbol     ?symbol.
        ?revnode 	pred:revenueValues	?revSubNode.
        ?revSubNode pred:Year		"2017";
                    pred:Value 		?value.
        ?company	pred:ceo		?ceo.
        OPTIONAL{
        ?ceo        pred:name       ?ceoName.}
        ?company 	pred:name		?companyName.
    }
    """
    res = queryDB(query)
    res = sorted(res, key=lambda x: int(x['value']))
    res = forexValuesExchange(res, "value", selected_coin)
    context = {'lowRevenue': res[:4],
               'highRevenue': res[-4:]
               }
    return render(request, 'pages/home.html', context)


def companies(request):
    queryArgs= ""
    if request.method == "POST":
        #Add sucessive user filter options to query
        if request.POST['searchQuery']:
            queryArgs = queryArgs + "\n filter (contains(lcase(?companyName),lcase(\"{arg}\")) ||  contains(lcase(?companySymbol),lcase(\"{arg}\"))).".format(arg=request.POST['searchQuery'])
        if request.POST['searchIndustry']:
            queryArgs = queryArgs + "\n ?company pred:industry ?companyIndustry.\nfilter contains(lcase(?companyIndustry),lcase(\"{}\")).".format(request.POST['searchIndustry'].lower().replace(" industry", ""))
        if request.POST['searchCEO']:
            queryArgs = queryArgs + "\n ?company pred:ceo ?ceo.\n optional{{?ceo a \"ceo\".\n?ceo pred:name ?ceoName.}} \nfilter( contains(lcase(?ceoName),lcase(\"{arg}\")) || contains(lcase(?ceo),lcase(\"{arg}\")) ).".format(arg=request.POST['searchCEO'])
        if request.POST['searchFounder']:
            queryArgs = queryArgs + "\n ?company pred:foundedBy ?founder.\nfilter contains(lcase(?founder),lcase(\"{}\")).".format(request.POST['searchFounder'])
        if request.POST['searchFoundYear']:
            queryArgs = queryArgs + "\n ?company pred:foundingYear ?foundingYear.\nfilter (?foundingYear = \"{}\").".format(request.POST['searchFoundYear'])
        if request.POST['searchCountry']:
            queryArgs = queryArgs + "\n ?company pred:country ?country.\nfilter contains(lcase(?country),lcase(\"{}\")).".format(request.POST['searchCountry'])
    defaultValues = {}
    collapseDropdown = False
    if request.method == "GET":
        if 'industry' in request.GET:
            defaultValues['industry'] = request.GET['industry']
            collapseDropdown = True
        if 'founder' in request.GET:
            defaultValues['founder'] = request.GET['founder']
            collapseDropdown = True
        if 'foundingYear' in request.GET:
            defaultValues['foundingYear'] = request.GET['foundingYear']
            collapseDropdown = True
        if 'country' in request.GET:
            defaultValues['country'] = request.GET['country']
            collapseDropdown = True
    query = """
    PREFIX pred: <http://wikicompany.pt/pred/>
    SELECT ?company ?companyName ?companySymbol ?companyIndustry
    WHERE {{
        ?company a "company".
        ?company pred:name ?companyName.
        ?company pred:symbol ?companySymbol.
        ?company pred:industry ?companyIndustry.
        {}
    }}
    """.format(queryArgs)
    companies = queryDB(query)
    print(query)
    context = {
        'companies': companies,
        'defaultValues': defaultValues,
        'collapseDropdown': collapseDropdown
    }
    return render(request, 'pages/companies.html', context)


def companiesInfo(request, symbol):
    selected_coin = 'usd'
    if 'selected_coin' in request.session:
        selected_coin = request.session['selected_coin']

    query = """
            PREFIX pred: <http://wikicompany.pt/pred/>
            SELECT ?companyCeo ?companyName ?companySymbol ?companyIndustry ?companyWebsite ?companyWikiRef ?companyFounder ?companyFoundingYear ?companyCountry ?companyDescription ?companyLogo ?ceoName ?revenue ?revenueYear ?revenueValue 
            WHERE {{
                ?company a "company".
                ?company pred:symbol '{s}'.
                ?company pred:name ?companyName.
                ?company pred:industry ?companyIndustry.
                ?company pred:symbol ?companySymbol.
                ?company pred:website ?companyWebsite.
                ?company pred:wikidataRef ?companyWikiRef.
                ?company pred:foundedBy ?companyFounder.
                ?company pred:foundingYear ?companyFoundingYear.
                ?company pred:country ?companyCountry.
                ?company pred:description ?companyDescription.
                ?company pred:logo ?companyLogo.
                ?company pred:ceo ?companyCeo.
                OPTIONAL{{?companyCeo pred:name ?ceoName.}}


            }}
                """.format(s=symbol)

    company = queryDB(query)

    query = """
                PREFIX pred: <http://wikicompany.pt/pred/>
                SELECT ?revenueYear ?revenueValue 
                WHERE {{
                    ?company a "company".
                    ?company pred:symbol '{s}'.
    
                    ?company pred:revenue ?rev.
                    ?rev pred:revenueValues ?revenueValues.
                    ?revenueValues pred:Year ?revenueYear.
                    ?revenueValues pred:Value ?revenueValue.
                    
                }}
                    """.format(s=symbol)

    revenues = queryDB(query)
    if not revenues:
        redirect("/companies/")
    revenues = sorted(revenues, key=lambda x: x['revenueYear'])
    revenues = forexValuesExchange(revenues, 'revenueValue', selected_coin, addSymbol=False)
    #print(company[0])

    context = {'company': company[0],
               'revenues': revenues}

    return render(request, 'pages/companiesInfo.html', context)


def valuesHome(request):
    selected_coin = 'usd'
    if 'selected_coin' in request.session:
        selected_coin = request.session['selected_coin']
    queryArgs = ""
    if request.method == "POST":
        # Add sucessive user filter options to query
        if request.POST['searchQuery']:
            queryArgs = queryArgs + "\n filter (contains(lcase(?companyName),lcase(\"{arg}\")) ||  contains(lcase(?companySymbol),lcase(\"{arg}\"))).".format(
                arg=request.POST['searchQuery'])
        if request.POST['searchIndustry']:
            queryArgs = queryArgs + "\n ?company pred:industry ?companyIndustry.\nfilter contains(lcase(?companyIndustry),lcase(\"{}\")).".format(
                request.POST['searchIndustry'].lower().replace(" industry", ""))
        if request.POST['searchCEO']:
            queryArgs = queryArgs + "\n ?company pred:ceo ?ceo.\n optional{{?ceo a \"ceo\".\n?ceo pred:name ?ceoName.}} \nfilter( contains(lcase(?ceoName),lcase(\"{arg}\")) || contains(lcase(?ceo),lcase(\"{arg}\")) ).".format(
                arg=request.POST['searchCEO'])
        if request.POST['searchFounder']:
            queryArgs = queryArgs + "\n ?company pred:foundedBy ?founder.\nfilter contains(lcase(?founder),lcase(\"{}\")).".format(
                request.POST['searchFounder'])
        if request.POST['searchFoundYear']:
            queryArgs = queryArgs + "\n ?company pred:foundingYear ?foundingYear.\nfilter (?foundingYear = \"{}\").".format(
                request.POST['searchFoundYear'])
        if request.POST['searchCountry']:
            queryArgs = queryArgs + "\n ?company pred:country ?country.\nfilter contains(lcase(?country),lcase(\"{}\")).".format(
                request.POST['searchCountry'])

    query = """
        PREFIX pred: <http://wikicompany.pt/pred/>
        SELECT ?companyName ?revenueYear ?revenueValue
        WHERE {{
            ?company a "company".
            ?company pred:name ?companyName.
            ?company pred:symbol ?companySymbol.
            {}
            ?company pred:revenue ?rev.
            ?rev pred:revenueValues ?revenue.
            ?revenue pred:Year ?revenueYear.
            ?revenue pred:Value ?revenueValue.
        }}
        """.format(queryArgs)
    values = queryDB(query)
    values = forexValuesExchange(values,'revenueValue', selected_coin, addSymbol=False)
    values, years = transformDataToChart(values)
    #print(years)
    context = {
        'values': values,
        'years': years
    }
    return render(request, 'pages/valuesFilter.html', context)


def profile(request):
    if request.user.is_authenticated:
        selected_coin = 'usd'
        if 'selected_coin' in request.session:
            selected_coin = request.session['selected_coin']

        # Get user name
        query = """
                PREFIX pred: <http://wikicompany.pt/pred/>
                SELECT ?userName 
                WHERE {{
                    ?user a "user".
                    ?user pred:idUser "{}".
                    ?user pred:name ?userName.
                }}
                """.format(request.user.id)

        user = queryDB(query)

        # Get user fav companies
        query = """
                PREFIX pred: <http://wikicompany.pt/pred/>
                SELECT distinct ?companyName ?companySymbol ?revenueValue ?company
                WHERE {{
                        ?user a "user".
                        ?user pred:idUser "{}".
                        ?user pred:favCompany ?company.
                        ?company pred:name ?companyName.
                        ?company pred:symbol ?companySymbol.
                        ?company pred:revenue ?rev.
                        optional{{
                			?rev pred:revenueValues ?revenueValues.
                            ?revenueValues pred:Year '2017'.
                            ?revenueValues pred:Value ?revenueValue.
                        }}
                    }}
                """.format(request.user.id)

        companies = queryDB(query)

        # apply metric prefix to rev values
        companies = forexValuesExchange(companies, 'revenueValue', selected_coin)

        # Get user fav CEOs
        query = """
                PREFIX pred: <http://wikicompany.pt/pred/>
                SELECT ?ceoName ?ceoWorth  ?ceoBirth ?ceo
                WHERE {{
                        ?user a "user".
                        ?user pred:idUser "{}".
                        ?user pred:favCeo ?ceo.
                        ?ceo  pred:name ?ceoName.
                        ?ceo  pred:worth ?ceoWorth.
                        ?ceo  pred:birth ?ceoBirth
                }}
                """.format(request.user.id)

        ceos = queryDB(query)

        # apply metric prefix to ceos worth
        number = True
        for ceo in ceos:

            try:
                if ceo['ceoWorth'] == 'Unknown':
                    number = False

            except:
                continue

            if number:
                ceo = forexValuesExchange([ceo], 'ceoWorth', selected_coin)

            number = True

        # Get CEOs suggestion
        query = """
                PREFIX pred: <http://wikicompany.pt/pred/>
                PREFIX user: <http://wikicompany.pt/user/>
                select ?ceoName ?ceoWorth ?ceo
                where{{
                    ?user pred:idUser "{}".
                    ?user pred:favCompany ?company.
                    ?company a "company".
                    ?company pred:ceo ?ceo.
                    ?ceo a "ceo".
                    ?ceo pred:name ?ceoName.
                    ?ceo pred:worth ?ceoWorth.
                    minus{{
                        ?user pred:favCeo ?ceo.
                    }}
                }}
                limit 3
                    """.format(request.user.id)

        ceos_suggestion = queryDB(query)
        # apply metric prefix to ceos worth
        number = True
        for ceo in ceos_suggestion:

            try:
                if ceo['ceoWorth'] == 'Unknown':
                    number = False

            except:
                continue

            if number:
                ceo = forexValuesExchange([ceo], 'ceoWorth', selected_coin)

            number = True

        # Get companies suggestion
        query = """
                PREFIX pred: <http://wikicompany.pt/pred/>
                PREFIX user: <http://wikicompany.pt/user/>
                select ?companyName ?companySymbol  ?company
                where{{
                    ?company a "company".
                    ?company pred:name ?companyName.
                    ?company pred:symbol ?companySymbol.
                    ?company pred:ceo ?ceo.
                    ?user pred:idUser "{}".
                    ?user pred:favCeo ?ceo.
                    ?ceo a "ceo".
                    minus{{
                    ?user pred:favCompany ?company.
                    }}
                }}
                limit 3
                        """.format(request.user.id)

        companies_suggestion = queryDB(query)

        context = {'user':  user[0],
                   'companies': companies,
                   'ceos': ceos,
                   'ceos_suggestion': ceos_suggestion,
                   'companies_suggestion': companies_suggestion
                   }

        return render(request, 'pages/profile.html', context)
    else:
        return redirect('/accounts/login')


def ceos(request):
    queryArgs = ""
    if request.method == "POST":
        # Add sucessive user filter options to query
        if request.POST['searchQuery']:
            queryArgs = queryArgs + "\n filter (contains(lcase(?ceoName),lcase(\"{arg}\"))).".format(
                arg=request.POST['searchQuery'])
        if request.POST['searchSex']:
            queryArgs = queryArgs + "\n ?ceo pred:sex ?ceoSex.\nfilter contains(lcase(?ceoSex),lcase(\"{}\")).".format(
                request.POST['searchSex'])
        if request.POST['searchCountry']:
            queryArgs = queryArgs + "\n ?ceo pred:nationality ?ceoNacionality.\nfilter contains(lcase(?ceoNacionality),lcase(\"{}\")).".format(
                request.POST['searchCountry'])

    defaultValues = {}
    collapseDropdown = False
    if request.method == "GET":
        if 'sex' in request.GET:
            defaultValues['sex'] = request.GET['sex']
            collapseDropdown = True
        if 'nationality' in request.GET:
            defaultValues['nationality'] = request.GET['nationality']
            collapseDropdown = True

    query = """
        PREFIX pred: <http://wikicompany.pt/pred/>
        SELECT ?ceo ?ceoName ?ceoSex ?ceoBirth
        WHERE {{
            ?ceo a "ceo".
            ?ceo pred:name  ?ceoName.
            ?ceo pred:sex   ?ceoSex.
            ?ceo pred:birth ?ceoBirth.
            {}
        }}
        """.format(queryArgs)
    ceos = queryDB(query)
    context = {
        'ceos': ceos,
        'defaultValues': defaultValues,
        'collapseDropdown': collapseDropdown
    }

    return render(request, 'pages/ceos.html', context)

def ceosinfo(request, name):
    selected_coin = 'usd'
    if 'selected_coin' in request.session:
        selected_coin = request.session['selected_coin']

    query = """
                PREFIX pred: <http://wikicompany.pt/pred/>
                SELECT ?ceoName ?ceoPhoto ?ceoSex ?ceoBirth ?ceoWorth ?ceoDescription ?ceoNationality ?companyName ?companySymbol ?ceoWiki ?ceo
                WHERE {{
                        {{
                                ?ceo a "ceo".
                                ?ceo pred:name '{x}'.
                                ?ceo pred:name ?ceoName.
                                ?ceo pred:photo ?ceoPhoto.
                                ?ceo pred:sex ?ceoSex.
                                ?ceo pred:birth ?ceoBirth.
                                ?ceo pred:worth ?ceoWorth.
                                ?ceo pred:description ?ceoDescription.
                                ?ceo pred:wikidataRef ?ceoWiki.
                
                            }}
                        UNION
                        {{
                				?ceo a "ceo".
                                ?ceo pred:name '{x}'.
                                 ?ceo pred:nationality ?ceoNationality.
                            }}
                        UNION{{
                				?ceo a "ceo".
                                ?ceo pred:name '{x}'.
                                ?company a "company".
                                ?company pred:name ?companyName.
                                ?company pred:symbol ?companySymbol.
                                ?company pred:ceo ?ceo
                                
                            }}
                    }}
                    """.format(x=name)

    ceo = queryDB(query)
    if not ceo:
        redirect("/ceos/")
    number = True
    for itm in ceo:
        try:
            if itm['ceoWorth']=='Unknown':
                number = False

        except:
            continue

    if number:
        ceo = forexValuesExchange(ceo, 'ceoWorth', selected_coin)

    nationalities = []
    companies = []

    for itm in ceo[1:]:
        try:
            if itm['ceoNationality']:
                nationalities.append(itm)
        except:
            try:
                if itm['companySymbol']:
                    companies.append(itm)
            except:
                continue

    context = {'ceo': ceo[0],
               'nationalities': nationalities,
               'companies': companies}

    return render(request, 'pages/ceosinfo.html', context)

def seefull(request, type ):
    if request.user.is_authenticated:
        selected_coin = 'usd'
        if 'selected_coin' in request.session:
            selected_coin = request.session['selected_coin']

        # Get user name
        query = """
                        PREFIX pred: <http://wikicompany.pt/pred/> 
                        SELECT ?userName 
                        WHERE {{
                            ?user a "user".
                            ?user pred:idUser "{}".
                            ?user pred:name ?userName.
                        }}
                        """.format(request.user.id)

        user = queryDB(query)

        if type == "companies":

            # Get user fav companies
            query = """
                    PREFIX pred: <http://wikicompany.pt/pred/>
                    SELECT distinct ?companyName ?companySymbol ?revenueValue  ?company
                    WHERE {{
                            ?user a "user".
                            ?user pred:idUser "{}".
                            ?user pred:favCompany ?company.
                            ?company pred:name ?companyName.
                            ?company pred:symbol ?companySymbol.
                            ?company pred:revenue ?rev.
                            optional{{
                                ?rev pred:revenueValues ?revenueValues.
                                ?revenueValues pred:Year '2017'.
                                ?revenueValues pred:Value ?revenueValue.
                            }}
                        }}
                    """.format(request.user.id)

            items = queryDB(query)

            # apply metric prefix to rev values
            items = forexValuesExchange(items, 'revenueValue', selected_coin)

            # Get companies suggestion
            query = """
                            PREFIX pred: <http://wikicompany.pt/pred/>
                            PREFIX user: <http://wikicompany.pt/user/>
                            select ?companyName ?companySymbol  ?company
                            where{{
                                ?company a "company".
                                ?company pred:name ?companyName.
                                ?company pred:symbol ?companySymbol.
                                ?company pred:ceo ?ceo.
                                ?user pred:idUser "{}".
                                ?user pred:favCeo ?ceo.
                                ?ceo a "ceo".
                                minus{{
                                ?user pred:favCompany ?company.
                                }}
                            }}
                                    """.format(request.user.id)

            suggestions = queryDB(query)

        else:
            # Get user fav CEOs
            query = """
                    PREFIX pred: <http://wikicompany.pt/pred/>
                    SELECT ?ceoName ?ceoWorth  ?ceoBirth ?ceo
                    WHERE {{
                            ?user a "user".
                            ?user pred:idUser "{}".
                            ?user pred:favCeo ?ceo.
                            ?ceo  pred:name ?ceoName.
                            ?ceo  pred:worth ?ceoWorth.
                            ?ceo  pred:birth ?ceoBirth
                    }}
                    """.format(request.user.id)

            items = queryDB(query)

            # apply metric prefix to ceos worth
            number = True
            for ceo in items:

                try:
                    if ceo['ceoWorth'] == 'Unknown':
                        number = False

                except:
                    continue

                if number:
                    ceo = forexValuesExchange([ceo], 'ceoWorth', selected_coin)

                number = True

            # Get CEOs suggestion
            query = """
                    PREFIX pred: <http://wikicompany.pt/pred/>
                    PREFIX user: <http://wikicompany.pt/user/>
                    select ?ceoName ?ceoWorth ?ceo
                    where{{
                        ?user pred:idUser "{}".
                        ?user pred:favCompany ?company.
                        ?company a "company".
                        ?company pred:ceo ?ceo.
                        ?ceo a "ceo".
                        ?ceo pred:name ?ceoName.
                        ?ceo pred:worth ?ceoWorth.
                        minus{{
                            ?user pred:favCeo ?ceo.
                        }}
                    }}
                        """.format(request.user.id)

            suggestions = queryDB(query)
            # apply metric prefix to ceos worth
            number = True
            for ceo in suggestions:

                try:
                    if ceo['ceoWorth'] == 'Unknown':
                        number = False

                except:
                    continue

                if number:
                    ceo = forexValuesExchange([ceo], 'ceoWorth', selected_coin)

                number = True


        context = {'user': user[0],
                   'type': type,
                   'items': items,
                   'suggestions': suggestions
                   }

        return render(request, 'pages/seefull.html', context)
    else:
        return redirect('/accounts/login')
