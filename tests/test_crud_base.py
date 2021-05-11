from unittest import mock
from unittest import IsolatedAsyncioTestCase

from newlane.crud.base import Base


class MockDb(object):
    """ Used to mock the `odmantic.AIOEngine` instance """
    async def find(): pass
    async def find_one(): pass
    async def save(): pass
    async def count(): pass


def Mock():
    """ Just a callable to return a new mock """
    return mock.Mock(MockDb)


@mock.patch('newlane.crud.base.Base.db', new_callable=Mock)
class TestCrudBase(IsolatedAsyncioTestCase):
    def setUp(self):
        self.sort = mock.Mock()
        self.model = mock.Mock()
        self.crud = Base(self.model, self.sort)

    def test_filters(self, _):
        """ Creates filters """
        self.crud.model.a = 'nice'
        self.crud.model.b = 'not nice'
        result = self.crud.filters(a='nice', b=123)
        expected = [True, False]
        self.assertListEqual(result, expected)

    async def test_create(self, db):
        """ Calls db.save with new object """
        await self.crud.create(nice='value')
        self.model.assert_called_once_with(nice='value')
        db.save.assert_called_once_with(mock.ANY)
        db.save.assert_awaited()

    async def test_get(self, db):
        """ Calls db.find_one  """
        await self.crud.get(nice='value')
        db.find_one.assert_called_once_with(self.model, mock.ANY)
        db.find_one.assert_awaited()

    async def test_find(self, db):
        """ Calls db.find """
        await self.crud.find(nice='value')
        db.find.assert_called_once_with(self.model, mock.ANY, sort=self.sort)
        db.find.assert_awaited()

    async def test_count(self, db):
        """ Calls db.count """
        await self.crud.count(nice='value')
        db.count.assert_called_once_with(self.model, mock.ANY)
        db.count.assert_awaited()

    async def test_page(self, db):
        """ Calls db.find with paged args """
        await self.crud.page(nice='value', page=2, size=5)
        db.find.assert_called_once_with(
            self.model,
            mock.ANY,
            skip=5,
            limit=5,
            sort=self.sort
        )
        db.find.assert_awaited()

    async def test_save(self, db):
        """ Calls db.save """
        await self.crud.save(123)
        db.save.assert_called_once_with(123)
        db.save.assert_awaited()
