from unittest import mock
from unittest import IsolatedAsyncioTestCase

from fastapi import HTTPException

from newlane.crud.crud import Crud


class TestCrudBase(IsolatedAsyncioTestCase):
    def setUp(self):
        self.sort = mock.Mock()
        self.model = mock.Mock()
        self.crud = Crud(self.model, self.sort)
    
    async def test_get_or_404(self):
        """ Gets value when in db """
        self.crud.get = mock.AsyncMock(return_value='not None')
        result = await self.crud.get_or_404(nice='value')
        self.assertEqual(result, 'not None')
        self.crud.get.assert_called_once_with(nice='value')
        self.crud.get.assert_awaited()
    
    async def test_get_or_404_error(self):
        """ Raises HTTPException when not in db """
        self.model.__name__ = 'Name'
        self.crud.get = mock.AsyncMock(return_value=None)  # force error
        
        with self.assertRaises(HTTPException) as error:
            await self.crud.get_or_404(nice='value')
        
        self.crud.get.assert_awaited()
        self.assertEqual(error.exception.status_code, 404)
        self.assertEqual(error.exception.detail, 'Name not found')

    async def test_get_or_create(self):
        """ Gets value when in db """
        self.crud.get = mock.AsyncMock(return_value='not None')
        result = await self.crud.get_or_create(nice='value')
        self.assertEqual(result, 'not None')
        self.crud.get.assert_called_once_with(nice='value')
        self.crud.get.assert_awaited()
    
    async def test_get_or_create_create(self):
        """ Create value when not in db """
        self.crud.get = mock.AsyncMock(return_value=None)  # force error
        self.crud.create = mock.AsyncMock(return_value='nice')  # anything
        result = await self.crud.get_or_create(nice='value')
        self.assertEqual(result, 'nice')
        self.crud.get.assert_called_once_with(nice='value')
        self.crud.get.assert_awaited()
        self.crud.create.assert_called_once_with(nice='value')
        self.crud.create.assert_awaited()