import os
from urllib.parse import urlparse


class createDep:

    def path(self):
        # Use os.path.join for cross-platform compatibility
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'crowl', 'data')

    def url_to_name(self, url):
        t = urlparse(url).netloc
        # Handle URLs without www prefix
        if not t:
            t = url.replace('http://', '').replace('https://', '').split('/')[0]
        return '.'.join(t.split('.')[-2:]).replace('.', '-')

    def mkdir(self, url):
        try:
            # Create the base directory if it doesn't exist
            base_path = self.path()
            if not os.path.exists(base_path):
                os.makedirs(base_path, exist_ok=True)

            # Create the project directory
            project_path = os.path.join(base_path, self.url_to_name(url))
            if not os.path.exists(project_path):
                os.makedirs(project_path, exist_ok=True)

            print(f"Created directory: {project_path}")
            return project_path
        except OSError as error:
            print(f"Error creating directory: {error}")
            return None

    def pathProject(self, url):
        # Use os.path.join for cross-platform compatibility
        return os.path.join(self.path(), self.url_to_name(url))
