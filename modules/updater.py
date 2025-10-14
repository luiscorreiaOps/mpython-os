from modules import sysctl
import uos

def apply_uploaded():
    try:
        if "/uploaded.bin" in uos.listdir("/"):
            with open("/uploaded.bin", "rb") as fin:
                data = fin.read()
            with open("/app.py", "wb") as fout:
                fout.write(data)
            uos.remove("/uploaded.bin")
            sysctl.log("Updater: applied uploaded.bin -> /app.py")
            return True
    except Exception as e:
        sysctl.log("Updater error:", e)
    return False
