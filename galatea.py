# This file is part galatea_blog module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import PoolMeta
from trytond.model import fields
from trytond.pyson import Eval

__all__ = ['GalateaWebSite']


class GalateaWebSite:
    __metaclass__ = PoolMeta
    __name__ = "galatea.website"

    posts_base_uri = fields.Many2One('galatea.uri', 'Posts Base Uri', domain=[
            ('website', '=', Eval('id', -1)),
            ], depends=['id'])
    default_blog_post_template = fields.Many2One('galatea.template',
        'Default Blog Post Template', domain=[
            ('allowed_models.model', 'in', ['galatea.blog.post'])
            ])
    tags_base_uri = fields.Many2One('galatea.uri', 'Tags Base Uri', domain=[
            ('website', '=', Eval('id', -1)),
            ], depends=['id'])
    default_blog_tag_template = fields.Many2One('galatea.template',
        'Default Tag Post Template', domain=[
            ('allowed_models.model', 'in', ['galatea.blog.tag'])
            ])
    archives_base_uri = fields.Many2One('galatea.uri', 'Archives Base Uri',
        domain=[
            ('website', '=', Eval('id', -1)),
            ], depends=['id'])
    blog_comment = fields.Boolean('Blog comments',
        help='Active blog comments.')
    blog_anonymous = fields.Boolean('Blog Anonymous', states={
            'invisible': ~Eval('blog_comment', False),
            }, depends=['blog_comment'],
        help='Active user anonymous to publish comments.')
    blog_anonymous_user = fields.Many2One('galatea.user',
        'Blog Anonymous User', states={
            'invisible': ~Eval('blog_comment', False),
            'required': Eval('blog_anonymous', True),
            }, depends=['blog_comment', 'blog_anonymous'])
