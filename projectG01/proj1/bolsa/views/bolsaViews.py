from django.shortcuts import render, HttpResponse
import urllib.request
import xmltodict
from lxml import etree
import os

from BaseXClient import BaseXClient

from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect

from bolsa.forms import RegisterForm

from bolsa.templatetags.randomGen import getCoinValue

# Create your views here.

def home(request):
    res = None
    # opening database session and running a query
    session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
    try:
        input = """
                <root>{
                let $x := db:open("Bolsa")//days/update[last()]
                let $y := db:open("Bolsa")//days/update[last()-1]
                return ($x,$y)
                }</root>
                """
        query = session.query(input)
        res = query.execute()
        query.close()

    # closes database session
    finally:
        if session:
            session.close()

    # dictionary with the result of the query
    dres = xmltodict.parse(res)

    # array of updates
    lres = dres['root']['update']
    today = lres[0]
    yesterday = lres[1]
    res = []

    # array of tuples (symbol, yesterday value, today value, grossing) of all the stocks for the last 2 days
    for stock in today['stock']:
        yesterdayValue = float([item for item in yesterday['stock'] if item['symbol'] == stock['symbol']][0]['value'])
        todayValue = float(stock['value'])
        grossingValue = 100 - (yesterdayValue * 100 / todayValue)

        res.append({
            'symbol': stock['symbol'],
            'yesterday': '{:.2f}'.format(yesterdayValue),
            'today': '{:.2f}'.format(todayValue),
            'grossing': round(grossingValue, 2)  # grossing rounded by 2 decimal places
        })

    # array of top 5 grossing stocks
    # sorted by descending order
    topGrossing = sorted(res, key=lambda k: k['grossing'], reverse=True)[0:4]
    lowGrossing = sorted(res, key=lambda k: k['grossing'])[0:4]

    context = {
        'topGrossing': topGrossing,
        'lowGrossing': lowGrossing
    }

    return render(request, 'pages/home.html', context)


def valuesHome(request):
    return render(request, 'pages/valuesHome.html')


def valuesToday(request):
    res = None
    searchQuery = ''
    if request.method == 'POST':
        searchQuery = request.POST['searchQuery']
    # opening database session and running a query
    session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
    try:
        input = """
            <root>{{
            for $x in db:open("Bolsa")//days/update[last()]/stock
            for $y in db:open("Bolsa")//companys/company
            where $x/symbol = $y/symbol
            and
            (contains(lower-case($y/symbol/text()),lower-case('{}')) or contains(lower-case($y/name/text()),lower-case('{}')))
            return <stock>{{$y/name,$x/symbol,$x/value}}</stock>
            }}</root>
            """.format(searchQuery, searchQuery)
        query = session.query(input)
        res = query.execute()
        query.close()

    # closes database session
    finally:
        if session:
            session.close()

    # dictionary with the result of the query
    dres = xmltodict.parse(res)

    # array of updates
    lres = dres['root']
    # deal with empty result
    try:
        res = lres['stock']
    except:
        res = []
    # when only one item returned -> put inside array
    if not isinstance(res, list):
        res = [res]
    context = {
        'companies': res
    }

    return render(request, 'pages/valuesToday.html', context)


