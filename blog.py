# This file is part galatea_blog module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from datetime import datetime

from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool
from trytond.transaction import Transaction

from trytond.modules.galatea import GalateaVisiblePage

__all__ = ['Tag', 'Post', 'PostWebsite', 'PostTag', 'Comment']


class Tag(GalateaVisiblePage, ModelSQL, ModelView):
    '''Blog Tag'''
    __name__ = 'galatea.blog.tag'

    websites = fields.Function(fields.Many2Many('galatea.website', None, None,
            'Websites'),
        'get_websites', searcher='search_websites')
    posts = fields.Many2Many('galatea.blog.post-galatea.blog.tag', 'tag',
        'post', 'Posts', readonly=True)

    def get_websites(self, name):
        website_ids = set()
        for post in self.posts:
            website_ids |= set(w.id for w in post.websites)
        return list(website_ids)

    @classmethod
    def search_websites(cls, name, clause):
        return [
            ('posts.websites', ) + tuple(clause[1:]),
            ]

    @classmethod
    def create(cls, vlist):
        pool = Pool()
        Website = pool.get('galatea.website')

        all_websites = Website.search([])
        websites_value = [('add', [w.id for w in all_websites])]
        for vals in vlist:
            if not vals.get('websites'):
                vals['websites'] = websites_value
        return super(Tag, cls).create(vlist)

    @classmethod
    def calc_uri_vals(cls, record_vals):
        pool = Pool()
        Website = pool.get('galatea.website')

        uri_vals = super(Tag, cls).calc_uri_vals(record_vals)

        website = Website(uri_vals['website'])
        assert website.tags_base_uri, (
            "Missing required field in Webite %s" % website.rec_name)
        assert website.default_blog_tag_template, (
            "Missing required field in Webite %s" % website.rec_name)

        uri_vals['parent'] = website.tags_base_uri.id
        uri_vals['template'] = website.default_blog_tag_template.id
        return uri_vals


class Post(GalateaVisiblePage, ModelSQL, ModelView):
    "Blog Post"
    __name__ = 'galatea.blog.post'
    websites = fields.Many2Many('galatea.blog.post-galatea.website',
        'post', 'website', 'Websites', required=True)
    description = fields.Text('Description', required=True, translate=True,
        help='You could write wiki markup to create html content. Formats '
        'text following the MediaWiki '
        '(http://meta.wikimedia.org/wiki/Help:Editing) syntax.')
    long_description = fields.Text('Long Description', translate=True,
        help='You could write wiki markup to create html content. Formats '
        'text following the MediaWiki '
        '(http://meta.wikimedia.org/wiki/Help:Editing) syntax.')
    markup = fields.Selection([
            (None, ''),
            ('wikimedia', 'WikiMedia'),
            ('rest', 'ReStructuredText'),
            ], 'Markup')
    metadescription = fields.Char('Meta Description', translate=True,
        help='Almost all search engines recommend it to be shorter '
        'than 155 characters of plain text')
    metakeywords = fields.Char('Meta Keywords', translate=True,
        help='Separated by comma')
    metatitle = fields.Char('Meta Title', translate=True)
    post_create_date = fields.DateTime('Create Date', readonly=True)
    post_write_date = fields.DateTime('Write Date', readonly=True)
    # TODO: it should be "author"
    user = fields.Many2One('galatea.user', 'User', required=True)
    tags = fields.Many2Many('galatea.blog.post-galatea.blog.tag', 'post',
        'tag', 'Tags')
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

    @classmethod
    def default_websites(cls):
        Website = Pool().get('galatea.website')
        websites = Website.search([('active', '=', True)])
        return [w.id for w in websites]

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
        now = datetime.now()
        vlist = [x.copy() for x in vlist]
        for vals in vlist:
            if not vals.get('post_create_date'):
                vals['post_create_date'] = now
        return super(Post, cls).create(vlist)

    @classmethod
    def calc_uri_vals(cls, record_vals):
        pool = Pool()
        Website = pool.get('galatea.website')

        uri_vals = super(Post, cls).calc_uri_vals(record_vals)

        website = Website(uri_vals['website'])
        assert website.posts_base_uri, (
            "Missing required field in Webite %s" % website.rec_name)
        assert website.default_blog_post_template, (
            "Missing required field in Webite %s" % website.rec_name)

        uri_vals['parent'] = website.posts_base_uri.id
        uri_vals['template'] = website.default_blog_post_template.id
        return uri_vals

    @classmethod
    def copy(cls, posts, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        if not default.get('post_create_date'):
            default['post_create_date'] = None
        default['post_write_date'] = None
        return super(Post, cls).copy(posts, default=default)

    @classmethod
    def write(cls, *args):
        now = datetime.now()
        actions = iter(args)
        args = []
        for posts, values in zip(actions, actions):
            values['post_write_date'] = now
            args.extend((posts, values))

        super(Post, cls).write(*args)

    @classmethod
    def delete(cls, posts):
        if Transaction().user != 1:
            # Change by user warning
            cls.raise_user_error('delete_posts')
        super(Post, cls).delete(posts)


class PostWebsite(ModelSQL):
    'Galatea Blog Post - Website'
    __name__ = 'galatea.blog.post-galatea.website'
    post = fields.Many2One('galatea.blog.post', 'Post',
        ondelete='CASCADE', select=True, required=True)
    website = fields.Many2One('galatea.website', 'Website',
        ondelete='RESTRICT', select=True, required=True)

    @classmethod
    def __setup__(cls):
        super(PostWebsite, cls).__setup__()
        cls._sql_constraints += [
            ('post_website_uniq', 'UNIQUE (post, website)',
                'The Website of the Post must be unique.'),
            ]


class PostTag(ModelSQL):
    'Galatea Blog Post - Tag'
    __name__ = 'galatea.blog.post-galatea.blog.tag'
    post = fields.Many2One('galatea.blog.post', 'Galatea Post',
        ondelete='CASCADE', required=True, select=True)
    tag = fields.Many2One('galatea.blog.tag', 'Tag', ondelete='CASCADE',
        required=True, select=True)

    @classmethod
    def __setup__(cls):
        super(PostTag, cls).__setup__()
        cls._sql_constraints += [
            ('post_tag_uniq', 'UNIQUE (post, tag)',
                'The Tag of the Post must be unique.'),
            ]


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
