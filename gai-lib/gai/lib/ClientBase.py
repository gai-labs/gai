import os
import gai.common.ConfigHelper as ConfigHelper

class ClientBase:

    def __init__(self, config_path=None):
        if config_path:
            self.config = ConfigHelper.get_lib_config(config_path)
        else:
            self.config = ConfigHelper.get_lib_config()
        self.base_url = self.config["gai_url"]

    def _gen_url(self, generator):
        url = os.path.join(self.base_url,
                           self.config["generators"][generator]["url"].lstrip('/'))
        return url