def valuesFilter(request):
    # Default Command
    inputCommand = """
        <root>{
        let $dateFirst := db:open("Bolsa")//days/update[1]/date
          return <firstDate>{$dateFirst}</firstDate>,
          let $dateLast := db:open("Bolsa")//days/update[last()]/date
          return <lastDate>{$dateLast}</lastDate>,
          let $companies := db:open("Bolsa")/companys//company//symbol
          return <companies>{$companies}</companies>,
          for $x in db:open("Bolsa")//days/update
          let $y := $x/stock
          return <update>{$x/date,$y}</update>
        }</root>
    """
    if request.method == 'POST':  # Change input command with all the parameters
        # Get Post data
        companyList = request.POST.getlist('companies')
        startDatePost = request.POST['startDate']
        endDatePost = request.POST['endDate']
        # Prepare companies query part
        companyCommand = ''
        if companyList:
            i = 0
            while i < len(companyList):
                if i == 0:
                    companyCommand += 'where $stock/symbol/text() = \"{}\"'.format(companyList[i])
                else:
                    companyCommand += 'or $stock/symbol/text() = \"{}\"'.format(companyList[i])
                i += 1
        startDateSplit = startDatePost.split('-')
        endDateSplit = endDatePost.split('-')
        startDate = {}
        endDate = {}
        startDate['day'] = startDateSplit[2]
        startDate['month'] = startDateSplit[1]
        startDate['year'] = startDateSplit[0]
        endDate['day'] = endDateSplit[2]
        endDate['month'] = endDateSplit[1]
        endDate['year'] = endDateSplit[0]
        inputCommand= """
        <root>{{
          let $companies := db:open("Bolsa")/companys//company//symbol
          return <companies>{{$companies}}</companies>,
          let $dateFirst := db:open("Bolsa")//days/update[1]/date
          return <firstDate>{{$dateFirst}}</firstDate>,
          let $dateLast := db:open("Bolsa")//days/update[last()]/date
          return <lastDate>{{$dateLast}}</lastDate>,
          for $x1 in db:open("Bolsa")//days/update
          let $y1 := db:open("Bolsa")//days/update
          where $x1/date/day/text() = "{}" and $x1/date/month/text() = "{}" and $x1/date/year/text() = "{}"
          return
            let $pos1 := index-of($y1,$x1)
             return
               for $x2 in db:open("Bolsa")//days/update
               where $x2/date/day/text() = "{}" and $x2/date/month/text() = "{}" and $x2/date/year/text() = "{}"
               return
                  let $pos2 := index-of($y1,$x2)
                  for $a in db:open("Bolsa")//days/update[position() >= $pos1 and not(position() > $pos2)]
                  return <update>
                      {{$a/date,
                      for $stock in $a/stock
                      {}
                      return $stock
                    }}
                  </update>
        }}</root>
        """.format(startDate.get('day'), startDate.get('month'), startDate.get('year'), endDate.get('day'), endDate.get('month'), endDate.get('year'), companyCommand)

    # Run the Query and pass the results to the template
    session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
    try:
        query = session.query(inputCommand)
        res = query.execute()
        query.close()

    # closes database session
    finally:
        if session:
            session.close()

    # dictionary with the result of the query
    dres = xmltodict.parse(res)['root']
    try:
        res = dres['update']
    except:
        res = []
    # when only one item returned put inside array
    if not isinstance(res, list):
        res = [res]

    # put data for the companies usable for graph
    graphData = {}
    for update in res:
        if 'stock' in update: #Check if there are any stocks
            if type(update['stock']) == list: # If more than one stock
                for stock in update['stock']:
                    graphData.setdefault(stock['symbol'], []).append(float(stock['value']))
            else: #If only one stock
                graphData.setdefault(update['stock']['symbol'], []).append(float(update['stock']['value']))
    # Dynamically fill empty values
    for v in graphData.values():
        while len(v) < len(res):
            v.insert(0, 0)
    context = {
        'updates': res,
        'graphData': graphData,
        'companies': dres['companies']['symbol'],
        'firstDate': dres['firstDate'],
        'lastDate': dres['lastDate']
    }

    return render(request, 'pages/valuesFilter.html', context)


def valuesCoins(request):
    res = None
    searchQuery = ''
    if request.method == 'POST':
        searchQuery = request.POST['searchQuery']
    # print(searchQuery)
    # opening database session and running a query
    session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
    try:
        input = """
            <root>{{
            for $x in db:open("Bolsa")//days/update[last()]/coin
              for $y in db:open("Bolsa")//coins/coin
              where $x/code = $y/code
              and
              (contains(lower-case($y/name/text()),lower-case('{}')) 
              or contains(lower-case($y/code/text()),lower-case('{}'))
               or contains($y/symbol/text(),'{}'))
              return <stock>{{$y/name,$y/symbol,$x/value}}</stock>
            }}</root>
                """.format(searchQuery, searchQuery, searchQuery)
        query = session.query(input)
        res = query.execute()
        query.close()

    # closes database session
    finally:
        if session:
            session.close()

    xmlTree = etree.XML(res)
    xsltPath = os.path.join('bolsa', os.path.join('data', os.path.join('xslt', 'coins.xslt')))
    xsltTree = etree.parse(xsltPath)
    transform = etree.XSLT(xsltTree)
    result = transform(xmlTree)

    context = {
        'table': result
    }

    return render(request, 'pages/valuesCoins.html', context)


