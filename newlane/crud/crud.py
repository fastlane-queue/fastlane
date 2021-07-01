from fastapi import HTTPException

from .base import Base


class Crud(Base):
    async def get_or_404(self, **kwargs):
        model = await self.get(**kwargs)

        if model is None:
            detail = f'{self.model.__name__} not found'
            raise HTTPException(status_code=404, detail=detail)

        return model

    async def get_or_create(self, **kwargs):
        model = await self.get(**kwargs)

        if model is None:
            return await self.create(**kwargs)

        return model
