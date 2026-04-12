const fs = require('fs');
const path = require('path');
const moment = require('moment');

class UserConfigManager {
  constructor() {
    this.storePath = path.join(__dirname, '..', 'store', 'userConfigs.json');
    this.userConfigs = {};
    this.inactivityDays = 7;
    this.load();
  }

  load() {
    try {
      if (fs.existsSync(this.storePath)) {
        const data = fs.readFileSync(this.storePath, 'utf8');
        this.userConfigs = JSON.parse(data);
      }
    } catch (error) {
      this.userConfigs = {};
    }
  }

  save() {
    try {
      const dir = path.dirname(this.storePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      fs.writeFileSync(this.storePath, JSON.stringify(this.userConfigs, null, 2));
    } catch (error) {
      console.error('Failed to save user configs:', error.message);
    }
  }

  createUserConfig(userId, username) {
    this.userConfigs[userId] = {
      username: username,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      lastActivity: new Date().toISOString(),
      github: {
        pat: null,
        repoPath: null,
        repoUrl: null,
        branch: 'main',
        remote: 'origin'
      },
      discord: {
        dmEnabled: true
      },
      preferences: {
        defaultCommitMessage: '',
        timezone: 'UTC'
      }
    };
    this.save();
    return this.userConfigs[userId];
  }

  getUserConfig(userId) {
    return this.userConfigs[userId] || null;
  }

  updateUserConfig(userId, updates) {
    if (!this.userConfigs[userId]) {
      return null;
    }
    
    this.userConfigs[userId] = {
      ...this.userConfigs[userId],
      ...updates,
      updatedAt: new Date().toISOString()
    };
    this.save();
    return this.userConfigs[userId];
  }

  updateLastActivity(userId) {
    if (this.userConfigs[userId]) {
      this.userConfigs[userId].lastActivity = new Date().toISOString();
      this.save();
    }
  }

  cleanupInactiveUsers(inactivityDays = null) {
    const days = inactivityDays || this.inactivityDays;
    const cutoff = moment().subtract(days, 'days');
    let cleaned = 0;

    for (const [userId, config] of Object.entries(this.userConfigs)) {
      if (config.lastActivity) {
        const lastActive = moment(config.lastActivity);
        if (lastActive.isBefore(cutoff)) {
          delete this.userConfigs[userId];
          cleaned++;
        }
      }
    }

    if (cleaned > 0) {
      this.save();
      console.log(`Cleaned up ${cleaned} inactive users`);
    }

    return cleaned;
  }

  setGitHubPAT(userId, pat) {
    if (!this.userConfigs[userId]) {
      return { success: false, error: 'User config not found' };
    }
    this.userConfigs[userId].github.pat = pat;
    this.userConfigs[userId].updatedAt = new Date().toISOString();
    this.save();
    return { success: true };
  }

  getGitHubPAT(userId) {
    return this.userConfigs[userId]?.github?.pat || null;
  }

  setRepoConfig(userId, repoPath, branch = 'main', remote = 'origin') {
    if (!this.userConfigs[userId]) {
      return { success: false, error: 'User config not found' };
    }
    this.userConfigs[userId].github.repoPath = repoPath;
    this.userConfigs[userId].github.branch = branch;
    this.userConfigs[userId].github.remote = remote;
    this.userConfigs[userId].updatedAt = new Date().toISOString();
    this.save();
    return { success: true };
  }

  getRepoConfig(userId) {
    return this.userConfigs[userId]?.github || null;
  }

  hasGitHubSetup(userId) {
    const config = this.userConfigs[userId]?.github;
    return !!(config?.pat && config?.repoPath);
  }

  deleteUserConfig(userId) {
    if (this.userConfigs[userId]) {
      delete this.userConfigs[userId];
      this.save();
      return true;
    }
    return false;
  }

  listUsers() {
    return Object.keys(this.userConfigs).map(userId => ({
      userId,
      username: this.userConfigs[userId].username,
      hasGitHub: this.hasGitHubSetup(userId),
      updatedAt: this.userConfigs[userId].updatedAt
    }));
  }
}

module.exports = new UserConfigManager();