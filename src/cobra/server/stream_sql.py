'''Stream SQL processor, to filter and transform messages when subcribing.

Copyright (c) 2018-2019 Machine Zone, Inc. All rights reserved.
'''

import collections
import logging

StreamSQLExpression = collections.namedtuple(
    'StreamSQLExpression', [
        'components', 'val', 'length',
        'equalExpression',
        'likeExpression',
        'differentExpression',
        'largerThanExpression',
        'lowerThanExpression'
    ]
)


class InvalidStreamSQLError(Exception):
    pass


class StreamSqlFilter:
    def __init__(self, sql_filter):
        '''
        Support expression on strings, bool, int
        Support AND and OR expressions

        No parenthesis support
        '''

        self.emptyFilter = False
        self.channel = None

        if sql_filter is None:
            raise InvalidStreamSQLError()

        # Basic validation
        tokens = [token.strip() for token in sql_filter.split()]

        validSql = len(tokens) >= 4 and \
            tokens[0].lower() == 'select' and \
            tokens[2].lower() == 'from'

        if not validSql:
            raise InvalidStreamSQLError()

        # Parse glob
        if tokens[1] == '*':
            self.fields = None
        else:
            self.fields = tokens[1]

        # Parse channel name
        self.channel = tokens[3].replace('`', '')

        if len(tokens) == 4:
            self.emptyFilter = True
            return

        if 'where' in sql_filter:
            whereStatement = 'where'
        elif 'WHERE' in sql_filter:
            whereStatement = 'WHERE'
        else:
            self.emptyFilter = True
            return

        _, _, sql_filter = sql_filter.partition(whereStatement)

        sql_filter = sql_filter.replace('\n', ' ')

        # Since we don't have a legit lexer, we need spaces around our
        # OR and AND ...
        # FIXME: we should figure out how to use ply
        self.andExpr = True
        if ' AND ' in sql_filter or ' OR ' in sql_filter:
            if ' AND ' in sql_filter:
                exprs = sql_filter.split(' AND ')
            elif ' OR ' in sql_filter:
                exprs = sql_filter.split(' OR ')
                self.andExpr = False

            exprs = [expr.strip() for expr in exprs]
            self.expressions = [self.buildExpression(expr) for expr in exprs]
        else:
            self.expressions = [self.buildExpression(sql_filter)]

    def buildExpression(self, text):
        '''
        FIXME: support lower than and greater than for ints
               support float ?
        '''

        equalExpression = False
        likeExpression = False
        differentExpression = False
        largerThanExpression = False
        lowerThanExpression = False

        if ' LIKE ' in text:
            jsonExpr, _, val = text.partition(' LIKE ')
            likeExpression = True
        elif ' != ' in text:
            jsonExpr, _, val = text.partition(' != ')
            differentExpression = True
        elif ' = ' in text:
            jsonExpr, _, val = text.partition('=')
            equalExpression = True
        elif ' > ' in text:
            jsonExpr, _, val = text.partition('>')
            largerThanExpression = True
        elif ' < ' in text:
            jsonExpr, _, val = text.partition('<')
            lowerThanExpression = True
        else:
            raise InvalidStreamSQLError('Invalid operand')

        self.jsonExpr = jsonExpr.strip()

        val = val.strip()
        if val.startswith("'") and val.endswith("'"):
            val = val.replace("'", '')
        elif val == 'true' or val == 'false':
            val = val == 'true'
        else:
            try:
                val = int(val)
            except ValueError:
                raise InvalidStreamSQLError()

        components = self.jsonExpr.split('.')
        return StreamSQLExpression(components, val, len(components),
                                   equalExpression,
                                   likeExpression,
                                   differentExpression,
                                   largerThanExpression,
                                   lowerThanExpression)

    def matchExpression(self, msg, expression):
        if expression.length == 2:
            val = msg.get(expression.components[0], {}).get(expression.components[1])  # noqa
            return self.matchOperand(val, expression)
        elif expression.length == 1:
            val = msg.get(expression.components[0])
            return self.matchOperand(val, expression)
        else:
            msgCopy = dict(msg)

            for component in expression.components:
                msgCopy = msgCopy.get(component, {})

            return self.matchOperand(msgCopy, expression)

    def matchOperand(self, val, expression):
        if expression.equalExpression:
            return expression.val == val
        elif expression.likeExpression:
            return expression.val in val
        elif expression.differentExpression:
            return expression.val != val
        elif expression.largerThanExpression:
            return val > expression.val
        elif expression.lowerThanExpression:
            return val < expression.val

    def match(self, msg):
        if self.emptyFilter:
            return self.transform(msg)

        if isinstance(msg, list):
            msg = msg[0]

        if not isinstance(msg, dict):
            logging.error('Bad type for {}'.format(msg))
            return False

        if self.andExpr:
            if not all(self.matchExpression(msg, expression) for expression in self.expressions):  # noqa
                return False
            else:
                return self.transform(msg)
        else:
            if not any(self.matchExpression(msg, expression) for expression in self.expressions):  # noqa
                return False
            else:
                return self.transform(msg)

    def transform(self, msg):
        '''extract a subfield'''

        if self.fields is None:
            return msg

        ret = {}
        fields = self.fields.split(',')
        for field in fields:
            subtree = dict(msg)
            fieldsComponents = field.split('.')
            for component in fieldsComponents:
                subtree = subtree.get(component, {})

            ret.update({field: subtree})

        return ret


def match_stream_sql_filter(sql_filter, msg):
    try:
        f = StreamSqlFilter(sql_filter)
        return f.match(msg)
    except InvalidStreamSQLError:
        return False
