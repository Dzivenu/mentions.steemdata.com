import datetime as dt
from collections import ChainMap

from toolz import thread_last

import utils


def despam_results(results):
    """ Remove spammy looking posts. """

    def _filters(result):
        # do not remove this filter, the app requires it
        if not result.get('json_metadata') or type(result['json_metadata']) != dict:
            return False

        # filter out spam and unloved posts
        if len(result['json_metadata'].get('links', [])) > 15:
            return False
        if len(result['json_metadata'].get('users', [])) > 10:
            return False
        if result.get('net_votes', 0) < 5:
            return False
        if int(result.get('author_reputation', -1)) < 0:
            return False
        if int(result.get('net_rshares')) < 0:
            return False

        # todo add more filters
        return True

    def _clean_body(result):
        # todo sanitize non https links
        result['body'] = result['body'].replace('steemitboard.com', 'localhost')
        return result

    return thread_last(
        results,
        (filter, _filters),
        (map, _clean_body),
        list
    )


def route(mongo, query):
    if query.startswith('@') or query.startswith('https://steemit.com'):
        conditions = {
            "json_metadata.app": "steemit/0.1"
        }

        if query.find('/') > -1:
            # find backlinks
            identifier = utils.parse_identifier(query)
            if not identifier:
                return []
            author, permlink = identifier
            p = mongo.db['Posts'].find_one({'author': author, 'permlink': permlink})
            if not p or not p.get('url'):
                return []
            conditions['json_metadata.links'] = "https://steemit.com{}".format(p.get('url'))
            results = perform_query(mongo, conditions=conditions)
        else:
            # find user mentions
            account = query.strip('@')
            conditions['json_metadata.users'] = account
            conditions['author'] = {'$ne': account}  # dont show own posts
            results = perform_query(mongo, conditions=conditions)

    else:
        # use mongodb text search
        results = perform_query(mongo, search=query)

    return results


def perform_query(mongo, conditions=None, search=None, sort_by='new', options=None):
    """ Run a query against SteemQ Posts. """
    # apply conditions, such as time constraints
    conditions = conditions or {}
    conditions['created'] = {
        '$gte': dt.datetime.now() - dt.timedelta(days=90),
    }
    query = {
        **conditions,
    }
    projection = {
        '_id': 0,
        'title': 1,
        'author': 1,
        'body': 1,
        'permlink': 1,
        'identifier': 1,
        'created': 1,
        'pending_payout_value': 1,
        'total_payout_value': 1,
        'net_votes': 1,
        'net_rshares': 1,
        'author_reputation': 1,
        'json_metadata': 1,

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
