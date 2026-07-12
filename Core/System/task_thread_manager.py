# Core/System/task_thread_manager.py
import threading
from django.utils import timezone
from django.core.management import call_command
import importlib

from Core.System.models import TaskScheduler

active_threads = {}  # thread.ident: ManagedThread

class ManagedThread(threading.Thread):
    def __init__(self, task: TaskScheduler, *args, **kwargs):
        thread_name = f"TaskThread-{task.name}"
        super().__init__(name=thread_name, *args, **kwargs)
        self.task = task
        self._stop_event = threading.Event()
        self.start_time = timezone.now()

    def run(self):
        try:
            if self.task.function_path.startswith("command:"):
                # Extract only command name, e.g. "command:sync_masters"
                command_name = self.task.function_path[len("command:"):].strip()
                if not command_name:
                    return
                call_command(command_name)
            else:
                module_path, func_name = self.task.function_path.rsplit('.', 1)
                mod = importlib.import_module(module_path)
                func = getattr(mod, func_name)
                if callable(func):
                    func()
        except Exception as e:
            pass
        finally:
            TaskThreadManager.unregister_thread(self.ident)

    def stop(self):
        self._stop_event.set()
        # No direct way to kill thread, rely on cooperative thread function to check _stop_event

class TaskThreadManager:
    global active_threads

    @classmethod
    def start_task(cls, task: TaskScheduler):
        if not task.allow_parallel:
            for thread in active_threads.values():
                if thread.task.id == task.id and thread.is_alive():
                    return False

        thread = ManagedThread(task=task)
        thread.start()
        active_threads[thread.ident] = thread
        return True

    @classmethod
    def stop_task(cls, thread_ident):
        thread = active_threads.get(thread_ident)
        if thread:
            thread.stop()
            return True
        return False

    @classmethod
    def unregister_thread(cls, thread_ident):
        active_threads.pop(thread_ident, None)

    @classmethod
    def get_status(cls):
        return {
            str(thread_id): {
                "name": thread.task.name,
                "start_time": thread.start_time,
                "duration": str(timezone.now() - thread.start_time),
                "max_execution_time": thread.task.max_execution_time,
                "alive": thread.is_alive(),
            }
            for thread_id, thread in active_threads.items()
        }

    @classmethod
    def kill_expired_threads(cls):
        killed = 0
        for thread_id, thread in list(active_threads.items()):
            elapsed = (timezone.now() - thread.start_time).total_seconds()
            if elapsed > thread.task.max_execution_time:
                thread.stop()
                cls.unregister_thread(thread_id)
                killed += 1
        return killed

    @classmethod
    def get_all_threads(cls):
        return [
            {
                "thread_id": thread_id,
                "task_name": thread.task.name,
                "start_time": thread.start_time.isoformat(),
                "is_alive": thread.is_alive(),
                "duration": str(timezone.now() - thread.start_time),
            }
            for thread_id, thread in active_threads.items()
        ]