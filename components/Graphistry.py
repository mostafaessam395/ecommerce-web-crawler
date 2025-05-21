import graphistry, os, streamlit as st, streamlit.components.v1 as components
import logging
from graphistry import PyGraphistry

# Create a simple logger instead of importing from util
logger = logging.getLogger(__name__)

try:
    logger.debug('Using graphistry version: %s', graphistry.__version__)
except Exception as e:
    logger.warning(f"Error loading graphistry version: {str(e)}")


class GraphistrySt:

    def __init__(self, overrides={}):
        graphistry.register(api=3, personal_key_id='CZSF3TG59H',
                            personal_key_secret='IEYZ2FWQ6FW436FR')

    def render_url(self, url):
        try:
            if self.test_login():
                logger.debug('rendering main area, with url: %s', url)
                # Use a more reliable way to display the graph
                st.markdown(f"""
                <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
                    <h3>Network Graph Visualization</h3>
                    <p>The graph visualization should appear below. If it doesn't load, you may need to:</p>
                    <ul>
                        <li>Check your internet connection</li>
                        <li>Ensure you have crawled enough data</li>
                        <li>Try refreshing the page</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

                try:
                    components.iframe(
                        src=url,
                        height=800,
                        scrolling=True
                    )
                except Exception as e:
                    st.error(f"Error displaying graph: {str(e)}")
                    st.markdown(f"You can try opening the graph directly at: [{url}]({url})")
        except Exception as e:
            st.error(f"Error rendering graph: {str(e)}")
            st.info("This may happen if the crawler hasn't generated enough data yet. Please wait for it to complete.")

    def plot(self, g):
        try:
            if PyGraphistry._is_authenticated:
                url = g.plot(as_files=True, render=False)  # TODO: Remove as_files=True when becomes default
                self.render_url(url)
            else:
                st.warning("""
                    Graphistry not authenticated. The network visualization requires authentication.

                    You can still use the other visualizations and data analysis features.
                """)
        except Exception as e:
            st.error(f"Error plotting graph: {str(e)}")
            st.info("This may happen if the crawler hasn't generated enough data yet. Please wait for it to complete.")

    def test_login(self, verbose=True):
        try:
            graphistry.register()
            return True
        except Exception as e:  # Catch specific exception
            if verbose:
                st.warning(f"""
                Not logged in for Graphistry plots: {str(e)}

                You can still use the other visualizations and data analysis features.
                """)
            return False

# Don't initialize the class here - it will be initialized when imported
# GraphistrySt()
