import os
import ssl
import certifi

def ssl_hook():
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['SSL_CERT_DIR'] = os.path.dirname(certifi.where())
    try:
        ssl.create_default_context()
    except:
        pass

ssl_hook()