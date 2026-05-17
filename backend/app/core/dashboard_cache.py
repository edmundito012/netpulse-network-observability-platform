from threading import Lock

dashboard_state = {}

dashboard_lock = Lock()


def update_dashboard_state(data: dict):
    global dashboard_state

    with dashboard_lock:
        dashboard_state = data


def get_dashboard_state() -> dict:
    with dashboard_lock:
        return dashboard_state.copy()