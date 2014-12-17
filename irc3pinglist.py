###
# Copyright (c) 2014, Pierre-Yves Chibon
# Copyright (c) 2007, Mike McGrath
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###

import logging
import urllib
import re
import textwrap

from datetime import datetime

import irc3

from irc3d import IrcServer
from irc3.compat import asyncio
from irc3.plugins.command import command


def _validate_listname(name):
    """ Validate that a provided listname matches the required criterias.
    """
    listname_regex = re.compile(r'\A\w+\Z')
    if not listname_regex.match(name):
        return False
    return True


def _nick_match(nick1, nick2):
    """ Return whether two given nick are matching or not.
    We will consider them matching is nick2 is nick1 + '_'
    """
    if nick1 == nick2:
        return True

    if re.match(r'%s[-_|]' % re.escape(nick1), nick2):
        return True

    return False


@irc3.plugin
class Pinglist(object):
    """ Plugin allowing to ping a list of users.
    """

    requires = [
        'irc3.plugins.core',
        'irc3.plugins.command',
        'irc3.plugins.storage',
    ]

    def __init__(self, bot):
        self.bot = bot

        koji_url = bot.config['koji']['url']
        self.koji_client = koji.ClientSession(koji_url, {})

    @command
    def add(self, mask, target, args):
        """add <listname> [<nick> ...]

        Adds a list of nicks to <listname>.  If no nicks are given, adds
        the caller's nick to the list.

            %%add <listname> [<nick> ...]
        """
        listname = args['<listname>']
        try:
            pinglist = self.bot.db[listname]
        except KeyError:
            msg = 'No such ping list.'
            self.bot.privmsg(target, '%s: %s' % (mask.nick, msg))
            return

        if nicks is None:
            nicks = set([mask.nick])
        else:
            nicks = set(nicks)
            for nick in nicks:
                if not ircutils.isNick(nick):
                    msg = 'Invalid nick: %s' % nick
                    self.bot.privmsg(target, '%s: %s' % (mask.nick, msg))
                    return

        self.bot.db[listname].update(nicks)

        msg = 'Nick(s) successfully added.'
        self.bot.privmsg(target, '%s: %s' % (mask.nick, msg))

    @command
    def remove(self, mask, target, args):
        """remove <listname> [<nick> ...]

        Removes a list of nicks to <listname>.  If no nicks are given,
        removes the caller's nick to the list.

            %%remove <listname> [<nick> ...]
        """
        listname = args['<listname>']
        try:
            pinglist = self.bot.db[listname]
        except KeyError:
            msg = 'No such ping list.'
            self.bot.privmsg(target, '%s: %s' % (mask.nick, msg))
            return

        if nicks is None:
            nicks = set([mask.nick])
        else:
            nicks = set(nicks)
            for nick in nicks:
                if not ircutils.isNick(nick):
                    msg = 'Invalid nick: %s' % nick
                    self.bot.privmsg(target, '%s: %s' % (mask.nick, msg))
                    return

        self.bot.db[listname].difference_update(nicks)

        msg = 'Nick(s) successfully removed.'
        self.bot.privmsg(target, '%s: %s' % (mask.nick, msg))

    @command
    def create(self, mask, target, args):
        """Creates a new pinglist called <listname>.  An optional list of
        initial nicks may be given.

            %%create <listname> [<nick> ...]
        """
        listname = args['<listname>']

        if not _validate_listname(listname):
            msg = 'List names can only contain alphanumeric characters.'
            self.bot.privmsg(target, '%s: %s' % (mask.nick, msg))
            return

        if nicks is None:
            nick = set()
        else:
            nicks = set(nicks)
            for nick in nicks:
                if not ircutils.isNick(nick):
                    irc.error('Invalid nick: %s' % nick)
                    return

        self.bot.db[listname].difference_update(nicks)

        msg = 'Pinglist %s added.' % listname
        self.bot.privmsg(target, '%s: %s' % (mask.nick, msg))

    @command
    def delete(self, mask, target, args):
        '''Deletes <listname>

            %%delete <listname>
        '''
        listname = args['<listname>']

        if not listname in self.bot.db:
            msg = 'No such ping list.'
            self.bot.privmsg(target, '%s: %s' % (mask.nick, msg))
            return

        del self.bot.db[listname]

        msg = 'Pinglist %s deleted.' % listname
        self.bot.privmsg(target, '%s: %s' % (mask.nick, msg))

    @command
    def show(self, mask, target, args):
        '''Shows the members of <listname>.

            %%show <listname>
        '''
        listname = args['<listname>']

        try:
            pinglist = self.bot.db[listname]
        except KeyError:
            msg = 'No such ping list.'
            self.bot.privmsg(target, '%s: %s' % (mask.nick, msg))
            return

        message = ' '.join(sorted(pinglist))

        message = textwrap.wrap(message,
            width=256, break_long_words=False, break_on_hyphens=False)

        msg = 'Members of %s: ' % listname
        self.bot.privmsg(target, '%s: %s' % (mask.nick, msg))
        for line in message:
            self.bot.privmsg(target, line)

    @command
    def pinglists(self, mask, target, args):
        ''' Displays a list of all ping lists.

            %%pinglists
        '''

        message = 'Current ping lists: '
        self.bot.privmsg(target, '%s: %s' % (mask.nick, message))
        message = ' '.join(sorted(self.bot.db.keys()))

        ping_message = textwrap.wrap(message,
            width=256, break_long_words=False, break_on_hyphens=False)

        for msg in ping_message:
            self.bot.privmsg(target, msg)

    @command
    def doping(self, mask, target, args):
        ''' Pings all of the members of the <listname> in <channel> with
        <message>.  If no channel is specified, the ping occurs in the
        channel that this was called in.

            %%doping <listname> [<channel>] <message>
        '''

        listname = args['<listname>']
        channel = args.get('<channel>', None)
        message = args['<message']

        if channel is not None:
            target = channel

        try:
            pinglist = self.bot.db[listname]
        except KeyError:
            msg = 'No such ping list.'
            self.bot.privmsg(target, '%s: %s' % (mask.nick, msg))
            return

        if not pinglist:
            msg = 'Ping list is empty.'
            self.bot.privmsg(target, '%s: %s' % (mask.nick, msg))
            return

        # Handle matching of away/status nicks.
        ping_set = set(pinglist)
        for nick in pinglist:
            for nick2 in irc.state.channels[target].users:
                if nick == nick2:
                    continue
                if _nick_match(nick, nick2):
                    ping_set.add(nick2)
        pinglist = sorted(ping_set)

        ping_message = textwrap.wrap(' '.join(pinglist),
            width=256, break_long_words=False, break_on_hyphens=False)

        for line in ping_message:
            self.bot.privmsg(target, line)


def main():
    # logging configuration
    logging.config.dictConfig(irc3.config.LOGGING)

    loop = asyncio.get_event_loop()

    server = IrcServer.from_argv(loop=loop)
    bot = irc3.IrcBot.from_argv(loop=loop).run()

    loop.run_forever()


if __name__ == '__main__':
    main()
