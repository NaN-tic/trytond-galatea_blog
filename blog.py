# This file is part galatea_blog module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from datetime import datetime

from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool
from trytond.pyson import Eval, Greater
from trytond.transaction import Transaction
# from trytond.cache import Cache

from .tools import slugify

__all__ = ['Post', 'Comment']


class Post(ModelSQL, ModelView):
    "Blog Post"
    __name__ = 'galatea.blog.post'
    name = fields.Char('Title', translate=True,
        required=True, on_change=['name', 'slug'])
    canonical_uri = fields.Many2One('galatea.uri', 'Canonical URI',
        required=True, select=True, domain=[
            ('website', 'in', Eval('websites')),
            ('type', '=', 'content'),
            ('template.allowed_models.model', 'in', ['galatea.blog.post']),
            ],
        states={
            'invisible': ~Greater(Eval('id', -1), 0),
            }, depends=['websites', 'id'])
    slug = fields.Function(fields.Char('Slug', translate=True, required=True),
        'on_change_with_slug', setter='set_canonical_uri_field',
        searcher='search_canonical_uri_field')
    uris = fields.One2Many('galatea.uri', 'content', 'URIs', readonly=True,
        help='All article URIs')
    uri = fields.Function(fields.Many2One('galatea.uri', 'URI'),
        'get_uri', searcher='search_uri')
    uri = fields.Function(fields.Char('Uri'), 'get_uri')
    # TODO: replace by uri_langs?
    # slug_langs = fields.Function(fields.Dict(None, 'Slug Langs'),
    #     'get_slug_langs')
    # _slug_langs_cache = Cache('galatea_blog_post.slug_langs')
    websites = fields.Many2Many('galatea.cms.article-galatea.website',
        'article', 'website', 'Websites', required=True,
        help='Tutorial will be available in those websites')
    description = fields.Text('Description', required=True, translate=True,
        help='You could write wiki markup to create html content. Formats '
        'text following the MediaWiki '
        '(http://meta.wikimedia.org/wiki/Help:Editing) syntax.')
    long_description = fields.Text('Long Description', translate=True,
        help='You could write wiki markup to create html content. Formats '
        'text following the MediaWiki '
        '(http://meta.wikimedia.org/wiki/Help:Editing) syntax.')
    metadescription = fields.Char('Meta Description', translate=True,
        help='Almost all search engines recommend it to be shorter '
        'than 155 characters of plain text')
    metakeywords = fields.Char('Meta Keywords', translate=True,
        help='Separated by comma')
    metatitle = fields.Char('Meta Title', translate=True)
    active = fields.Boolean('Active',
        help='Dissable to not show content post.')
    visibility = fields.Selection([
            ('public', 'Public'),
            ('register', 'Register'),
            ('manager', 'Manager'),
            ], 'Visibility', required=True)
    # TODO: extend getter/setter/searcher to all uris (is active is some uri is
    # active)
    active = fields.Function(fields.Boolean('Active',
            help='Dissable to not show content article.'),
        'get_active', setter='set_canonical_uri_field',
        searcher='search_canonical_uri_field')
    post_create_date = fields.DateTime('Create Date', readonly=True)
    post_write_date = fields.DateTime('Write Date', readonly=True)
    user = fields.Many2One('galatea.user', 'User', required=True)
    gallery = fields.Boolean('Gallery', help='Active gallery attachments.')
    comment = fields.Boolean('Comment', help='Active comments.')
    comments = fields.One2Many('galatea.blog.comment', 'post', 'Comments')
    total_comments = fields.Function(fields.Integer("Total Comments"),
        'get_total_comments')
    attachments = fields.One2Many('ir.attachment', 'resource', 'Attachments')

    @classmethod
    def __setup__(cls):
        super(Post, cls).__setup__()
        cls._order.insert(0, ('post_create_date', 'DESC'))
        cls._order.insert(1, ('name', 'ASC'))
        cls._error_messages.update({
            'delete_posts': ('You can not delete '
                'posts because you will get error 404 NOT Found. '
                'Dissable active field.'),
            })

    @fields.depends('name', 'slug')
    def on_change_name(self):
        res = {}
        if self.name and not self.slug:
            res['slug'] = slugify(self.name)
        return res

    @fields.depends('canonical_uri', 'slug')
    def on_change_with_slug(self, name=None):
        if self.canonical_uri:
            return self.canonical_uri.slug
        if self.slug:
            return slugify(self.slug)

    @classmethod
    def set_canonical_uri_field(cls, articles, name, value):
        pool = Pool()
        Uri = pool.get('galatea.uri')
        Uri.write([a.canonical_uri for a in articles if a.canonical_uri], {
                name: value,
                })

    @classmethod
    def search_canonical_uri_field(cls, name, clause):
        domain = [
            ('canonical_uri.%s' % name,) + tuple(clause[1:]),
            ]
        if clause == ['active', '=', False]:
            domain = [
                'OR',
                domain,
                [('canonical_uri', '=', None)],
                ]
        return domain

    # TODO: replace by uri_langs?
    # def get_slug_langs(self, name):
    #     'Return dict slugs for each active languages'
    #     pool = Pool()
    #     Lang = pool.get('ir.lang')
    #     Post = pool.get('galatea.blog.post')

    #     post_id = self.id
    #     langs = Lang.search([
    #         ('active', '=', True),
    #         ('translatable', '=', True),
    #         ])

    #     slugs = {}
    #     for lang in langs:
    #         with Transaction().set_context(language=lang.code):
    #             post, = Post.read([post_id], ['slug'])
    #             slugs[lang.code] = post['slug']

    #     return slugs

    def get_uri(self, name):
        context = Transaction().context
        if context.get('website', False):
            for uri in self.uris:
                if uri.website.id == context['website']:
                    return uri.id
        return self.canonical_uri.id

    @classmethod
    def search_uri(cls, name, clause):
        context = Transaction().context
        if context.get('website', False):
            # TODO: is it better and If()?
            return [
                ['OR', [
                    ('canonical_uri',) + tuple(clause[1:]),
                    ('website', '=', context['website']),
                    ], [
                    ('uris',) + tuple(clause[1:]),
                    ('website', '=', context['website']),
                    ]],
                ]
        return [
            ['OR', [
                ('canonical_uri',) + tuple(clause[1:]),
                ], [
                ('uris',) + tuple(clause[1:]),
                ]],
            ]

    @classmethod
    def default_websites(cls):
        Website = Pool().get('galatea.website')
        websites = Website.search([('active', '=', True)])
        return [w.id for w in websites]

    @staticmethod
    def default_visibility():
        return 'public'

    @staticmethod
    def default_active():
        return True

    def get_active(self, name):
        return self.canonical_uri.active if self.canonical_uri else False

    @classmethod
    def default_user(cls):
        Website = Pool().get('galatea.website')
        websites = Website.search([('active', '=', True)], limit=1)
        if not websites:
            return None
        website, = websites
        if website.blog_anonymous_user:
            return website.blog_anonymous_user.id
        return None

    @staticmethod
    def default_gallery():
        return True

    @staticmethod
    def default_comment():
        return True

    def get_total_comments(self, name):
        return len(self.comments)

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Uri = pool.get('galatea.uri')

        now = datetime.now()
        vlist = [x.copy() for x in vlist]
        for vals in vlist:
            vals['post_create_date'] = now
            if not vals.get('canonical_uri'):
                assert vals.get('slug')
                assert vals.get('websites')
                print 'websites:', vals['websites']
                uri_vals = cls.calc_uri_vals(vals)
                print "uri_vals:", uri_vals
                uri, = Uri.create([uri_vals])
                vals['canonical_uri'] = uri.id
        new_posts = super(Post, cls).create(vlist)

        uri_args = []
        for post in new_posts:
            if not post.canonical_uri.content:
                uri_args.extend(([post.canonical_uri], {
                        'content': str(post),
                        }))
        if uri_args:
            Uri.write(*uri_args)
        return new_posts

    @classmethod
    def calc_uri_vals(cls, post_vals):
        pool = Pool()
        Website = pool.get('galatea.website')

        website_id = [websites
            for action, websites in post_vals['websites']
            if action == 'add'][0][0]
        website = Website(website_id)
        assert website.posts_base_uri, (
            "Missing required field in Webite %s" % website.rec_name)
        assert website.default_blog_post_template, (
            "Missing required field in Webite %s" % website.rec_name)

        return {
            'website': website_id,
            'parent': website.posts_base_uri.id,
            'name': post_vals['name'],
            'slug': post_vals['slug'],
            'type': 'content',
            'template': website.default_blog_post_template.id,
            'active': post_vals.get('active', cls.default_active()),
            }

    @classmethod
    def copy(cls, posts, default=None):
        pool = Pool()
        Uri = pool.get('galatea.uri')

        if default is None:
            default = {}
        else:
            default = default.copy()
        default['blog_create_date'] = None
        default['blog_write_date'] = None

        new_posts = []
        for post in posts:
            default['canonical_uri'], = Uri.copy([post.canonical_uri], {
                    'slug': '%s-copy' % post.slug,
                    })
            new_posts += super(Post, cls).copy([post],
                default=default)
        return new_posts

    @classmethod
    def write(cls, *args):
        pool = Pool()
        Uri = pool.get('galatea.uri')

        now = datetime.now()
        actions = iter(args)
        args = []
        uri_args = []
        for posts, values in zip(actions, actions):
            values['post_write_date'] = now
            args.extend((posts, values))

            if values.get('canonical_uri'):
                canonical_uri = Uri(values['canonical_uri'])
                canonical_uri.content = posts[0]
                canonical_uri.save()
            if 'name' in values:
                uri_todo = []
                for post in posts:
                    if post.canonical_uri.name == post.name:
                        uri_todo.append(post.canonical_uri)
                    for uri in post.uris:
                        if uri.name == post.name and uri not in uri_todo:
                            uri_todo.append(uri)
                if uri_todo:
                    # What happens if canonical_uri and name change?
                    uri_args.append(uri_todo)
                    uri_args.append({
                            'name': values['name'],
                            })

        super(Post, cls).write(*args)
        if uri_args:
            Uri.write(*uri_args)

    @classmethod
    def delete(cls, posts):
        cls.raise_user_error('delete_posts')


