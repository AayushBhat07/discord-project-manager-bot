const schedulerService = require('../../src/modules/commitScheduler/schedulerService');
const path = require('path');
const fs = require('fs');

describe('SchedulerService', () => {
  const testStorePath = path.join(__dirname, 'fixtures', 'test-jobs.json');
  
  beforeEach(() => {
    schedulerService.jobs.clear();
    schedulerService.jobCallbacks.clear();
    schedulerService.storePath = testStorePath;
    schedulerService.maxJobs = 50;
    schedulerService.maxJobsPerUser = 10;
  });

  afterEach(() => {
    if (fs.existsSync(testStorePath)) {
      fs.unlinkSync(testStorePath);
    }
    schedulerService.stopAll();
  });

  describe('validateCronExpression', () => {
    test('should validate correct cron expressions', () => {
      expect(schedulerService.validateCronExpression('0 9 * * *')).toBe(true);
      expect(schedulerService.validateCronExpression('0 9 * * 1')).toBe(true);
      expect(schedulerService.validateCronExpression('*/15 * * * *')).toBe(true);
    });

    test('should reject invalid cron expressions', () => {
      expect(schedulerService.validateCronExpression('invalid')).toBe(false);
      expect(schedulerService.validateCronExpression('60 * * * *')).toBe(false);
    });
  });

  describe('createJob', () => {
    test('should create a new job', () => {
      const result = schedulerService.createJob('user123', '0 9 * * *', 'Test commit');
      expect(result.success).toBe(true);
      expect(result.job).toHaveProperty('id');
      expect(result.job.cronExpression).toBe('0 9 * * *');
      expect(result.job.message).toBe('Test commit');
      expect(result.job.status).toBe('active');
    });

    test('should reject invalid cron expression', () => {
      const result = schedulerService.createJob('user123', 'invalid', 'Test commit');
      expect(result.success).toBe(false);
      expect(result.error).toContain('Invalid cron');
    });

    test('should enforce max jobs per user', () => {
      schedulerService.maxJobsPerUser = 2;
      schedulerService.createJob('user123', '0 9 * * *', 'Job 1');
      schedulerService.createJob('user123', '0 10 * * *', 'Job 2');
      const result = schedulerService.createJob('user123', '0 11 * * *', 'Job 3');
      expect(result.success).toBe(false);
      expect(result.error).toContain('exceeded');
    });

    test('should enforce max total jobs', () => {
      schedulerService.maxJobs = 2;
      schedulerService.createJob('user1', '0 9 * * *', 'Job 1');
      schedulerService.createJob('user2', '0 10 * * *', 'Job 2');
      const result = schedulerService.createJob('user3', '0 11 * * *', 'Job 3');
      expect(result.success).toBe(false);
    });
  });

  describe('getJob', () => {
    test('should return job by ID', () => {
      const result = schedulerService.createJob('user123', '0 9 * * *', 'Test');
      const retrieved = schedulerService.getJob(result.job.id);
      expect(retrieved).not.toBeNull();
      expect(retrieved.message).toBe('Test');
    });

    test('should return null for non-existent job', () => {
      const retrieved = schedulerService.getJob('non-existent-id');
      expect(retrieved).toBeNull();
    });
  });

  describe('cancelJob', () => {
    test('should cancel an active job', () => {
      const result = schedulerService.createJob('user123', '0 9 * * *', 'Test');
      const cancelResult = schedulerService.cancelJob(result.job.id);
      expect(cancelResult.success).toBe(true);
      expect(cancelResult.job.status).toBe('cancelled');
    });

    test('should fail for non-existent job', () => {
      const result = schedulerService.cancelJob('non-existent');
      expect(result.success).toBe(false);
    });
  });

  describe('pauseJob', () => {
    test('should pause an active job', () => {
      const result = schedulerService.createJob('user123', '0 9 * * *', 'Test');
      const pauseResult = schedulerService.pauseJob(result.job.id);
      expect(pauseResult.success).toBe(true);
      expect(pauseResult.job.status).toBe('paused');
    });
  });

  describe('resumeJob', () => {
    test('should resume a paused job', () => {
      const result = schedulerService.createJob('user123', '0 9 * * *', 'Test');
      schedulerService.pauseJob(result.job.id);
      const resumeResult = schedulerService.resumeJob(result.job.id);
      expect(resumeResult.success).toBe(true);
      expect(resumeResult.job.status).toBe('active');
    });

    test('should fail if job is not paused', () => {
      const result = schedulerService.createJob('user123', '0 9 * * *', 'Test');
      const resumeResult = schedulerService.resumeJob(result.job.id);
      expect(resumeResult.success).toBe(false);
    });
  });

  describe('listJobs', () => {
    test('should list all jobs', () => {
      schedulerService.createJob('user1', '0 9 * * *', 'Job 1');
      schedulerService.createJob('user2', '0 10 * * *', 'Job 2');
      const jobs = schedulerService.listJobs();
      expect(jobs.length).toBe(2);
    });

    test('should filter by ownerId', () => {
      schedulerService.createJob('user1', '0 9 * * *', 'Job 1');
      schedulerService.createJob('user2', '0 10 * * *', 'Job 2');
      const jobs = schedulerService.listJobs({ ownerId: 'user1' });
      expect(jobs.length).toBe(1);
      expect(jobs[0].message).toBe('Job 1');
    });

    test('should filter by status', () => {
      const result = schedulerService.createJob('user1', '0 9 * * *', 'Job 1');
      schedulerService.pauseJob(result.job.id);
      const jobs = schedulerService.listJobs({ status: 'paused' });
      expect(jobs.length).toBe(1);
      expect(jobs[0].status).toBe('paused');
    });
  });

  describe('getUserJobCount', () => {
    test('should return correct count for user', () => {
      schedulerService.createJob('user1', '0 9 * * *', 'Job 1');
      schedulerService.createJob('user1', '0 10 * * *', 'Job 2');
      schedulerService.createJob('user2', '0 11 * * *', 'Job 3');
      expect(schedulerService.getUserJobCount('user1')).toBe(2);
    });
  });

  describe('stopAll', () => {
    test('should stop all cron jobs', () => {
      schedulerService.createJob('user1', '0 9 * * *', 'Job 1');
      schedulerService.createJob('user2', '0 10 * * *', 'Job 2');
      schedulerService.stopAll();
      expect(schedulerService.jobCallbacks.size).toBe(0);
    });
  });
});