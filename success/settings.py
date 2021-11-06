import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(__file__)

HAS_SAML2 = False # supports the SSO interface provided by the Up2U project (www.up2uiversity.eu) ?
HAS_EARMASTER = False # supports import and processing of the data exported from the EarMaster application ?
PRIMARY_DOMAIN = 'success4all.commonspaces.eu'
SECONDARY_DOMAIN = None
TEST_DOMAIN = None

from commons.settings import *

SITE_ID = 4
SITE_NAME = 'SUCCESS4ALL'

WSGI_APPLICATION = 'success.wsgi.application'
ROOT_URLCONF = 'success.urls'

PROJECT_TITLE = 'SUCCESS4ALL - Supporting success for all people'
PROJECT_NAME = 'success'
LOGIN_REDIRECT_URL = 'success.home'
