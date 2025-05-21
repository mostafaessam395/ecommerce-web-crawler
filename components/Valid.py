import os.path
from os import path
import shutil


class ValidAction:
    def projectIsset(self, file):
        if path.exists(file):
            return True
        return False

    def checkCrawlCache(self, root):
        # Get the base directory of the project
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Use os.path.join for cross-platform compatibility
        dirName = os.path.join(base_dir, 'crawls', 'crowl', 'data', root)
        print(f"Checking crawl cache: {dirName}")

        if path.exists(dirName):
            print(f"Removing existing crawl cache: {dirName}")
            shutil.rmtree(dirName)

        # Also check the data directory
        data_dir = os.path.join(base_dir, 'crowl', 'data', root)
        if path.exists(data_dir):
            print(f"Removing existing data directory: {data_dir}")
            shutil.rmtree(data_dir)
