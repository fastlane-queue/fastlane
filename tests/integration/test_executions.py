import uuid

from tests.integration.base import BaseTest


class TestExecution(BaseTest):
    def setUp(self):
        super().setUp()

        task_name = 'test_jobs_task_%s' % uuid.uuid4()
        task = {'name': task_name}
        response = self.app.post('/tasks/', json=task)
        assert response.status_code == 201, 'Failed to create base task'

        job = {'image': 'alpine', 'command': 'uname -a'}
        response = self.app.post(f'/tasks/{task_name}/jobs/', json=job)
        assert response.status_code == 201, 'Failed to create base job'
        data = response.json()

        job_id = data['id']
        self.app.base_url += f'/tasks/{task_name}/jobs/{job_id}/'

    def test_post_execution(self):
        """ POST new execution """
        total_before = self.db.execution.count_documents({})
        response = self.app.post('executions/')
        total_after = self.db.execution.count_documents({})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(total_after, total_before + 1)

    def test_get_execution(self):
        """ GET a execution """
        response = self.app.post('executions/')
        data = response.json()

        url = 'executions/%s' % data['id']
        response = self.app.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), data)

    def test_get_execution_404(self):
        """ GET non existent execution returns 404 """
        url = 'executions/%s' % uuid.uuid4()
        response = self.app.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_executions_empty(self):
        """ GET empty page of executions """
        response = self.app.get('executions')

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 0)

    def test_get_executions(self):
        """ GET page of executions """
        for i in range(10):
            self.app.post('executions/')

        for i in range(2):
            params = {'page': i + 1, 'size': 5}
            response = self.app.get('executions/', params=params)

            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertEqual(len(data), 5)
