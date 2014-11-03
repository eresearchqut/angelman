from django.forms import widgets
import logging

logger = logging.getLogger("registry_log")


class CreatePatientWidget(widgets.Widget):
    def render(self, name, value, attrs=None):
        logger.debug("name = %s" % name)
        logger.debug("value = %s" % value)
        logger.debug("attrs = %s" % attrs)
        if value is None:
            return """<input type="button" value="Create Patient"/>"""
        else:
            return """<a href='http://www.smh.com.au">Patient in registry</a>"""