def companies(request):
    res = None
    companySearchCommand= ''
    if request.method == "POST":
        companySearchCommand = 'where (contains(lower-case($x/symbol/text()),lower-case(\'{c}\')) or contains(lower-case($x/name/text()),lower-case(\'{c}\')))'.format(c=request.POST['searchQuery'])
    # opening database session and running a query
    session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
    try:
        input = """
                    <root>{{
                    for $x in db:open("Bolsa")//companys/company
                    {}
                    return <company>{{$x/name,$x/symbol}}</company>
                    }}</root>
                    """.format(companySearchCommand)
        query = session.query(input)
        res = query.execute()
        query.close()

    # closes database session
    finally:
        if session:
            session.close()

    xmlTree = etree.XML(res)
    xsltPath = os.path.join('bolsa', os.path.join('data', os.path.join('xslt', 'companies.xslt')))
    xsltTree = etree.parse(xsltPath)
    transform = etree.XSLT(xsltTree)
    result = transform(xmlTree)

    context = {
        'table': result
    }
    # print(context)
    return render(request, 'pages/companies.html', context)


def companiesInfo(request, symbol):
    if request.method == 'POST':
        if request.user.is_authenticated:
            company = symbol
            quantitySell = request.POST['quantitySell']
            session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
            try:
                input = """
                  for $y in db:open("Bolsa")//portfolios/portfolio
                  where $y/idUser = "{id}"
                  return
                    let $a := db:open("Bolsa")//days/update[last()]
                    for $stock in $a/stock
                    where $stock/symbol/text() = "{c}"
                    return if($y/money/text() > $stock/value/text()*{q}) then
                      (replace node $y/money/text() with $y/money/text()-$stock/value/text()*{q},
                      let $userStock := $y/wallet/stock
                      return(
                        if($userStock/symbol/text() = "{c}") then
                          for $c in $userStock
                          where $c/symbol/text() = "{c}"
                          return replace node $c/quantity/text() with $c/quantity/text()+{q}
                        else
                           insert node <stock><symbol>{c}</symbol><quantity>{q}</quantity></stock> into $y/wallet
                      ),
                      let $b := $y/buys
                      return insert node <buy><stock>{{$stock/symbol,$a/date}}<amount>{q}</amount></stock></buy> into $b
                    )
                    else
                      ()
                """.format(id=request.user.id, c=company, q=quantitySell)

                query = session.query(input)
                res = query.execute()
                query.close()


                # closes database session
            finally:
                if session:
                    session.close()

            return redirect('/portfolio')
        else:
            return redirect('/accounts/login')
    res = None
    # opening database session and running a query
    session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
    try:
        input = """
                <root>{{
                    let $symbol := '{}'
                    for $y in db:open("Bolsa")//companys/company
                    where $y/symbol/text() = $symbol
                    return $y,
                    let $symbol := '{}'
                    let $x := db:open("Bolsa")//days/update
                    where $x/stock/symbol/text() = $symbol 
                    return $x
                }}</root>
                """.format(symbol, symbol)

        query = session.query(input)
        res = query.execute()
        query.close()
    # closes database session
    finally:
        if session:
            session.close()

    # dictionary with the result of the query
    dres = xmltodict.parse(res)
    # array of updates
    lres = dres['root']
    values = []
    dates = []
    info = lres['company']
    if 'update' in lres:
        updates = lres['update']

        values = []
        dates = []
        for elem in updates:
            for stock in elem['stock']:
                if stock['symbol'] == symbol:
                    values.append(float(stock["value"]))
                    dates.append(str(elem['date']['day'] + "/" + elem['date']['month'] + '/' + elem['date']['year']))

    # print(values)
    # print(dates)

    context = {
        'company': info,
        'values': values,
        'dates': dates,
    }
    # print(context)
    return render(request, 'pages/companiesInfo.html', context)


