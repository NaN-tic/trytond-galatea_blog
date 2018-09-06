# This file is part galatea_blog module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import galatea
from . import blog

def register():
    Pool.register(
        blog.Tag,
        blog.Post,
        blog.PostWebsite,
        blog.PostTag,
        blog.Comment,
        galatea.GalateaWebSite,
        module='galatea_blog', type_='model')
