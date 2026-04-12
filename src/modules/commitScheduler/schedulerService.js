const cron = require('node-cron');
const jsonfile = require('jsonfile');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const commitEngine = require('./commitEngine');

class SchedulerService {
  constructor() {
    this.jobs = new Map();
    this.storePath = null;
    this.maxJobs = 50;
    this.maxJobsPerUser = 10;
    this.jobCallbacks = new Map();
  }

  initialize(storePath, options = {}) {
    this.storePath = storePath;
    this.maxJobs = options.maxJobs || 50;
    this.maxJobsPerUser = options.maxJobsPerUser || 10;
    return this.loadJobs();
  }

  async loadJobs() {
    try {
      if (this.storePath && require('fs').existsSync(this.storePath)) {
        const data = await jsonfile.readFile(this.storePath);
        if (data && data.jobs) {
          for (const [id, job] of Object.entries(data.jobs)) {
            this.jobs.set(id, job);
            if (job.status === 'active' && job.cronExpression) {
              this.scheduleJob(id, job);
            }
          }
        }
        return { success: true, loaded: this.jobs.size };
      }
    } catch (error) {
      console.error('Failed to load jobs:', error.message);
    }
    return { success: true, loaded: 0 };
  }

  async saveJobs() {
    if (!this.storePath) return;
    
    const jobsObj = {};
    for (const [id, job] of this.jobs) {
      jobsObj[id] = job;
    }

    try {
      const dir = path.dirname(this.storePath);
      if (!require('fs').existsSync(dir)) {
        require('fs').mkdirSync(dir, { recursive: true });
      }
      await jsonfile.writeFile(this.storePath, { jobs: jobsObj, updatedAt: new Date().toISOString() });
    } catch (error) {
      console.error('Failed to save jobs:', error.message);
    }
  }

  validateCronExpression(expression) {
    return cron.validate(expression);
  }

  createJob(ownerId, cronExpression, message, options = {}) {
    if (!this.validateCronExpression(cronExpression)) {
      return {
        success: false,
        error: 'Invalid cron expression'
      };
    }

    const userJobCount = this.getUserJobCount(ownerId);
    if (userJobCount >= this.maxJobsPerUser) {
      return {
        success: false,
        error: `Maximum ${this.maxJobsPerUser} jobs per user exceeded`
      };
    }

    if (this.jobs.size >= this.maxJobs) {
      return {
        success: false,
        error: `Maximum ${this.maxJobs} total jobs exceeded`
      };
    }

    const id = uuidv4();
    const now = new Date();
    
    const job = {
      id,
      ownerId,
      cronExpression,
      message: message || 'Scheduled commit',
      status: 'active',
      createdAt: now.toISOString(),
      lastRun: null,
      nextRun: this.getNextRunTime(cronExpression),
      options: {
        branch: options.branch || 'main',
        remote: options.remote || 'origin',
        files: options.files || ['.'],
        push: options.push !== false
      }
    };

    this.jobs.set(id, job);
    this.scheduleJob(id, job);
    this.saveJobs();

    return {
      success: true,
      job: job
    };
  }

  scheduleJob(id, job) {
    if (!job.cronExpression || job.status !== 'active') return;

    const task = cron.schedule(job.cronExpression, async () => {
      await this.executeJob(id);
    });

    this.jobCallbacks.set(id, task);
  }

  async executeJob(id) {
    const job = this.jobs.get(id);
    if (!job || job.status !== 'active') return;

    try {
      const timestamp = new Date().toISOString();
      const result = await commitEngine.execute(job.message, timestamp, job.options);

      job.lastRun = new Date().toISOString();
      job.nextRun = this.getNextRunTime(job.cronExpression);
      job.lastResult = {
        success: result.success,
        error: result.error || null
      };

      this.saveJobs();

      return {
        success: result.success,
        jobId: id,
        result: result
      };
    } catch (error) {
      job.lastRun = new Date().toISOString();
      job.lastResult = {
        success: false,
        error: error.message
      };
      this.saveJobs();

      return {
        success: false,
        jobId: id,
        error: error.message
      };
    }
  }

  getNextRunTime(cronExpression) {
    const interval = this.estimateNextRun(cronExpression);
    if (interval) {
      return new Date(Date.now() + interval).toISOString();
    }
    return null;
  }

  estimateNextRun(cronExpression) {
    const parts = cronExpression.split(' ');
    if (parts.length !== 5) return null;

    const [min, hour, dayMonth, month, dayWeek] = parts;
    
    const now = new Date();
    const next = new Date(now);
    
    if (dayWeek !== '*') {
      const targetDay = parseInt(dayWeek);
      const currentDay = next.getDay();
      let diff = targetDay - currentDay;
      if (diff <= 0) diff += 7;
      next.setDate(next.getDate() + diff);
    }

    if (hour !== '*') next.setHours(parseInt(hour), 0, 0, 0);
    if (min !== '*') next.setMinutes(parseInt(min), 0, 0);

    if (next <= now) {
      next.setDate(next.getDate() + 7);
    }

    return next.getTime() - now.getTime();
  }

  cancelJob(id) {
    const job = this.jobs.get(id);
    if (!job) {
      return { success: false, error: 'Job not found' };
    }

    job.status = 'cancelled';
    
    const task = this.jobCallbacks.get(id);
    if (task) {
      task.stop();
      this.jobCallbacks.delete(id);
    }

    this.saveJobs();

    return { success: true, job: job };
  }

  pauseJob(id) {
    const job = this.jobs.get(id);
    if (!job) {
      return { success: false, error: 'Job not found' };
    }

    job.status = 'paused';
    
    const task = this.jobCallbacks.get(id);
    if (task) {
      task.stop();
    }

    this.saveJobs();

    return { success: true, job: job };
  }

  resumeJob(id) {
    const job = this.jobs.get(id);
    if (!job) {
      return { success: false, error: 'Job not found' };
    }

    if (job.status !== 'paused') {
      return { success: false, error: 'Job is not paused' };
    }

    job.status = 'active';
    this.scheduleJob(id, job);
    this.saveJobs();

    return { success: true, job: job };
  }

  getJob(id) {
    return this.jobs.get(id) || null;
  }

  listJobs(options = {}) {
    const jobs = Array.from(this.jobs.values());
    
    let filtered = jobs;
    
    if (options.ownerId) {
      filtered = filtered.filter(j => j.ownerId === options.ownerId);
    }
    
    if (options.status) {
      filtered = filtered.filter(j => j.status === options.status);
    }

    if (options.limit) {
      filtered = filtered.slice(0, options.limit);
    }

    return filtered;
  }

  getUserJobCount(ownerId) {
    return Array.from(this.jobs.values()).filter(j => j.ownerId === ownerId).length;
  }

  stopAll() {
    for (const [id, task] of this.jobCallbacks) {
      task.stop();
    }
    this.jobCallbacks.clear();
  }
}

module.exports = new SchedulerService();