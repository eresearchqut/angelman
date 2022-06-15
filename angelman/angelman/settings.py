# flake8: noqa
import os

from rdrf.settings import *
import angelman


FALLBACK_REGISTRY_CODE = "angelman"
LOCALE_PATHS = env.getlist("locale_paths", ['/data/translations/locale'])

# Adding the angelman app first, so that its templates overrides base templates
INSTALLED_APPS = [
    FALLBACK_REGISTRY_CODE,
] + INSTALLED_APPS

ROOT_URLCONF = '%s.urls' % FALLBACK_REGISTRY_CODE

SEND_ACTIVATION_EMAIL = False

RECAPTCHA_SITE_KEY = env.get("recaptcha_site_key", "")
RECAPTCHA_SECRET_KEY = env.get("recaptcha_secret_key", "")

PROJECT_TITLE = env.get("project_title", "Global Angelman Syndrome Registry")
PROJECT_TITLE_LINK = "login_router"

PROJECT_LOGO = env.get("project_logo", "images/logo.png")

VERSION = env.get('app_version', '%s (ang)' % angelman.VERSION)

REGISTRATION_FORM = "angelman.forms.angelman_registration_form.ANGRegistrationForm"
REGISTRATION_CLASS = "angelman.registry.groups.registration.angelman_registration.AngelmanRegistration"

CSP_FRAME_SRC += ["https://www.youtube.com", "https://angelmanregistry.info", "https://www.angelmanregistry.info"]
CSP_OBJECT_SRC += ["https://angelmanregistry.info", "https://www.angelmanregistry.info"]

SECURITY_WHITELISTED_URLS += (
    "parent_edit",
    "parent_page",
)

# SYSTEM_ROLE = SystemRoles.NORMAL

PASSWORD_EXPIRY_DAYS = env.get("password_expiry_days", 0)
PASSWORD_EXPIRY_WARNING_DAYS = env.get("password_expiry_warning_days", 0)
ACCOUNT_EXPIRY_DAYS = env.get("account_expiry_days", 0) 