def portfolio(request):
    if request.user.is_authenticated:
        if request.method == "POST":  # ADD MONEY
            moneyToAdd = request.POST['moneyToAdd']
            if 'selectedCoin' in request.session:
                if request.session['selectedCoin'] != "usd":
                    moneyToAdd = float(moneyToAdd) * 1/(float(getCoinValue(request.session['selectedCoin'])))
            session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
            try:
                input = """
                    for $y in db:open("Bolsa")//portfolios/portfolio
                    where $y/idUser = "{}"
                    return replace node $y/money/text() with $y/money/text()+{}
                """.format(request.user.id, moneyToAdd)
                query = session.query(input)
                res = query.execute()
                query.close()
            # closes database session
            finally:
                if session:
                    session.close()

        res = None
        # opening database session and running a query
        session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
        try:
            input = """
                                for $y in db:open("Bolsa")//portfolios/portfolio
                                where $y/idUser = "{}"
                                return $y
                            """.format(request.user.id)

            query = session.query(input)
            res = query.execute()
            query.close()
        # closes database session
        finally:
            if session:
                session.close()
        #print(request.user.id)
        #print(res)
        # dictionary with the result of the query
        dres = xmltodict.parse(res)
        # array of updates

        lres = dres['portfolio']

        sells = []
        buys = []
        wallet = []
        portfolio_value = 0


        if lres['wallet'] != None:
            for elem in lres['wallet'].items():
                for stock in elem[1]:
                    if isinstance(stock, dict):
                        wallet.append(
                            {
                                'symbol': stock['symbol'],
                                'amount': stock['quantity'],
                                'value': get_stock_current_value(stock['symbol'])
                            }
                        )
                        portfolio_value += float(get_stock_current_value(stock['symbol'])) * int(
                            stock['quantity'])

                    else:
                        wallet.append(
                            {
                                'symbol': elem[1]['symbol'],
                                'amount': elem[1]['quantity'],
                                'value': get_stock_current_value( elem[1]['symbol'])
                            }
                        )
                        portfolio_value += float(get_stock_current_value(elem[1]['symbol'])) * int(elem[1]['quantity'])
                        break


        if lres['sells'] != None:
            if (len(lres['sells']['sell']) == 1):
                sells.append(
                    {
                        'symbol': lres['sells']['sell']['stock']['symbol'],
                        'date': lres['sells']['sell']['stock']['date']['day'] + '/' +
                                lres['sells']['sell']['stock']['date']['month'] + '/' +
                                lres['sells']['sell']['stock']['date']['year'],
                        'amount': lres['sells']['sell']['stock']['amount']
                    }
                )
            else:
                for elem in lres['sells'].items():
                    for sell in elem[1]:
                        sells.append(
                            {
                                'symbol': sell['stock']['symbol'],
                                'date': sell['stock']['date']['day'] + '/' + sell['stock']['date']['month'] + '/' +
                                        sell['stock']['date']['year'],
                                'amount': sell['stock']['amount']
                            }
                        )

        if lres['buys'] != None:
            if (len(lres['buys']['buy']) == 1):
                buys.append(
                    {
                        'symbol': lres['buys']['buy']['stock']['symbol'],
                        'date': lres['buys']['buy']['stock']['date']['day'] + '/' +
                                lres['buys']['buy']['stock']['date']['month'] + '/' +
                                lres['buys']['buy']['stock']['date']['year'],
                        'amount': lres['buys']['buy']['stock']['amount']
                    }
                )
            else:
                for elem in lres['buys'].items():
                    for buy in elem[1]:
                        buys.append(
                            {
                                'symbol': buy['stock']['symbol'],
                                'date': buy['stock']['date']['day'] + '/' + buy['stock']['date']['month'] + '/' +
                                        buy['stock']['date']['year'],
                                'amount': buy['stock']['amount']
                            }
                        )


        context = {
            'user': lres,
            'wallet': wallet,
            'sells': sells,
            'buys': buys,
            'portfolio_value' : portfolio_value
        }

        return render(request, 'pages/portfolio.html', context)
    else:
        return redirect('/accounts/login')


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            name = form.cleaned_data.get('name')
            user = authenticate(username=username, password=raw_password)
            # Add user to XML DB
            session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
            try:
                input = """
                                for $a in db:open("Bolsa")//portfolios
                                return insert node
                                    <portfolio>
                                        <idUser>{}</idUser>
                                        <name>{}</name> 
                                        <money>0</money>
                                        <wallet></wallet>
                                        <buys></buys>
                                        <sells></sells>
                                     </portfolio>
                                into $a
                            """.format(user.id, name)
                query = session.query(input)
                res = query.execute()
                query.close()

            finally:
                if session:
                    session.close()
            login(request, user)
            return redirect('/portfolio')
    else:
        form = RegisterForm()
    context = {
        'form': form
    }
    return render(request, 'registration/register.html', context)


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        return render(request, 'registration/logout.html')
    else:
        return redirect('/accounts/login')


