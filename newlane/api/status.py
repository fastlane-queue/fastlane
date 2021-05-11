from fastapi import APIRouter

from newlane import core

router = APIRouter(prefix='/status')


@router.get('/')
async def get_status():
    docker = core.get_docker().info()
    redis = core.get_queue().connection.ping()
    db = await core.get_db().client.server_info()
    return {
        'redis': redis,
        'docker': docker != {},
        'mongo': db.get('ok', 0.0) != 0.0,
    }
