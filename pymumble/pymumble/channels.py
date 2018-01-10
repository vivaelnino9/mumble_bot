# -*- coding: utf-8 -*-
import threading

from . import constants, messages
from .errors import UnknownChannelError


class Channels(dict):
    """
    Object that Stores all channels and their properties.
    """
    def __init__(self, mumble_object, callbacks):
        self.mumble_object = mumble_object
        self.callbacks = callbacks
        self.lock = threading.Lock()

    def update(self, message):
        """Update the channel informations based on an incoming message"""
        self.lock.acquire()

        if message.channel_id not in self:
            self[message.channel_id] = Channel(self.mumble_object, message)
            self.callbacks(constants.PYMUMBLE_CLBK_CHANNELCREATED,
                           self[message.channel_id])
        else:
            actions = self[message.channel_id].update(message)
            self.callbacks(constants.PYMUMBLE_CLBK_CHANNELUPDATED,
                           self[message.channel_id], actions)

        self.lock.release()

    def remove(self, channel_id):
        """Delete a channel when server signal the channel is removed"""
        self.lock.acquire()

        if channel_id in self:
            channel = self[channel_id]
            del self[channel_id]
            self.callbacks(constants.PYMUMBLE_CLBK_CHANNELREMOVED, channel)

        self.lock.release()

    def find_by_tree(self, tree):
        """
        Find a channel by its full path (a list with an element for each leaf)
        """
        if not getattr(tree, '__iter__', False):
            tree = tree  # function use argument as a list

        current = self[0]

        for name in tree:
            found = False
            for subchannel in self.get_children(current).values():
                if subchannel['name'] == name:
                    current = subchannel
                    found = True
                    break

            if not found:
                err = 'Cannot find channel {}'.format(tree)
                raise UnknownChannelError(err)

        return current

    def get_children(self, channel):
        """Get the children of a channel in a list"""
        children = []
        for child in self.values():
            if child.parent == channel.channel_id:
                children.append(child)
        return children

    def get_descendants(self, channel):
        """Get all the descendant of a channel, in nested lists"""
        descendants = []
        for subchannel in channel.get_children():
            descendants.append(subchannel.get_children())
        return descendants

    def get_tree(self, channel):
        """Get the whole list of channels, in a multidimensionnal list"""
        tree = []
        current = channel

        while current.channel_id != 0:
            tree.insert(0, current)
            current = self[current.channel_id]

        tree.insert(0, self[0])

        return tree

    def find_by_name(self, name):
        """Find a channel by name.  Stop on the first that match"""
        if name == '':
            return self[0]

        for channel in list(self.values()):
            if channel.name == name:
                return channel

        err = 'Channel {} does not exist'.format(name)
        raise UnknownChannelError(err)


class Channel:
    """
    Stores informations about one specific channel
    """
    def __init__(self, mumble_object, message):
        self.mumble_object = mumble_object
        self.channel_id = message.channel_id
        self.update(message)

    def __repr__(self):
        return '{}(channel_id={}, name={})'.format(
            self, self.channel_id, self.name
        )

    def update(self, message):
        """Update a channel based on an incoming message"""

        for (field, value) in message.ListFields():
            if field.name in ('session', 'actor', 'description_hash'):
                continue
            setattr(self, field.name, value)

        if message.HasField('description_hash'):
            setattr(self, 'description_hash',  message.description_hash)
            if message.HasField('description'):
                self.mumble_object.blobs[message.description_hash] = message.description
            else:
                self.mumble_object.blobs.get_channel_description(message.description_hash)

    def move(self, session=None):
        """
        Moves a specific user to the channel matching `self.channel_id`

        :param session: User to move. Moves the pymumble client if a user
                        session is not supplied.
        """
        if session is None:
            session = self.mumble_object.users.myself_session

        cmd = messages.MoveCommand(session, self.channel_id)
        self.mumble_object.execute_command(cmd)

    @property
    def users(self):
        """Returns list of users contained in a specific channel"""
        channel_users = []
        for user in self.mumble_object.users:
            u = self.mumble_object.users[user]
            if u.channel_id == self.channel_id:
                channel_users.append(u)

        return channel_users

    def send_text_message(self, message):
        """
        Sends a text message to the channel matching `self.channel_id`

        :param message: Text message to send to channel
        """
        session = self.mumble_object.users.myself_session

        cmd = messages.TextMessage(session, self.channel_id, message)
        self.mumble_object.execute_command(cmd)
