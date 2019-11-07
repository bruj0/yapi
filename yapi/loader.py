
import logging
import os.path
import yaml

logger = logging.getLogger(__name__)


class yaml_loader():
    def load(self,filename):
        """
        Load a yaml file and expect only one document

        Args:
            filename (str): path to document

        Returns:
            dict: content of file
        """
        try:
            with open(filename, "r") as fileobj:
                try:
                    contents = yaml.load(fileobj, Loader=yaml.SafeLoader)
                except yaml.composer.ComposerError as e:
                    logger.exception(e)
                    exit(1)
        except FileNotFoundError:
            logger.error(f"File not found: {filename}")
            exit(1)
        #logger.debug(f"contents=\n{contents}")
        return contents