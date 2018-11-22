from flask import Blueprint, current_app, jsonify

bp = Blueprint("status", __name__, url_prefix="/status")


@bp.route("/", methods=("GET",))
def healthcheck():
    executor = current_app.load_executor()
    status = {"hosts": [], "containers": {"running": []}}

    containers = executor.get_running_containers()

    for host, port, container_id in containers["running"]:
        status["containers"]["running"].append(
            {"host": host, "port": port, "id": container_id}
        )

    status["hosts"] = containers["available"]

    return jsonify(status), 200
