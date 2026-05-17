from threading import Lock

device_state_cache = {}

device_state_lock = Lock()


def update_device_state(
    device_id: int,
    state: dict,
):
    with device_state_lock:
        device_state_cache[device_id] = state


def get_device_state(device_id: int):
    with device_state_lock:
        return device_state_cache.get(device_id)


def get_all_device_states():
    with device_state_lock:
        return device_state_cache.copy()