import logging
from configparser import ConfigParser, ExtendedInterpolation

class Config(object):
    def __init__(self, config="config.ini"):
        self.config = ConfigParser(interpolation=ExtendedInterpolation(),
                                   allow_no_value=True)
        # don't lowercase section names
        self.config.optionxform = lambda option: option
        self.config.read([config])
        self.log = logging.getLogger('newsclips.config')

    def staff(self):
        """
        TODO: Document this
        """
        staff = {}
        for k, v in self.config.items("staff"):
            staff[k] = v.split(', ')
        return staff

    def __getitem__(self, line):
        for section in self.sort_sections():
            if section in line:
                return dict(self.config.items(section))

        return {}

    def sort_sections(self):
        """
        Yield section names in length descending order.
        """
        # longer sections should appear first because they'll be more
        # "unique."
        #
        # For example: If the URL is "lvrj.com/blogs/sherm" and the config
        # file contains both "lvrj.com/blogs/sherm" and "lvrj.com," we want
        # it to match with "lvrj.com/blogs/sherm" instead of just "lvrj.com."
        for section in sorted(self.config.sections(), key=len, reverse=True):
            yield section
