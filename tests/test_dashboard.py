import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

class DashboardTests(unittest.TestCase):
    def test_run_and_change_controls(self):
        app = AppTest.from_file(str(Path(__file__).parents[1]/'src/lastmile/dashboard.py'), default_timeout=60).run()
        self.assertFalse(app.exception)
        app.slider[0].set_value(1)
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.metric),3)
        self.assertEqual(len(app.dataframe),2)
        app.slider[1].set_value(60)
        app.multiselect[0].set_value(['normal'])
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.dataframe[0].value.iloc[0]['fleet'],60)
