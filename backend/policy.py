"""
Policy engine — reads/writes devices from SQLite via database.py.
"""

from database import (
    get_all_devices, get_device, toggle_device_trust,
    enroll_device, remove_device, write_log
)

ALLOWED_USERS = {"admin", "analyst"}


def check_policy(user: str, device: str, ip: str = None) -> dict:
    if user not in ALLOWED_USERS:
        write_log(f"Policy denied — unknown user: {user}", "denied", username=user, ip=ip)
        return {"access": "denied", "reason": f"Unknown user: {user}"}

    dev = get_device(device)
    if dev is None:
        write_log(f"Policy denied — unknown device: {device}", "denied", username=user, ip=ip)
        return {"access": "denied", "reason": f"Unknown device: {device}"}

    if not dev["trusted"]:
        write_log(f"Policy denied — untrusted device: {device}", "denied", username=user, ip=ip)
        return {"access": "denied", "reason": f"Device '{device}' is not trusted", "device": dict(dev)}

    write_log(f"Access granted: {user}@{device}", "success", username=user, ip=ip)
    return {
        "access": "granted",
        "user": user,
        "device": device,
        "device_info": dict(dev),
    }


# Re-export DB helpers so main.py can import from one place
def list_devices():
    return get_all_devices()

def toggle(device_id: str):
    result = toggle_device_trust(device_id)
    if result:
        state = "trusted" if result["trusted"] else "revoked"
        write_log(f"Device {device_id} set to {state}", "info", ip=None)
    return result

def enroll(device_id: str, name: str, os_name: str, security_level: int):
    ok = enroll_device(device_id, name, os_name, security_level)
    if ok:
        write_log(f"Device enrolled: {device_id} ({name})", "info")
    return ok

def remove(device_id: str):
    ok = remove_device(device_id)
    if ok:
        write_log(f"Device removed: {device_id}", "info")
    return ok
