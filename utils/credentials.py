from typing import Optional
from os import path
import ssl
from apns2.credentials import Credentials

# Work out where our certificates are.
cert_loc = path.join(path.dirname(__file__), 'certs.pem')


class MissingCertFile(Exception):
    """
    The certificate file could not be found.
    """
    pass


def init_context(cert_path=None, cert=None, cert_password=None):
    """
    Create a new ``SSLContext`` that is correctly set up for an HTTP/2
    connection. This SSL context object can be customized and passed as a
    parameter to the :class:`HTTPConnection <hyper.HTTPConnection>` class.
    Provide your own certificate file in case you don’t want to use hyper’s
    default certificate. The path to the certificate can be absolute or
    relative to your working directory.

    :param cert_path: (optional) The path to the certificate file of
        “certification authority” (CA) certificates
    :param cert: (optional) if string, path to ssl client cert file (.pem).
        If tuple, ('cert', 'key') pair.
        The certfile string must be the path to a single file in PEM format
        containing the certificate as well as any number of CA certificates
        needed to establish the certificate’s authenticity. The keyfile string,
        if present, must point to a file containing the private key in.
        Otherwise the private key will be taken from certfile as well.
    :param cert_password: (optional) The password argument may be a function to
        call to get the password for decrypting the private key. It will only
        be called if the private key is encrypted and a password is necessary.
        It will be called with no arguments, and it should return a string,
        bytes, or bytearray. If the return value is a string it will be
        encoded as UTF-8 before using it to decrypt the key. Alternatively a
        string, bytes, or bytearray value may be supplied directly as the
        password argument. It will be ignored if the private key is not
        encrypted and no password is needed.
    :returns: An ``SSLContext`` correctly set up for HTTP/2.
    """
    cafile = cert_path or cert_loc
    if not cafile or not path.exists(cafile):
        err_msg = ("No certificate found at " + str(cafile) + ". Either " +
                   "ensure the default cert.pem file is included in the " +
                   "distribution or provide a custom certificate when " +
                   "creating the connection.")
        raise MissingCertFile(err_msg)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.set_default_verify_paths()
    context.load_verify_locations(cafile=cafile)
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    # required by the spec
    context.options |= ssl.OP_NO_COMPRESSION

    if cert is not None:
        try:
            basestring
        except NameError:
            basestring = (str, bytes)
        if not isinstance(cert, basestring):
            context.load_cert_chain(cert[0], cert[1], cert_password)
        else:
            context.load_cert_chain(cert, password=cert_password)

    return context


# Credentials subclass for certificate authentication
class CertificateCredentials(Credentials):
    def __init__(self, cert_file: Optional[str] = None, password: Optional[str] = None,
                 cert_chain: Optional[str] = None) -> None:
        ssl_context = init_context(cert=cert_file, cert_password=password)
        if cert_chain:
            ssl_context.load_cert_chain(cert_chain)
        super(CertificateCredentials, self).__init__(ssl_context)
