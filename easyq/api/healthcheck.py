from flask import Blueprint, current_app

bp = Blueprint('healthcheck', __name__, url_prefix='/healthcheck')


@bp.route('/', methods=('GET', ))
def healthcheck():
    res = current_app.redis.ping()
    assert res, 'Connection to redis failed.'

    return 'WORKING'
