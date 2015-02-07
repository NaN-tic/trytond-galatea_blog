# This file is part galatea_blog module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from .galatea import *
from .blog import *

def register():
    Pool.register(
        Tag,
        Post,
        PostTag,
        Comment,
        GalateaWebSite,
        module='galatea_blog', type_='model')
