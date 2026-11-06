import os
from app import init_db
import st_ui

DB_PATH = os.path.join(os.path.dirname(__file__), 'foodie_delight.db')
init_db()

st_ui.render_streamlit_interface(DB_PATH)
