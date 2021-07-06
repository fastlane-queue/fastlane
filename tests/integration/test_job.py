import uuid

from tests.integration.base import BaseTest


class TestJobs(BaseTest):
    def setUp(self):
        super().setUp()

        name = 'test_jobs_task_%s' % uuid.uuid4()
        task = {'name': name}
        response = self.app.post('/tasks/', json=task)
        assert response.status_code == 201, 'Failed to create base task'

        # We override the base_url so we can make requests while only being
        # concerned about the `jobs` part of the URL.
        # For example:
        #   Instead of calling `self.app.get('/tasks/{name}/jobs')`
        #   We simply call `self.app.get('jobs')`
        self.app.base_url += f'/tasks/{name}/'

    def test_post_job(self):
        """ POST new job """
        job = {'image': 'alpine', 'command': 'uname -a'}

        total_before = self.db.job.count_documents({})
        response = self.app.post('jobs/', json=job)
        total_after = self.db.job.count_documents({})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(total_after, total_before + 1)

    def test_post_job_task_404(self):
        """ POST job to non existent task return 404 """
        job = {'image': 'alpine', 'command': 'uname -a'}

        total_before = self.db.job.count_documents({})
        response = self.app.post('/tasks/huehue/jobs/', json=job)
        total_after = self.db.job.count_documents({})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(total_after, total_before)

    def test_get_job(self):
        """ GET a job """
        job = {'image': 'alpine', 'command': 'uname -a'}

        response = self.app.post('jobs/', json=job)
        data = response.json()

        url = 'jobs/%s' % data['id']
        response = self.app.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), data)

    def test_get_job_404(self):
        """ GET non existent job returns 404 """
        url = 'jobs/%s' % uuid.uuid4()
        response = self.app.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_jobs_empty(self):
        """ GET empty page of jobs """
        response = self.app.get('jobs')

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 0)

    def test_get_jobs(self):
        """ GET page of jobs """
        for i in range(10):
            job = {'image': 'alpine', 'command': 'uname -a'}
            self.app.post('jobs/', json=job)

        for i in range(2):
            params = {'page': i + 1, 'size': 5}
            response = self.app.get('jobs/', params=params)

            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertEqual(len(data), 5)
