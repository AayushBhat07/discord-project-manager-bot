const fs = require('fs');
const path = require('path');
const simpleGit = require('simple-git');
const { v4: uuidv4 } = require('uuid');

class TempRepoManager {
  constructor() {
    this.tempRepoPath = null;
    this.userRepos = new Map();
  }

  initialize(options = {}) {
    this.tempRepoPath = options.tempRepoPath || path.join(process.cwd(), 'TEMP_REPO');
    return this;
  }

  async createTempRepo(userId, options = {}) {
    const repoDir = this.getUserRepoPath(userId);
    
    if (fs.existsSync(path.join(repoDir, '.git'))) {
      return {
        success: true,
        message: 'TEMP repository already exists',
        path: repoDir,
        isNew: false
      };
    }

    try {
      if (!fs.existsSync(repoDir)) {
        fs.mkdirSync(repoDir, { recursive: true });
      }

      const git = simpleGit(repoDir);
      await git.init();

      if (options.remoteUrl) {
        await git.addRemote('origin', options.remoteUrl);
      }

      const readmePath = path.join(repoDir, 'README.md');
      fs.writeFileSync(readmePath, `# TEMP Repository\n\nThis is a temporary commit storage for user ${userId}\n`);

      await git.add('.');
      await git.commit('Initial commit');

      if (options.remoteUrl) {
        await git.push('origin', options.branch || 'main', { '--set-upstream': null });
      }

      return {
        success: true,
        message: 'TEMP repository created successfully',
        path: repoDir,
        isNew: true
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        path: repoDir
      };
    }
  }

  async createPrivateGitHubRepo(userId, token, repoName = 'TEMP') {
    const fetch = require('node-fetch');
    
    try {
      const response = await fetch('https://api.github.com/user/repos', {
        method: 'POST',
        headers: {
          'Authorization': `token ${token}`,
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: `${repoName}_${userId.substring(0, 8)}`,
          private: true,
          auto_init: true,
          description: 'Temporary commit storage for Discord bot'
        })
      });

      if (!response.ok) {
        const error = await response.json();
        return {
          success: false,
          error: error.message || 'Failed to create GitHub repo'
        };
      }

      const repoData = await response.json();
      
      return {
        success: true,
        repo: {
          name: repoData.name,
          fullName: repoData.full_name,
          url: repoData.html_url,
          cloneUrl: repoData.clone_url
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  getUserRepoPath(userId) {
    return path.join(this.tempRepoPath, `user_${userId}`);
  }

  async commitToTempRepo(userId, message, timestamp, options = {}) {
    const repoDir = this.getUserRepoPath(userId);
    
    if (!fs.existsSync(repoDir)) {
      const createResult = await this.createTempRepo(userId);
      if (!createResult.success) {
        return createResult;
      }
    }

    try {
      const git = simpleGit(repoDir);
      
      const env = {};
      if (timestamp) {
        env.GIT_AUTHOR_DATE = timestamp;
        env.GIT_COMMITTER_DATE = timestamp;
      }

      const testFile = path.join(repoDir, `commit_${Date.now()}.txt`);
      fs.writeFileSync(testFile, `Commit: ${message}\nTime: ${timestamp || new Date().toISOString()}\n`);

      await git.add('.');
      await git.commit(message, { '--date': timestamp });

      if (options.push && options.remoteUrl) {
        await git.addRemote('origin', options.remoteUrl);
        await git.push('origin', options.branch || 'main');
      }

      return {
        success: true,
        message: 'Commit created in TEMP repository',
        path: repoDir,
        timestamp: timestamp || new Date().toISOString()
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async setupUserRepo(userId, options = {}) {
    const { repoType = 'temp', customPath, githubRepo, token, branch = 'main' } = options;

    let repoConfig;

    switch (repoType) {
      case 'temp':
        const tempResult = await this.createTempRepo(userId);
        repoConfig = {
          type: 'temp',
          path: tempResult.path,
          isNew: tempResult.isNew
        };
        break;

      case 'github':
        if (githubRepo) {
          repoConfig = {
            type: 'github',
            path: `./${githubRepo.replace('/', '-')}`,
            remote: `https://${token}@github.com/${githubRepo}.git`,
            branch: branch
          };
        } else {
          const ghResult = await this.createPrivateGitHubRepo(userId, token);
          if (!ghResult.success) {
            return ghResult;
          }
          repoConfig = {
            type: 'github',
            path: `./${ghResult.repo.name}`,
            remote: ghResult.repo.cloneUrl,
            branch: branch,
            repoInfo: ghResult.repo
          };
        }
        break;

      case 'local':
        if (!customPath) {
          return { success: false, error: 'Custom path required for local repo type' };
        }
        repoConfig = {
          type: 'local',
          path: customPath,
          branch: branch
        };
        break;

      default:
        return { success: false, error: 'Invalid repo type. Use: temp, github, or local' };
    }

    this.userRepos.set(userId, repoConfig);
    return { success: true, config: repoConfig };
  }

  getUserRepo(userId) {
    return this.userRepos.get(userId) || null;
  }

  async deleteUserRepo(userId, options = {}) {
    const repoConfig = this.userRepos.get(userId);
    if (!repoConfig) return { success: false, error: 'No repository configured' };

    if (repoConfig.type === 'temp' && options.deleteFiles) {
      const repoDir = this.getUserRepoPath(userId);
      if (fs.existsSync(repoDir)) {
        fs.rmSync(repoDir, { recursive: true, force: true });
      }
    }

    this.userRepos.delete(userId);
    return { success: true, message: 'User repository removed' };
  }

  listUserRepos() {
    const repos = [];
    for (const [userId, config] of this.userRepos) {
      repos.push({ userId, ...config });
    }
    return repos;
  }
}

module.exports = new TempRepoManager();