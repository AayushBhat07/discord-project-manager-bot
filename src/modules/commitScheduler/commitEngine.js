const simpleGit = require('simple-git');
const path = require('path');

class CommitEngine {
  constructor() {
    this.git = null;
    this.repoPath = null;
    this.config = {
      branch: 'main',
      remote: 'origin'
    };
  }

  initialize(repoPath, options = {}) {
    this.repoPath = repoPath;
    this.config = { ...this.config, ...options };
    this.git = simpleGit(repoPath);
    return this;
  }

  async stage(files = ['.']) {
    if (!this.git) {
      throw new Error('CommitEngine not initialized. Call initialize() first.');
    }

    try {
      const result = await this.git.add(files);
      return {
        success: true,
        files: files,
        output: result
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        stage: 'add'
      };
    }
  }

  async commit(message, timestamp, options = {}) {
    if (!this.git) {
      throw new Error('CommitEngine not initialized. Call initialize() first.');
    }

    if (!message || typeof message !== 'string') {
      return {
        success: false,
        error: 'Commit message is required',
        stage: 'validation'
      };
    }

    const authorDate = timestamp || new Date();
    const dateString = typeof authorDate === 'string' ? authorDate : authorDate.toISOString();

    try {
      const env = {
        GIT_AUTHOR_DATE: dateString,
        GIT_COMMITTER_DATE: dateString
      };

      const result = await this.git.raw(['commit', '-m', message, '--date', dateString]);
      
      return {
        success: true,
        message: message,
        timestamp: dateString,
        output: result
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        stage: 'commit'
      };
    }
  }

  async push(remote = null, branch = null) {
    if (!this.git) {
      throw new Error('CommitEngine not initialized. Call initialize() first.');
    }

    try {
      const remoteName = remote || this.config.remote;
      const branchName = branch || this.config.branch;
      
      const result = await this.git.push(remoteName, branchName);
      
      return {
        success: true,
        remote: remoteName,
        branch: branchName,
        output: result
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        stage: 'push'
      };
    }
  }

  async execute(message, timestamp, options = {}) {
    const dryRun = options.dryRun || false;
    const files = options.files || ['.'];
    const push = options.push !== false;

    if (dryRun) {
      return {
        success: true,
        dryRun: true,
        message: message,
        timestamp: timestamp,
        actions: ['stage', 'commit', push ? 'push' : 'skip']
      };
    }

    const stageResult = await this.stage(files);
    if (!stageResult.success) {
      return stageResult;
    }

    const commitResult = await this.commit(message, timestamp);
    if (!commitResult.success) {
      return commitResult;
    }

    if (!push) {
      return {
        ...commitResult,
        pushed: false,
        message: 'Commit created but not pushed (push disabled)'
      };
    }

    const pushResult = await this.push();
    return {
      ...commitResult,
      pushed: pushResult.success,
      pushError: pushResult.success ? null : pushResult.error
    };
  }

  async getStatus() {
    if (!this.git) {
      throw new Error('CommitEngine not initialized. Call initialize() first.');
    }

    try {
      const status = await this.git.status();
      return {
        success: true,
        status: status
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async getLastCommit() {
    if (!this.git) {
      throw new Error('CommitEngine not initialized. Call initialize() first.');
    }

    try {
      const log = await this.git.log({ maxCount: 1 });
      return {
        success: true,
        commit: log.latest
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async addAndCommit(message, timestamp, options = {}) {
    const result = await this.execute(message, timestamp, {
      ...options,
      push: options.push !== undefined ? options.push : true
    });
    return result;
  }
}

module.exports = new CommitEngine();