def sell(request):
    if request.user.is_authenticated:
        current_user = request.user
        if request.method == 'POST':
            # Get Post Values
            company = request.POST['companies']
            quantitySell = request.POST['quantitySell']
            session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
            try:
                input = """
                  for $y in db:open("Bolsa")//portfolios/portfolio
                  where $y/idUser = "{id}"
                  return
                   for $stock in $y/wallet/stock
                   where $stock/symbol/text() = "{c}"
                   return 
                     if ($stock/quantity/text()-{q} > 0) then
                      (
                        replace node $stock/quantity/text() with $stock/quantity/text()-{q},
                        let $a := db:open("Bolsa")//days/update[last()]
                        for $stock in $a/stock
                        where $stock/symbol/text() = "{c}"
                        return 
                          let $price := $stock/value
                          return replace node $y/money/text() with $y/money/text()+$price*{q},
                          let $b := $y/sells
                          let $a := db:open("Bolsa")//days/update[last()]
                          return insert node <sell><stock>{{$stock/symbol,$a/date}}<amount>{q}</amount></stock></sell> into $b
                      )
                    else if ($stock/quantity/text()-{q} = 0) then
                      (
                        delete node $stock,
                        let $a := db:open("Bolsa")//days/update[last()]
                        for $stock in $a/stock
                        where $stock/symbol/text() = "{c}"
                        return 
                          let $price := $stock/value
                          return replace node $y/money/text() with $y/money/text()+$price*{q},
                          let $b := $y/sells
                          let $a := db:open("Bolsa")//days/update[last()]
                          return insert node <sell><stock>{{$stock/symbol,$a/date}}<amount>{q}</amount></stock></sell> into $b
                      
                      )
                      
                    else()
                 """.format(id=current_user.id, c=company, q=quantitySell)

                query = session.query(input)
                res = query.execute()
                query.close()
                # closes database session
            finally:
                if session:
                    session.close()

        res = None
        # opening database session and running a query
        session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
        try:
            input = """
                                <root>{
                                    let $idUser := '""" + str(current_user.id) + """'
                                    for $y in db:open("Bolsa")//portfolios/portfolio
                                    where $y/idUser = $idUser
                                    return $y
                                }</root>
                                """

            query = session.query(input)
            res = query.execute()
            query.close()
        # closes database session
        finally:
            if session:
                session.close()

        # dictionary with the result of the query
        dres = xmltodict.parse(res)
        # array of updates
        lres = dres['root']['portfolio']
        wallet = []


        if lres['wallet'] != None:
            for elem in lres['wallet'].items():
                for stock in elem[1]:
                    if isinstance(stock, dict):
                        wallet.append(
                            {
                                'symbol': stock['symbol'],
                                'amount': stock['quantity']
                            }
                        )
                    else:
                        wallet.append(
                            {
                                'symbol': elem[1]['symbol'],
                                'amount': elem[1]['quantity'],
                            }
                        )
                        break



        context = {
            'wallet': wallet,
            'balance': lres['money']
        }
        return render(request, 'pages/sell.html', context)
    else:
        return redirect('/accounts/login')


