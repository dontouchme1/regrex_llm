from django.test import TestCase, Client
from django.urls import reverse
import io, pandas as pd

class TransformAPITests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_csv_email_redaction(self):
        df = pd.DataFrame([
            {"ID":1,"Name":"John","Email":"john.doe@example.com"},
            {"ID":2,"Name":"Jane","Email":"jane@site.org"},
        ])
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        buf.seek(0)

        payload = '{"instruction":"find email addresses","replacement":"REDACTED"}'
        resp = self.client.post(
            reverse('transform'),
            data={"file": buf, "payload": payload},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("regexUsed", data)
        self.assertIn("rows", data)
