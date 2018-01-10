from threading import Lock

from . import constants


class Command:
    """
    Define a command object, used to ask an action from the pymumble thread,
    usually to forward to the murmur server
    """
    def __init__(self):
        self.cmd_id = None
        self.lock = Lock()

        self.cmd = None
        self.parameters = None
        self.response = None


class MoveCommand(Command):
    """Command to move a user from channel"""
    def __init__(self, session, channel_id):
        Command.__init__(self)

        self.cmd = constants.PYMUMBLE_CMD_MOVE
        self.parameters = {
            'session': session,
            'channel_id': channel_id
        }


class TextMessage(Command):
    """Command to send a text message"""
    def __init__(self, session, channel_id, message):
        Command.__init__(self)

        self.cmd = constants.PYMUMBLE_CMD_TEXTMESSAGE
        self.parameters = {
            'session': session,
            'channel_id': channel_id,
            'message': message
        }


class TextPrivateMessage(Command):
    """Command to send a private text message"""
    def __init__(self, session, message):
        Command.__init__(self)

        self.cmd = constants.PYMUMBLE_CMD_TEXTPRIVATEMESSAGE
        self.parameters = {
            'session': session,
            'message': message
        }


class ModUserState(Command):
    """Command to change a user state"""
    def __init__(self, session, params):
        Command.__init__(self)

        self.cmd = constants.PYMUMBLE_CMD_MODUSERSTATE
        self.parameters = params
