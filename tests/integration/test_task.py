import uuid

from tests.integration.base import BaseTest


class TestTasks(BaseTest):
    def test_post_task(self):
        """ POST new task """
        name = 'test_create_task_%s' % uuid.uuid4()
        task = {'name': name}

        total_before = self.db.task.count_documents({})
        response = self.app.post('tasks/', json=task)
        total_after = self.db.task.count_documents({})

        self.assertEqual(response.status_code, 201)
        self.assertEqual(total_after, total_before + 1)

    def test_post_existing_task(self):
        """ POST existing task does not create new """
        name = 'test_create_task_%s' % uuid.uuid4()
        task = {'name': name}

        # POST task
        self.app.post('tasks/', json=task)

        # POST again
        total_before = self.db.task.count_documents({})
        self.app.post('tasks/', json=task)
        total_after = self.db.task.count_documents({})

        self.assertEqual(total_after, total_before)

    def test_get_tasks(self):
        """ GET page of tasks """
        for i in range(10):
            name = 'test_get_tasks_%s' % uuid.uuid4()
            task = {'name': name}
            self.app.post('tasks/', json=task)

        for i in range(2):
            params = {'page': i + 1, 'size': 5}
            response = self.app.get('tasks/', params=params)

            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertEqual(len(data), 5)

    def test_get_tasks_empty(self):
        """ GET empty paged tasks """
        response = self.app.get('tasks/')

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 0)

    def test_get_task(self):
        """ GET task by name """
        name = 'test_create_task_%s' % uuid.uuid4()
        task = {'name': name}

        response = self.app.post('tasks/', json=task)
        data = response.json()

        response = self.app.get(f'tasks/{name}')

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), data)

    def test_get_task_404(self):
        """ GET non existent task returns 404 """
        response = self.app.get(f'tasks/huehue/')
        self.assertEqual(response.status_code, 404)

    def test_delete_task(self):
        """ DELETE task """
        name = 'test_create_task_%s' % uuid.uuid4()
        task = {'name': name}

        self.app.post('tasks/', json=task)

        total_before = self.db.task.count_documents({})
        response = self.app.delete(f'tasks/{name}/')
        total_after = self.db.task.count_documents({})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(total_after, total_before - 1)

    def test_delete_task_404(self):
        """ DELETE non existent task """
        response = self.app.delete(f'tasks/huehue/')
        self.assertEqual(response.status_code, 404)