class Comment(ModelSQL, ModelView):
    "Blog Comment Post"
    __name__ = 'galatea.blog.comment'
    post = fields.Many2One('galatea.blog.post', 'Post', required=True)
    user = fields.Many2One('galatea.user', 'User', required=True)
    description = fields.Text('Description', required=True,
        help='You could write wiki markup to create html content. Formats '
        'text following the MediaWiki '
        '(http://meta.wikimedia.org/wiki/Help:Editing) syntax.')
    active = fields.Boolean('Active',
        help='Dissable to not show content post.')
    comment_create_date = fields.Function(fields.Char('Create Date'),
        'get_comment_create_date')

    @classmethod
    def __setup__(cls):
        super(Comment, cls).__setup__()
        cls._order.insert(0, ('create_date', 'DESC'))
        cls._order.insert(1, ('id', 'DESC'))

    @staticmethod
    def default_active():
        return True

    @classmethod
    def default_user(cls):
        Website = Pool().get('galatea.website')
        websites = Website.search([('active', '=', True)], limit=1)
        if not websites:
            return None
        website, = websites
        if website.blog_anonymous_user:
            return website.blog_anonymous_user.id
        return None

    @classmethod
    def get_comment_create_date(cls, records, name):
        'Created domment date'
        res = {}
        DATE_FORMAT = '%s %s' % (Transaction().context['locale']['date'],
            '%H:%M:%S')
        for record in records:
            res[record.id] = record.create_date.strftime(DATE_FORMAT) or ''
        return res
