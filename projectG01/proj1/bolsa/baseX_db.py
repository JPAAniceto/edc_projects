from django.shortcuts import render, HttpResponse, redirect
from BaseXClient import BaseXClient
import os
from lxml import etree
import sys
# create session

xmls = ['coins','days','companies','portefolios']

def start_db():
    session = BaseXClient.Session("localhost", 1984, "admin", "admin")
    try:
        # create empty database
        session.execute("create db Bolsa ")

        for xml in xmls:
            state = validateXml(xml)
            if state == 1 :
                print('Non valid {} (Schema)'.format(xml))
                sys.exit()
            elif state == 2:
                print('Non valid {} (XML)'.format(xml))
                sys.exit()
            else :
                # add document
                session.add("{}.xml".format(xml), open(os.path.join('xml', '{}.xml'.format(xml)), "r", encoding='utf-8').read())

    finally:
        # close session
        if session:
            session.close()

if __name__=="__main__":
    start_db()


def validateXml(name):
    try:
        xmlPath = os.path.join('xml', '{}.xml'.format(name))
        xmlTree = etree.parse(xmlPath)

        schemaPath = os.path.join('bolsa', os.path.join('data', os.path.join('schemas', '{}.xsd'.format(name))))
        schemaTree = etree.parse(schemaPath)
        xmlSchema = etree.XMLSchema(schemaTree)

        if xmlSchema.validate(xmlTree):
            return 0
        else:
            return 1
    except:
        return 2



