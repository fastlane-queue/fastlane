import uuid

from tests.integration.base import BaseTest


class TestGZip(BaseTest):
    def test_gzip(self):
        """ Tests GZip middleware """
        for i in range(100):
            name = 'test_create_task_%s' % uuid.uuid4()
            task = {'name': name}
            response = self.app.post('tasks/', json=task)

        headers = {'accept-encoding': 'gzip'}
        response = self.app.get('tasks', headers=headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn('content-encoding', response.headers)
        self.assertEqual(response.headers['content-encoding'], 'gzip')