def rssFeed(request,symbol):

    # checking if the stock/symbol exists in our db

    res = None
    # opening database session and running a query
    session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
    try:
        input = """
                <root>{
                    let $symbol := '""" + symbol.upper() + """'
                    for $x in db:open("Bolsa")//companys/company
                    where $x/symbol/text() = $symbol
                    return $x
                }</root>
                """
        query = session.query(input)
        res = query.execute()
        query.close()
    # closes database session
    finally:
        if session:
            session.close()


    # dictionary with the result of the query
    dres = xmltodict.parse(res)
    # array of updates
    try:
        lres = dres['root']['company']
    except:
        return HttpResponse('Wrong symbol <br><a href=\"/\">Get Back</a>')


    url = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={}".format(symbol)
    contents = ""
    try:
        # contents = urllib.request.urlopen(url).read()
        contents = etree.parse(urllib.request.urlopen(url))
    except:
        return HttpResponse('Invalid URL <br><a href=\"/\">Get Back</a>')


    # validating feed
    schemaPath = os.path.join('bolsa', os.path.join('data', os.path.join('schemas', 'rssfeed.xsd')))
    xmlschema_doc = etree.parse(schemaPath)
    xmlschema = etree.XMLSchema(xmlschema_doc)
    validation = xmlschema.validate(contents)

    if validation:

        # print(etree.tostring(contents).decode('utf8'))
        dcontents = xmltodict.parse(etree.tostring(contents).decode('utf8'))
        dcontents = dcontents['rss']['channel']
        items = [v for k, v in dcontents.items() if k == 'item'][0]

        # print(items)

        context = {
            'company' : lres,
            'title': dcontents['title'],
            'link': dcontents['link'],
            'description': dcontents['description'],
            'items': items,
        }

        return render(request, 'pages/rssfeed.html', context)

    else :
        return HttpResponse('Feed not supported <br><a href=\"/\">Get Back</a>')


def get_stock_current_value(symbol):

    # checking if the stock/symbol exists in our db

    res = None
    # opening database session and running a query
    session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
    try:
        input = """
                    <root>{
                        let $symbol := '""" + symbol.upper() + """'
                        for $x in db:open("Bolsa")//days/update
                        where $x/stock/symbol/text() = $symbol
                        return $x
                    }</root>
                    """
        query = session.query(input)
        res = query.execute()
        query.close()
    # closes database session
    finally:
        if session:
            session.close()

    # dictionary with the result of the query
    dres = xmltodict.parse(res)
    # array of updates


    lres = dres['root']



    values = []

    # only one update with that stock
    if(len(lres['update']) == 1):
        for item in lres['update']['stock']:
            if item['symbol'] == symbol:
                return item["value"]

    else:
        for elem in lres['update']:
            for stock in elem['stock']:
                if stock['symbol'] == symbol:
                    values.append(stock["value"])

    return  values[-1]

