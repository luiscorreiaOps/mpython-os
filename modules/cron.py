import uasyncio as asyncio
import ujson
import time
from modules import sysctl, cmd_handler

CRON_FILE = "/cron.json"

class CronScheduler:
    def __init__(self):
        self.tasks = []
        self.load_tasks()
        self.running = False

    def load_tasks(self):
        try:
            with open(CRON_FILE, "r") as f:
                self.tasks = ujson.load(f)
            sysctl.log("Cron: Tarefas carregadas.")
        except:
            self.tasks = []
            sysctl.log("Cron: Nenhuma tarefa slva.")

    def save_tasks(self):
        try:
            with open(CRON_FILE, "w") as f:
                ujson.dump(self.tasks, f)
        except Exception as e:
            sysctl.log("Cron: Erro ao salvar tarefas", e)

    def add_task(self, interval, command):
        import ubinascii, machine
        task_id = ubinascii.hexlify(machine.unique_id()).decode()[-4:] + str(int(time.time()))[-4:]

        task = {
            "id": task_id,
            "interval": int(interval),
            "command": command,
            "active": True,
            "last_run": 0
        }
        self.tasks.append(task)
        self.save_tasks()
        sysctl.log(f"Cron: Tarefa {task_id} adicionada.")
        return task_id

    def remove_task(self, task_id):
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        self.save_tasks()
        sysctl.log(f"Cron: Tarefa {task_id} removida.")

    async def execute_task(self, task):
        sysctl.log(f"Cron: Executando '{task['command']}'")
        try:
            output, _ = cmd_handler.process_command(task['command'])
            sysctl.log(f"Cron Output ({task['id']}): {output}")
        except Exception as e:
            sysctl.log(f"Cron Error ({task['id']}): {e}")

    async def run(self):
        sysctl.log("Cron: Scheduler iniciado.")
        self.running = True
        while self.running:
            now = time.time()
            for task in self.tasks:
                if not task["active"]:
                    continue

                if task.get("last_run", 0) == 0:
                     task["last_run"] = now

                if now - task["last_run"] >= task["interval"]:
                    asyncio.create_task(self.execute_task(task))
                    task["last_run"] = now

            await asyncio.sleep(1)

# global
scheduler = CronScheduler()

async def start():
    await scheduler.run()
