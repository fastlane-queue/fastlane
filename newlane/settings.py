from pydantic import BaseSettings, RedisDsn, AnyUrl

class Settings(BaseSettings):
    mongo: AnyUrl = 'mongodb://localhost:27017'
    redis: RedisDsn = 'redis://localhost:6379'
    docker: str = 'tcp://localhost:2376'

settings = Settings()