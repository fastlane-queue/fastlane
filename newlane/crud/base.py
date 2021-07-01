from newlane import core


class Base(object):
    def __init__(self, model, sort=None):
        super(Base, self).__init__()
        self.model = model
        self.sort = sort

    @property
    def db(self):
        return core.get_db()

    def filters(self, **kwargs: dict) -> list:
        return [getattr(self.model, k) == v for k, v in kwargs.items()]

    async def create(self, **kwargs: dict):
        model = self.model(**kwargs)
        return await self.save(model)

    async def get(self, **kwargs: dict):
        queries = self.filters(**kwargs)
        return await self.db.find_one(self.model, *queries)

    async def find(self, **kwargs: dict):
        queries = self.filters(**kwargs)
        return await self.db.find(self.model, *queries, sort=self.sort)

    async def count(self, **kwargs: dict):
        queries = self.filters(**kwargs)
        return await self.db.count(self.model, *queries)

    async def page(self, page: int = 1, size: int = 10, **kwargs: dict):
        skip = (page - 1) * size
        queries = self.filters(**kwargs)
        return await self.db.find(
            self.model,
            *queries,
            skip=skip,
            limit=size,
            sort=self.sort
        )

    async def save(self, model):
        await self.db.save(model)
        return model

    async def delete(self, model):
        return await self.db.remove(model)
