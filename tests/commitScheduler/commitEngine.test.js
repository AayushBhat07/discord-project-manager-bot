const commitEngine = require('../../src/modules/commitScheduler/commitEngine');
const path = require('path');

describe('CommitEngine', () => {
  const testRepoPath = path.join(__dirname, 'fixtures', 'test-repo');

  beforeAll(() => {
    const fs = require('fs');
    if (!fs.existsSync(testRepoPath)) {
      fs.mkdirSync(testRepoPath, { recursive: true });
    }
  });

  describe('initialize', () => {
    test('should initialize with repo path', () => {
      const result = commitEngine.initialize(testRepoPath);
      expect(result).toBe(commitEngine);
      expect(commitEngine.repoPath).toBe(testRepoPath);
    });

    test.skip('should throw if initialized without path', () => {
      const freshEngine = require('../../src/modules/commitScheduler/commitEngine');
      expect(() => freshEngine.stage()).toThrow();
    });
  });

  describe('stage', () => {
    test('should stage files', async () => {
      commitEngine.initialize(testRepoPath);
      const result = await commitEngine.stage(['.']);
      expect(result).toHaveProperty('success');
    });
  });

  describe('execute', () => {
    test('should return dry run result without actual commit', async () => {
      commitEngine.initialize(testRepoPath);
      const result = await commitEngine.execute('test commit', new Date().toISOString(), {
        dryRun: true
      });
      expect(result.success).toBe(true);
      expect(result.dryRun).toBe(true);
    });

    test('should fail with empty message', async () => {
      commitEngine.initialize(testRepoPath);
      const result = await commitEngine.execute('', new Date().toISOString());
      expect(result.success).toBe(false);
      expect(result.error).toContain('required');
    });
  });

  describe('getStatus', () => {
    test('should return repository status', async () => {
      commitEngine.initialize(testRepoPath);
      const result = await commitEngine.getStatus();
      expect(result).toHaveProperty('success');
    });
  });

  describe('addAndCommit', () => {
    test('should combine add, commit and optional push', async () => {
      commitEngine.initialize(testRepoPath);
      const result = await commitEngine.addAndCommit('test message', new Date().toISOString(), {
        push: false
      });
      expect(result).toHaveProperty('success');
    });
  });
});