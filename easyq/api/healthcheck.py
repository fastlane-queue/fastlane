from flask import Blueprint, current_app, jsonify

from easyq.models import db

bp = Blueprint('healthcheck', __name__, url_prefix='/healthcheck')


@bp.route('/', methods=('GET', ))
def healthcheck():
    status = {
        'redis': True,
        'mongo': True,
        'errors': [],
    }
    try:
        res = current_app.redis.ping()
        assert res, f'Connection to redis failed ({res}).'
    except Exception as err:
        status['errors'].append({"source": "redis", "message": str(err)})
        status['redis'] = False

    try:
        res = tuple(db.connection.easyq.jobs.find())
        assert isinstance(res,
                          (tuple, )), f'Connection to mongoDB failed ({res}).'
    except Exception as err:
        status['errors'].append({"source": "mongo", "message": str(err)})
        status['mongo'] = False

    code = 200

    if len(status['errors']) > 0:
        code = 500

    return jsonify(status), code
