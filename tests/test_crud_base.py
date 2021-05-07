import uuid
from unittest import mock
from unittest import IsolatedAsyncioTestCase

from newlane.crud.base import Base


class TestCrudBase(IsolatedAsyncioTestCase):
    def setUp(self):
        Base.db = mock.Mock()
        Base.db.find = mock.AsyncMock()
        Base.db.save = mock.AsyncMock()
        Base.db.count = mock.AsyncMock()
        Base.db.find_one = mock.AsyncMock()

        self.sort = mock.Mock()
        self.model = mock.Mock()
        self.crud = Base(self.model, self.sort)

    def test_filters(self):
        """ Creates filters """
        self.model.a = 'nice'
        self.model.b = 'not nice'
        result = self.crud.filters(a='nice', b=123)
        expected = [True, False]
        self.assertListEqual(result, expected)

    async def test_create(self):
        """ Calls db.save with new object """
        await self.crud.create(nice='value')
        self.model.assert_called_once_with(nice='value')
        self.crud.db.save.assert_called_once()
        self.crud.db.save.assert_awaited()

    async def test_get(self):
        """ Calls db.find_one  """
        await self.crud.get(nice='value')
        self.crud.db.find_one.assert_called_once_with(self.model, mock.ANY)
        self.crud.db.find_one.assert_awaited()

    async def test_find(self):  
        """ Calls db.find """
        await self.crud.find(nice='value')
        self.crud.db.find\
            .assert_called_once_with(self.model, mock.ANY, sort=self.sort)
        self.crud.db.find.assert_awaited()

    async def test_count(self):  
        """ Calls db.count """
        self.crud.db.count = mock.AsyncMock()

        await self.crud.count(nice='value')
        self.crud.db.count.assert_called_once_with(self.model, mock.ANY)
        self.crud.db.count.assert_awaited()

    async def test_page(self):  
        """ Calls db.find with paged args """
        await self.crud.page(nice='value', page=2, size=5)
        self.crud.db.find.assert_called_once_with(
            self.model, 
            mock.ANY, 
            skip=5, 
            limit=5,
            sort=self.sort
        )
        self.crud.db.find.assert_awaited()

    async def test_save(self):
        """ Calls db.save """
        await self.crud.save(123)
        self.crud.db.save.assert_called_once_with(123)
        self.crud.db.save.assert_awaited()
