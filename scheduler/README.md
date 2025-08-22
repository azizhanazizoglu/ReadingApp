# scheduler/job_scheduler.py

Basit bir job scheduler ve state flow yöneticisi.

- Her adım (webbot, memory, llm, rapor) birer job olarak tanımlanır.
- Scheduler, adımları sıralı ve kontrollü şekilde çalıştırır.
- Her adımın durumu (waiting, running, done, error) izlenebilir.
- Hata olursa otomasyon durur ve kullanıcıya bildirilir.

## Kullanım
```python
from scheduler.job_scheduler import Job, JobScheduler

def my_job():
    # ...
    return "done"

scheduler = JobScheduler()
scheduler.add_job(Job("step1", my_job))
scheduler.run_all()
```

## User Story
- Kullanıcı Qt arayüzünden otomasyonu başlatır.
- Scheduler, webbot → memory → llm → rapor adımlarını sırasıyla tetikler.
- Her adımın sonucu ve durumu memory/state'e kaydedilir, GUI'ye yansıtılır.
