"""Tiny client for the Fusion360MCP add-in (127.0.0.1:9876).

Usage:
  python fx.py ping
  python fx.py code "print(design.parentDocument.name)"
  python fx.py file path/to/script.py [KEY=VALUE ...]   (exec a script file inside Fusion; KEY=VALUE become globals)
  python fx.py render view out.png [w h]
"""
import base64
import json
import socket
import sys


def call(cmd, params=None, timeout=240.0):
    payload = json.dumps({"type": cmd, "params": params or {}}) + "\n"
    with socket.create_connection(("127.0.0.1", 9876), timeout=5.0) as c:
        c.settimeout(timeout)
        c.sendall(payload.encode("utf-8"))
        data = b""
        while b"\n" not in data:
            block = c.recv(1 << 20)
            if not block:
                break
            data += block
    return json.loads(data.decode("utf-8"))


def run_code(code, timeout=240.0):
    r = call("execute_code", {"code": code}, timeout)
    res = r.get("result", r)
    if isinstance(res, dict) and res.get("ok") is False:
        print("ERROR:", res.get("error_message"))
        print(res.get("traceback", ""))
        sys.exit(1)
    if r.get("status") != "success":
        print("BRIDGE:", r)
        sys.exit(2)
    out = res.get("result", res) if isinstance(res, dict) else res
    if isinstance(out, dict) and "output" in out:
        out = out["output"]
    print(out if isinstance(out, str) else json.dumps(out, indent=1))


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "ping":
        print(call("ping"))
    elif mode == "code":
        run_code(sys.argv[2])
    elif mode == "file":
        import os
        path = os.path.abspath(sys.argv[2]).replace("\\", "/")
        pre = f"HM_SCRIPTS = r'{os.path.dirname(path)}'\n"
        for kv in sys.argv[3:]:
            k, v = kv.split("=", 1)
            pre += f"{k}={v}\n"
        run_code(pre + f"exec(compile(open(r'{path}',encoding='utf-8').read(), r'{path}', 'exec'))")
    elif mode == "render":
        w = int(sys.argv[4]) if len(sys.argv) > 4 else 1200
        h = int(sys.argv[5]) if len(sys.argv) > 5 else 900
        r = call("render_view", {"view": sys.argv[2], "width": w, "height": h, "fit": True})
        res = r["result"]
        if res.get("ok") is False:
            print(res); sys.exit(1)
        open(sys.argv[3], "wb").write(base64.b64decode(res["image_base64"]))
        print("saved", sys.argv[3])
    else:
        print(json.dumps(call(mode, json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}), indent=1)[:20000])
