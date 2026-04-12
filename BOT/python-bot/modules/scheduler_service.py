import os
import json
import uuid
import asyncio
from datetime import datetime, timedelta
from croniter import croniter

class SchedulerService:
    store_path = os.path.join('store', 'jobs.json')
    jobs = {}
    max_jobs = 50
    max_jobs_per_user = 10
    _initialized = False

    @classmethod
    def initialize(cls, store_path=None, config=None):
        if store_path:
            cls.store_path = store_path
        if config:
            cls.max_jobs = config.get('max_jobs', 50)
            cls.max_jobs_per_user = config.get('max_jobs_per_user', 10)
        
        os.makedirs(os.path.dirname(cls.store_path), exist_ok=True)
        cls.load()
        cls._initialized = True
        asyncio.create_task(cls.run_scheduler())

    @classmethod
    def load(cls):
        try:
            if os.path.exists(cls.store_path):
                with open(cls.store_path, 'r') as f:
                    cls.jobs = json.load(f)
        except Exception:
            cls.jobs = {}

    @classmethod
    def save(cls):
        try:
            os.makedirs(os.path.dirname(cls.store_path), exist_ok=True)
            with open(cls.store_path, 'w') as f:
                json.dump(cls.jobs, f, indent=2)
        except Exception as e:
            print(f'Failed to save jobs: {e}')

    @classmethod
    def validate_cron_expression(cls, cron_expr):
        try:
            croniter(cron_expr)
            return True
        except Exception:
            return False

    @classmethod
    def get_next_run(cls, cron_expr):
        try:
            cron = croniter(cron_expr, datetime.now())
            return cron.get_next(datetime).isoformat()
        except Exception:
            return None

    @classmethod
    def create_job(cls, owner_id, cron_expr, message):
        if not cls.validate_cron_expression(cron_expr):
            return {'success': False, 'error': 'Invalid cron expression'}

        user_jobs = [j for j in cls.jobs.values() if j.get('owner_id') == owner_id and j.get('status') == 'active']
        if len(user_jobs) >= cls.max_jobs_per_user:
            return {'success': False, 'error': f'Max {cls.max_jobs_per_user} jobs per user'}

        if len(cls.jobs) >= cls.max_jobs:
            return {'success': False, 'error': f'Max {cls.max_jobs} total jobs'}

        job_id = str(uuid.uuid4())
        now = datetime.now()
        
        cls.jobs[job_id] = {
            'id': job_id,
            'owner_id': owner_id,
            'cron_expression': cron_expr,
            'message': message,
            'status': 'active',
            'created_at': now.isoformat(),
            'next_run': cls.get_next_run(cron_expr),
            'last_run': None,
            'run_count': 0
        }
        
        cls.save()
        return {'success': True, 'job': cls.jobs[job_id]}

    @classmethod
    def get_job(cls, job_id):
        return cls.jobs.get(job_id)

    @classmethod
    def cancel_job(cls, job_id):
        if job_id not in cls.jobs:
            return {'success': False, 'error': 'Job not found'}
        
        cls.jobs[job_id]['status'] = 'cancelled'
        cls.save()
        return {'success': True}

    @classmethod
    def list_jobs(cls, owner_id=None, limit=10):
        jobs = list(cls.jobs.values())
        
        if owner_id:
            jobs = [j for j in jobs if j.get('owner_id') == owner_id]
        
        jobs = [j for j in jobs if j.get('status') == 'active']
        jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jobs[:limit]

    @classmethod
    def list_all_jobs(cls):
        jobs = [j for j in cls.jobs.values() if j.get('status') == 'active']
        jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return jobs

    @classmethod
    async def run_scheduler(cls):
        while True:
            try:
                now = datetime.now()
                for job_id, job in list(cls.jobs.items()):
                    if job.get('status') != 'active':
                        continue
                    
                    cron_expr = job.get('cron_expression')
                    if not cron_expr:
                        continue
                    
                    try:
                        cron = croniter(cron_expr, now)
                        next_run = cron.get_next(datetime)
                        
                        if abs((next_run - now).total_seconds()) < 60:
                            print(f'Executing scheduled job: {job_id}')
                            await cls.execute_job(job_id)
                            job['last_run'] = now.isoformat()
                            job['run_count'] = job.get('run_count', 0) + 1
                            job['next_run'] = cls.get_next_run(cron_expr)
                    except Exception as e:
                        print(f'Error in job {job_id}: {e}')
                
                cls.save()
            except Exception as e:
                print(f'Scheduler error: {e}')
            
            await asyncio.sleep(30)

    @classmethod
    async def execute_job(cls, job_id):
        job = cls.jobs.get(job_id)
        if not job:
            return
        
        print(f'Would execute commit: {job.get("message")}')
        return True
