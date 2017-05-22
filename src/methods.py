import re
from collections import ChainMap


def strip_comment_from_url(uri):
    return '@%s' % uri.split('@')[-1]


def resolve_identifier(identifier):
    match = re.match("@?([\w\-\.]*)/([\w\-]*)", *strip_comment_from_url(identifier))
    if not hasattr(match, "group"):
        raise ValueError("Invalid identifier")
    return match.group(1), match.group(2)


def get_comment_history(mongo, author, permlink):
    conditions = {
        # 'account': author,
        'author': author,
        'type': 'comment',
        'permlink': permlink,
    }
    return list(mongo['Posts'].find(conditions).sort('created', -1))


def route(mongo, query):
    if query.startswith('@'):
        conditions = {
            "json_metadata.app": "steemit/0.1"
        }

        if query.find('/') > -1:
            # find backlinks
            author, permlink = resolve_identifier(query)
            p = mongo.db['Posts'].find_one({'author': author, 'permlink': permlink})
            if not p:
                return []
            url = "https://steemit.com/%s" % p.get('url')
            conditions['json_metadata.links'] = url
            results = perform_query(mongo, conditions=conditions)

            # filter out posts that link more than 10 things
            return [x for x in results if len(x['json_metadata']['links']) < 10]
        else:
            # find user mentions
            account = query.strip('@')
            conditions['json_metadata.users'] = account
            results = perform_query(mongo, conditions=conditions)

            # filter out results with more than 10 mentions (likely spam)
            return [x for x in results if len(x['json_metadata']['users']) < 10]
    else:
        # use mongodb text search
        results = perform_query(mongo, search=query)
        return results


def perform_query(mongo, conditions=None, search=None, sort_by='new', options=None):
    """ Run a query against SteemQ Posts. """
    # apply conditions, such as time constraints
    conditions = conditions or {}
    query = {
        **conditions,
    }
    projection = {
        '_id': 0,
        'title': 1,
        'author': 1,
        # 'body': 1,
        'permlink': 1,
        'identifier': 1,
        'created': 1,
        'pending_payout_value': 1,
        'total_payout_value': 1,
        'net_votes': 1,

    }

    sorting = []
    if sort_by == 'new':
        sorting = [('created', -1)]
    elif sort_by == 'payout':
        sorting = [
            ('pending_payout_value.amount', -1),
            ('total_payout_value.amount', -1),
        ]
    elif sort_by == 'votes':
        sorting = [('net_votes', -1)]

    if search:
        query['$text'] = {'$search': search}
        projection['score'] = {'$meta': 'textScore'}
        sorting.insert(0, ('score', {'$meta': 'textScore'}))

    options = options or {}
    default_options = {
        'limit': 100,
        'skip': 0,
    }
    options = ChainMap(options, default_options)

    return list(mongo.db['Posts'].find(
        filter=query,
        projection=projection,
        sort=sorting,
        limit=options.get('limit'),
        skip=options.get('skip'),
    ))


if __name__ == '__main__':
    from pprint import pprint
    from steemdata import SteemData

    sd = SteemData()
    pprint(perform_query(sd, search='furion python', sort_by='payout'))
