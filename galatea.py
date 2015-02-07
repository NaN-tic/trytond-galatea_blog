# This file is part galatea_blog module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.model import fields
from trytond.pyson import Eval

__all__ = ['GalateaWebSite']
__metaclass__ = PoolMeta


class GalateaWebSite:
    __name__ = "galatea.website"

    posts_base_uri = fields.Many2One('galatea.uri', 'Posts Base Uri', domain=[
            ('website', '=', Eval('id', -1)),
            ])
    default_blog_post_template = fields.Many2One('galatea.template',
        'Default Blog Post Template', domain=[
            ('allowed_models.model', 'in', ['galatea.blog.post'])
            ])
    tags_base_uri = fields.Many2One('galatea.uri', 'Tags Base Uri', domain=[
            ('website', '=', Eval('id', -1)),
            ])
    default_blog_tag_template = fields.Many2One('galatea.template',
        'Default Tag Post Template', domain=[
            ('allowed_models.model', 'in', ['galatea.blog.tag'])
            ])
    blog_comment = fields.Boolean('Blog comments',
        help='Active blog comments.')
    blog_anonymous = fields.Boolean('Blog Anonymous',
        help='Active user anonymous to publish comments.')
    blog_anonymous_user = fields.Many2One('galatea.user',
        'Blog Anonymous User', states={
            'required': Eval('blog_anonymous', True),
            })
