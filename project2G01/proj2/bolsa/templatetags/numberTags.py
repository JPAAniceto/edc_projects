from django import template
import random

register = template.Library()

@register.simple_tag()
def addCommasNumber(n):
    return "{:,}".format(round(float(n),2))

@register.simple_tag()
def randomInt(a, b):
    return random.randint(a, b)
