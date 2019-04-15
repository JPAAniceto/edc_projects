from django.shortcuts import render, HttpResponse, redirect
from django.conf import settings
import xmltodict
from lxml import etree
import zipfile
import os
import io
from BaseXClient import BaseXClient


def adminXmlMain(request):
    if request.user.is_superuser:
        context = {}
        return render(request, 'pages/adminXml/main.html', context)
    return redirect("/")

def adminXmlExport(request, target):
    if request.user.is_superuser:
        dir2output = os.path.join(settings.BASE_DIR,'outputDB')
        session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
        try:
            session.execute("open Bolsa")
            print("export " + dir2output)
            session.execute("export \"" + dir2output + "\"")
            session.execute("close")
        # closes database session
        finally:
            if session:
                session.close()
        if target == 'all':
            filenames = [os.path.join(dir2output, 'days.xml'),os.path.join(dir2output, 'portefolios.xml'),os.path.join(dir2output, 'coins.xml'),os.path.join(dir2output, 'companies.xml')]
            zip_filename = "db.zip"
            s = io.BytesIO()
            # The zip compressor
            zf = zipfile.ZipFile(s, "w")

            for fpath in filenames:
                # Calculate path for file in zip
                fdir, fname = os.path.split(fpath)
                zip_path = fname

                # Add file, at correct path
                zf.write(fpath, zip_path)

            # Must close zip for all contents to be written
            zf.close()
            resp = HttpResponse(s.getvalue(), content_type="application/x-zip-compressed")
            resp['Content-Disposition'] = 'attachment; filename=db.zip'
            return resp
        elif target == "days.xml":
            f = open(os.path.join(dir2output, 'days.xml'))
            response = HttpResponse(f, content_type='application/xml')
            response["Content-disposition"] = 'attachment; filename=\"days.xml\"'
            return response
        elif target == "portefolios.xml":
            f = open(os.path.join(dir2output, 'portefolios.xml'))
            response = HttpResponse(f, content_type='application/xml')
            response["Content-disposition"] = 'attachment; filename=\"portefolios.xml\"'
            return response
        elif target == "companies.xml":
            f = open(os.path.join(dir2output, 'companies.xml'))
            response = HttpResponse(f, content_type='application/xml')
            response["Content-disposition"] = 'attachment; filename=\"companies.xml\"'
            return response
        elif target == "coins.xml":
            f = open(os.path.join(dir2output, 'coins.xml'))
            response = HttpResponse(f, content_type='application/xml')
            response["Content-disposition"] = 'attachment; filename=\"coins.xml\"'
            return response
        else:
            return redirect('/adminxml/main')

    return redirect("/")


def adminXmlSubmitUpdate(request):
    if request.user.is_superuser:
        context = {}
        if request.method == 'POST':
            text = request.POST['update']
            try:
                xmlTree = etree.XML(text)
                schemaPath = os.path.join('bolsa', os.path.join('data', os.path.join('schemas', 'update.xsd')))
                schemaTree = etree.parse(schemaPath)
                xmlSchema = etree.XMLSchema(schemaTree)
                if xmlSchema.validate(xmlTree):
                    session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
                    try:
                        input = """
                            let $a := db:open("Bolsa")/days
                            return insert node {} as last into $a
                        """.format(text)
                        query = session.query(input)
                        res = query.execute()
                        query.close()
                    # closes database session
                    finally:
                        if session:
                            session.close()
                    context['message'] = "Update Submitted"
                else:
                    context['error'] = "Non valid update (Schema)"
            except:
                context['error'] = "Non valid update (XML)"
        return render(request, 'pages/adminXml/submitUpdate.html', context)
    return redirect("/")

def adminXmlSubmitCompany(request):
    if request.user.is_superuser:
        context = {}
        if request.method == 'POST':
            name = request.POST['name']
            type = request.POST['type']
            year = request.POST['year']
            symbol = request.POST['symbol']
            description = request.POST['description']
            logoData = request.FILES['logo']
            extension = os.path.splitext(str(logoData))[1]
            filepath= os.path.join(settings.STATIC_ROOT, os.path.join('images', symbol+extension))
            with open(filepath, 'wb+') as destination:
                for chunk in logoData.chunks():
                    destination.write(chunk)
            logo = symbol+extension
            session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')
            try:
                input = """
                    let $a := db:open("Bolsa")/companys
                    return insert node <company>
                    <name>{}</name><symbol>{}</symbol><logo>{}</logo><type>{}</type><year>{}</year><description>{}</description>
                    </company> as last into $a
                """.format(name, symbol, logo, type, year, description)
                #print(input)
                query = session.query(input)
                res = query.execute()
                query.close()
            # closes database session
            finally:
                if session:
                    session.close()

        return render(request, 'pages/adminXml/submitCompany.html', context)
    return redirect("/")


