from pyftpdlib.handlers import FTPHandler


class PermissiveFTPHandler(FTPHandler):
    """
    FTP handler subclass that permits foreign addresses for active PORT
    commands. Use only when you need to support clients using active FTP
    behind NAT that advertise a different IP. This can be a security risk -
    prefer passive mode instead.
    """

    permit_foreign_addresses = True
