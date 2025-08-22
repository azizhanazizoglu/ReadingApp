import threading
import time

class JobState:
    WAITING = "waiting"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"

class Job:
    def __init__(self, name, func):
        self.name = name
        self.func = func
        self.state = JobState.WAITING
        self.result = None
        self.error = None
    def run(self, *args, **kwargs):
        self.state = JobState.RUNNING
        try:
            self.result = self.func(*args, **kwargs)
            self.state = JobState.DONE
        except Exception as e:
            self.error = str(e)
            self.state = JobState.ERROR

class JobScheduler:
    def __init__(self):
        self.jobs = []
        self.state_log = []
    def add_job(self, job):
        self.jobs.append(job)
    def run_all(self):
        for job in self.jobs:
            self.state_log.append((job.name, JobState.WAITING))
            job.run()
            self.state_log.append((job.name, job.state))
            if job.state == JobState.ERROR:
                print(f"[Scheduler] {job.name} failed: {job.error}")
                break
            else:
                print(f"[Scheduler] {job.name} finished.")
    def get_states(self):
        return [(job.name, job.state) for job in self.jobs]

# Örnek kullanım (test amaçlı):
if __name__ == "__main__":
    def webbot_job():
        print("Webbot çalışıyor...")
        time.sleep(1)
        return "webbot done"
    def memory_job():
        print("Memory kaydediliyor...")
        time.sleep(1)
        return "memory done"
    def llm_job():
        print("LLM mapping yapılıyor...")
        time.sleep(1)
        return "llm done"
    scheduler = JobScheduler()
    scheduler.add_job(Job("webbot", webbot_job))
    scheduler.add_job(Job("memory", memory_job))
    scheduler.add_job(Job("llm", llm_job))
    scheduler.run_all()
    print("Job states:", scheduler.get_states())
