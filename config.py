import logging
from configparser import ConfigParser, ExtendedInterpolation

class Config(object):
    def __init__(self, config="config.ini"):
        self.config = ConfigParser(interpolation=ExtendedInterpolation(),
                                   allow_no_value=True)
        # don't lowercase section names
        self.config.optionxform = lambda option: option
        self.config.read([config])
        self.log = logging.getLogger('newsclips2.config')

    def __getitem__(self, domain):
        self.log.debug("  Getting config values for '%s'" % domain)
        values = dict(author='', medium='', media='', format='')
        values.update(dict(self.config.items(domain)))
        return values

    def sort_sections(self):
        """
        Yield section names in `len` descending order.
        """
        # longer sections should appear first because they'll be more
        # "unique."
        #
        # For example: If the URL is "lvrj.com/blogs/sherm" and the config
        # file contains both "lvrj.com/blogs/sherm" and "lvrj.com," we want
        # it to match with "lvrj.com/blogs/sherm" instead of just "lvrj.com."
        for section in sorted(self.config.sections(), key=len, reverse=True):
            yield section

    def find_config_values(self, url):
        """
        Given a URL, return its "xpath info" for how to parse.
        """
        for section in self.sort_sections():
            if section in url:
                return self[section]
