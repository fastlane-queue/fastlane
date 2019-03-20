

from flask import Blueprint, jsonify, current_app, abort

bp = Blueprint('routes', __name__, url_prefix="/routes") # pylint: disable=invalid-name


@bp.route('/', methods=['GET'])
def routes():  # pragma: no cover
    """Print available functions."""
    if not current_app.debug:
        abort(404)

    func_list = []
    for rule in current_app.url_map.iter_rules():
        endpoint = rule.rule
        methods = ", ".join(list(rule.methods))
        doc = current_app.view_functions[rule.endpoint].__doc__

        route = {
            "endpoint": endpoint,
            "methods": methods
        }
        if doc:
            route["doc"] = doc
        func_list.append(route)

    func_list = sorted(func_list, key=lambda k: k['endpoint'])
    return jsonify(func_list)
