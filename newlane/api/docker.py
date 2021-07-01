from fastapi import APIRouter

from newlane import core


router = APIRouter(prefix='/docker')


@router.get('/containers/')
async def get_containers():
    docker = core.get_docker()
    return docker.containers.list()


@router.post('/prune/')
async def post_prune():
    docker = core.get_docker()
    return docker.containers.prune()
