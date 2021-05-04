from pydantic import BaseSettings, RedisDsn, AnyUrl


class Settings(BaseSettings):
    mongo: AnyUrl = 'mongodb://localhost:27017'
    redis: RedisDsn = 'redis://localhost:6379'
    docker: AnyUrl = 'tcp://localhost:2375'


settings = Settings()
