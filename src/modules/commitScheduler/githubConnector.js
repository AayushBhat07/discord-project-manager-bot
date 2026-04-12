const commitEngine = require('./commitEngine');
const path = require('path');
const fs = require('fs');

class GitHubConnector {
  constructor() {
    this.config = {
      repoPath: null,
      remote: null,
      branch: 'main',
      pat: null
    };
    this.initialized = false;
  }

  configure(options) {
    this.config = {
      ...this.config,
      ...options
    };
    return this;
  }

  async initialize() {
    if (!this.config.repoPath) {
      throw new Error('Repository path not configured');
    }

    const resolvedPath = path.resolve(this.config.repoPath);
    
    if (!fs.existsSync(resolvedPath)) {
      try {
        fs.mkdirSync(resolvedPath, { recursive: true });
      } catch (error) {
        throw new Error(`Failed to create repository directory: ${error.message}`);
      }
    }

    const gitDir = path.join(resolvedPath, '.git');
    const isRepo = fs.existsSync(gitDir);

    if (!isRepo) {
      throw new Error(`Directory ${resolvedPath} is not a git repository. Please initialize it with 'git init' first.`);
    }

    commitEngine.initialize(resolvedPath, {
      branch: this.config.branch,
      remote: 'origin'
    });

    this.initialized = true;
    return {
      success: true,
      path: resolvedPath,
      isNewRepo: !isRepo
    };
  }

  async createCommit(message, timestamp, options = {}) {
    if (!this.initialized) {
      await this.initialize();
    }

    const timestampObj = typeof timestamp === 'string' 
      ? timestamp 
      : (timestamp ? timestamp.toISOString() : new Date().toISOString());

    const result = await commitEngine.execute(message, timestampObj, {
      push: options.push !== false,
      files: options.files,
      dryRun: options.dryRun
    });

    return {
      ...result,
      repository: this.config.repoPath,
      branch: this.config.branch
    };
  }

  async createBackdatedCommit(message, dateString, timeString) {
    if (!this.initialized) {
      await this.initialize();
    }

    let timestamp;
    if (dateString && timeString) {
      timestamp = `${dateString} ${timeString}`;
    } else if (dateString) {
      timestamp = dateString;
    } else {
      timestamp = new Date().toISOString();
    }

    return this.createCommit(message, timestamp);
  }

  async createScheduledCommit(message, cronTime) {
    return this.createCommit(message, new Date().toISOString());
  }

  async getStatus() {
    if (!this.initialized) {
      return {
        success: false,
        error: 'Connector not initialized'
      };
    }
    return commitEngine.getStatus();
  }

  async getLastCommit() {
    if (!this.initialized) {
      return {
        success: false,
        error: 'Connector not initialized'
      };
    }
    return commitEngine.getLastCommit();
  }

  validateConfig() {
    const errors = [];

    if (!this.config.repoPath) {
      errors.push('Repository path (TARGET_REPO_PATH) is required');
    }

    if (!this.config.branch) {
      errors.push('Branch name (TARGET_REPO_BRANCH) is required');
    }

    if (errors.length > 0) {
      return {
        valid: false,
        errors: errors
      };
    }

    return { valid: true };
  }
}

module.exports = new GitHubConnector();