def seeFull(request,type):
    if request.user.is_authenticated:
        split = type.split('-')
        type = split[0]

        current_user = request.user
        res = None
        # opening database session and running a query
        session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
        try:
            input = """
                        <root>{
                            let $idUser := '""" + str(current_user.id) + """'
                            for $y in db:open("Bolsa")//portfolios/portfolio
                            where $y/idUser = $idUser
                            return $y
                        }</root>
                        """

            query = session.query(input)
            res = query.execute()
            query.close()
        # closes database session
        finally:
            if session:
                session.close()

        # dictionary with the result of the query
        dres = xmltodict.parse(res)
        # array of updates
        lres = dres['root']['portfolio']

        items = []
        portfolio_value = 0

        # an array of dictionaries
        # each contaning stock name and total sales/buys
        stock_val_symbol = []

        if type == 'Wallet':
            if lres['wallet'] != None:
                if (len(lres['wallet']['stock']) == 1):
                    items.append(
                        {
                            'symbol': lres['wallet']['stock']['symbol'],
                            'amount': lres['wallet']['stock']['quantity'],
                            'value' : get_stock_current_value(lres['wallet']['stock']['symbol'])
                        }
                    )
                    portfolio_value+= float(get_stock_current_value(lres['wallet']['stock']['symbol'])) * int(lres['wallet']['stock']['quantity'])

                else:
                    for elem in lres['wallet'].items():
                        for stock in elem[1]:
                            items.append(
                                {
                                    'symbol': stock['symbol'],
                                    'amount': stock['quantity'],
                                    'value' : get_stock_current_value(stock['symbol'])
                                }
                            )
                            portfolio_value += float(get_stock_current_value(stock['symbol'])) * int(stock['quantity'])

        elif type == 'Sells':
            if lres['sells'] != None:
                if (len(lres['sells']['sell']) == 1):
                    check = False

                    if len(stock_val_symbol) != 0:
                        for item in stock_val_symbol:
                            if item['symbol'] == lres['sells']['sell']['stock']['symbol']:
                                item['totalamount'] += int(lres['sells']['sell']['stock']['amount'])
                                check = True

                    if not check:
                        stock_val_symbol.append(
                            {
                                'symbol': lres['sells']['sell']['stock']['symbol'],
                                'totalamount': int(lres['sells']['sell']['stock']['amount'])
                            }
                        )
                    items.append(
                        {
                            'symbol': lres['sells']['sell']['stock']['symbol'],
                            'date': lres['sells']['sell']['stock']['date']['day'] + '/' +
                                    lres['sells']['sell']['stock']['date']['month'] + '/' +
                                    lres['sells']['sell']['stock']['date']['year'],
                            'amount': lres['sells']['sell']['stock']['amount']
                        }
                    )
                else:
                    for elem in lres['sells'].items():
                        for sell in elem[1]:
                            check = False

                            if len(stock_val_symbol) != 0:
                                for item in stock_val_symbol:
                                    if item['symbol'] == sell['stock']['symbol']:
                                        item['totalamount'] += int(sell['stock']['amount'])
                                        check = True

                            if not check:
                                stock_val_symbol.append(
                                    {
                                        'symbol': sell['stock']['symbol'],
                                        'totalamount': int(sell['stock']['amount'])
                                    }
                                )


                            items.append(
                                {
                                    'symbol': sell['stock']['symbol'],
                                    'date': sell['stock']['date']['day'] + '/' + sell['stock']['date']['month'] + '/' +
                                            sell['stock']['date']['year'],
                                    'amount': sell['stock']['amount']
                                }
                        )

        else:
            if lres['buys'] != None:
                if (len(lres['buys']['buy']) == 1):
                    check = False

                    if len(stock_val_symbol) != 0:
                        for item in stock_val_symbol:
                            if item['symbol'] == lres['buys']['buy']['stock']['symbol']:
                                item['totalamount'] += int(lres['buys']['buy']['stock']['amount'])
                                check = True

                    if not check:
                        stock_val_symbol.append(
                            {
                                'symbol': lres['buys']['buy']['stock']['symbol'],
                                'totalamount': lres['buys']['buy']['stock']['amount']
                            }
                        )

                    items.append(
                        {
                            'symbol': lres['buys']['buy']['stock']['symbol'],
                            'date': lres['buys']['buy']['stock']['date']['day'] + '/' +
                                    lres['buys']['buy']['stock']['date']['month'] + '/' +
                                    lres['buys']['buy']['stock']['date']['year'],
                            'amount': lres['buys']['buy']['stock']['amount'],
                        }
                    )

                else:
                    for elem in lres['buys'].items():
                        for buy in elem[1]:
                            check = False

                            if len(stock_val_symbol) != 0:
                                for item in stock_val_symbol:
                                    if item['symbol'] == buy['stock']['symbol']:
                                        item['totalamount'] += int(buy['stock']['amount'])
                                        check = True

                            if not check:
                                stock_val_symbol.append(
                                    {
                                        'symbol': buy['stock']['symbol'],
                                        'totalamount': int(buy['stock']['amount'])
                                    }
                                )

                            items.append(
                                {
                                    'symbol': buy['stock']['symbol'],
                                    'date': buy['stock']['date']['day'] + '/' + buy['stock']['date']['month'] + '/' +
                                            buy['stock']['date']['year'],
                                    'amount': buy['stock']['amount']
                                }
                            )


        context = {
            'type': type,
            'items': items,
            'stock' : stock_val_symbol,
            'portfolio_value' : portfolio_value
        }

        return render(request, 'pages/seefull.html', context)

    else:
        return redirect('/accounts/login')

def selectCoin(request, code):
    referer = request.GET['last']
    if code == "usd":
        request.session['selectedCoin'] = code
        return redirect(referer)
    session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
    try:
        input = """<root>{{
                   for $a in db:open("Bolsa")/coins/coin
                   where $a/code = "{}"
                   return $a/code/text()
                   }}</root>
               """.format(code)
        query = session.query(input)
        res = query.execute()
        query.close()
    # closes database session
    finally:
        if session:
            session.close()
    dres = xmltodict.parse(res)
    lres = dres['root']
    if lres:
        request.session['selectedCoin'] = code
    return redirect(referer)